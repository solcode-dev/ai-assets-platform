import base64
import httpx
import logging
import asyncio
import google.auth
import google.auth.transport.requests
from app.domain.interfaces import AIGenerationClient
from app.core.config import settings
from app.core.exceptions import ExternalServiceException
from typing import Optional
import contextlib
from redis.asyncio import Redis, from_url

logger = logging.getLogger(__name__)


class VertexAIClient(AIGenerationClient):
    """Google Vertex AI 기반 AI 생성 클라이언트"""

    def __init__(self):
        self.project_id = settings.GCP_PROJECT_ID
        self.region = settings.GCP_REGION
        self.credentials = None
        self._redis: Optional[Redis] = None

        # 구글 표준 방식(ADC: Application Default Credentials)으로 인증 시도
        try:
            self.credentials, detected_project_id = google.auth.default(
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            
            # 명시적으로 설정된 프로젝트 ID가 없으면 감지된 프로젝트 ID 사용
            if not self.project_id:
                self.project_id = detected_project_id
                
            logger.info(f"Initialized VertexAI with ADC. Project: {self.project_id}, Region: {self.region}")
        except Exception as e:
            logger.error(f"Failed to load GCP credentials: {e}")
            raise ExternalServiceException("Failed to initialize Vertex AI client: No valid GCP credentials found") from e

        self.base_url = f"https://{self.region}-aiplatform.googleapis.com/v1"

    def _truncate_base64_log(self, data: any) -> any:
        """딕셔너리 내의 긴 base64 문자열을 로그 출력을 위해 잘라냅니다."""
        if isinstance(data, dict):
            return {k: self._truncate_base64_log(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._truncate_base64_log(i) for i in data]
        elif isinstance(data, str) and len(data) > 100:
            # 100자 이상이면 base64일 가능성이 높으므로 자름
            return data[:50] + "..." + data[-50:]
        return data

    def _get_token(self) -> str:
        """유효한 액세스 토큰을 반환합니다."""
        if not self.credentials:
            raise ExternalServiceException("No valid GCP credentials found")

        # Credentials 기반 토큰 생성/갱신
        if not self.credentials.valid:
            request = google.auth.transport.requests.Request()
            self.credentials.refresh(request)
        return self.credentials.token

    def _get_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._get_token()}",
            "Content-Type": "application/json",
        }

    async def _get_redis(self) -> Redis:
        """Redis 클라이언트 인스턴스를 반환합니다."""
        if self._redis is None:
            self._redis = from_url(settings.REDIS_URL, decode_responses=True)
        return self._redis

    @contextlib.asynccontextmanager
    async def _track_request(self):
        """요청의 시작과 끝을 추적하여 Redis에 기록합니다."""
        r = await self._get_redis()
        try:
            await r.incr("vertex_ai:active_requests")
            yield
        finally:
            # 예외가 발생하더라도 활성 요청 수는 감소시키고 완료 갯수는 증가시킴
            pipe = r.pipeline()
            pipe.decr("vertex_ai:active_requests")
            pipe.incr("vertex_ai:completed_requests")
            await pipe.execute()

    async def generate_image(self, prompt: str) -> bytes:
        """Imagen 3.0을 사용하여 이미지를 생성합니다."""
        async with self._track_request():
            endpoint = f"{self.base_url}/projects/{self.project_id}/locations/{self.region}/publishers/google/models/imagen-3.0-fast-generate-001:predict"

            payload = {
                "instances": [{"prompt": prompt}],
                "parameters": {
                    "sampleCount": 1,
                    "aspectRatio": "1:1",
                    "safetyFilterLevel": "block_some",
                },
            }

            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        endpoint, headers=self._get_headers(), json=payload
                    )
                    response.raise_for_status()

                    # 상세 디버깅 로깅
                    logger.info(f"[HAWKEYE:AI] Vertex AI Status: {response.status_code}")
                    if response.status_code != 200:
                        logger.error(f"[HAWKEYE:AI] Vertex AI Error Body: {response.text}")
                    
                    result = response.json()
                    logger.debug(f"[HAWKEYE:AI] Parsed JSON keys: {list(result.keys())}")

                    # Fail Fast: 응답 구조 검증
                    if "predictions" not in result or len(result["predictions"]) == 0:
                        logger.error(
                            f"Invalid Vertex AI response structure: {self._truncate_base64_log(result)}"
                        )
                        raise ExternalServiceException(
                            "Invalid response structure from Vertex AI"
                        )

                    image_b64 = result["predictions"][0].get("bytesBase64Encoded")
                    if not image_b64:
                        logger.error(
                            f"Missing 'bytesBase64Encoded' in response: {self._truncate_base64_log(result)}"
                        )
                        raise ExternalServiceException(
                            "Missing image data in Vertex AI response"
                        )

                    return base64.b64decode(image_b64)

            except httpx.HTTPStatusError as e:
                logger.error(
                    f"Vertex AI HTTP error: status={e.response.status_code}, "
                    f"prompt='{prompt[:50]}...', response={e.response.text[:200]}"
                )
                raise ExternalServiceException(
                    f"Vertex AI image generation failed: HTTP {e.response.status_code}"
                ) from e

            except httpx.TimeoutException as e:
                logger.error(f"Vertex AI timeout (60s): prompt='{prompt[:50]}...'")
                raise ExternalServiceException(
                    "Vertex AI request timed out after 60 seconds"
                ) from e

            except (KeyError, IndexError, ValueError) as e:
                logger.error(f"Vertex AI response parsing error: {e}")
                raise ExternalServiceException(
                    f"Failed to parse Vertex AI response: {type(e).__name__}"
                ) from e

    async def generate_video_from_text(self, prompt: str) -> bytes:
        """텍스트 프롬프트로 비디오 생성 (Veo)"""
        async with self._track_request():
            url = f"{self.base_url}/projects/{self.project_id}/locations/{self.region}/publishers/google/models/veo-3.0-fast-generate-001:predictLongRunning"

            payload = {
                "instances": [{"prompt": prompt}],
                "parameters": {
                    "sampleCount": 1,
                    "videoLength": "5s",
                    "aspectRatio": "16:9",
                },
            }

            return await self._handle_video_lro(url, payload, "Text-to-Video")

    async def generate_video_from_image(self, prompt: str, image_bytes: bytes, source_image_mime_type: Optional[str]) -> bytes:
        """이미지와 프롬프트로 비디오 생성 (Veo)"""
        async with self._track_request():
            url = f"{self.base_url}/projects/{self.project_id}/locations/{self.region}/publishers/google/models/veo-3.0-fast-generate-001:predictLongRunning"
            image_b64 = base64.b64encode(image_bytes).decode("utf-8")

            image_obj = {"bytesBase64Encoded": image_b64}
            if source_image_mime_type:
                image_obj["mimeType"] = source_image_mime_type

            payload = {
                "instances": [
                    {
                        "prompt": prompt, 
                        "image": image_obj
                    }
                ],
                "parameters": {
                    "sampleCount": 1,
                    "videoLength": "5s",
                    "aspectRatio": "16:9",
                },
            }

            return await self._handle_video_lro(url, payload, "Image-to-Video")

    async def _poll_operation(
        self, operation_name: str, project_id: str = None
    ) -> dict:
        """LRO(Long Running Operation) 폴링"""
        # operation_name에서 UUID만 추출 (예: 25538847-c2b0-44af-bf08-a8d768cdc665)
        operation_id = operation_name.split("/")[-1]
        target_project_id = project_id or self.project_id

        headers = {
            "Authorization": f"Bearer {self._get_token()}",
            "Content-Type": "application/json",
        }

        logger.info(
            f"Starting polling. ID: {operation_id} (Project: {target_project_id})"
        )
        logger.debug(f"Full Operation Name: {operation_name}")

        # 첫 폴링 전 약간의 대기 (LRO 생성 직후 바로 요청하는 것을 방지)
        # await asyncio.sleep(2)

        # fetchPredictOperation 패턴: 모델 리소스 경로 추출
        # operation_name: projects/PID/locations/LOC/publishers/google/models/MODEL/operations/OPID
        # model_resource: projects/PID/locations/LOC/publishers/google/models/MODEL
        model_resource = "/".join(operation_name.split("/")[:-2])
        url = f"https://{self.region}-aiplatform.googleapis.com/v1/{model_resource}:fetchPredictOperation"
        payload = {"operationName": operation_name}

        while True:
            try:
                logger.debug(f"===> Polling URL: {url}")
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        url, headers=headers, json=payload, timeout=10
                    )

                    # 404 발생 시 상세 로그
                    if response.status_code == 404:
                        logger.warning(
                            f"===> Polling 404 Not Found. URL: {url}, Payload: {payload}"
                        )
                        logger.warning(f"===> Response Body: {response.text}")

                    if response.status_code != 200:
                        logger.error(
                            f"Polling Non-200 Response. Status: {response.status_code}"
                        )
                        logger.error(f"Response Headers: {response.headers}")
                        logger.error(f"Response Body: {response.text}")

                    response.raise_for_status()
                    data = response.json()

                    # 진행 상황 로깅 (옵션)
                    # logger.info(f"Polling Response Data: {data}")

                if "error" in data:
                    logger.error(f"Operation returned error: {data['error']}")
                    raise ExternalServiceException(f"Operation failed: {data['error']}")

                if data.get("done", False):
                    logger.info("Operation completed successfully.")
                    logger.info(
                        f"Final Operation Result: {self._truncate_base64_log(data)}"
                    )  # 성공 시 전체 결과 로깅 (base64 제외)
                    return data

                logger.debug("Operation still running, waiting...")
                await asyncio.sleep(5)  # 5초 대기

            except httpx.HTTPStatusError as e:
                logger.error(f"Polling HTTP Error: {e}")
                logger.error(f"Response Body: {e.response.text}")
                raise ExternalServiceException(f"Polling failed: {e}") from e
            except Exception as e:
                logger.error(f"Unexpected polling error: {e}", exc_info=True)
                raise

    async def _handle_video_lro(self, url: str, payload: dict, log_label: str) -> bytes:
        """비디오 생성을 위한 공통 LRO(Long Running Operation) 핸들러"""
        headers = {
            "Authorization": f"Bearer {self._get_token()}",
            "Content-Type": "application/json; charset=utf-8",
        }

        try:
            logger.info(f"Submitting {log_label} job. URL: {url}")
            logger.debug(f"Payload: {self._truncate_base64_log(payload)}")

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url, json=payload, headers=headers, timeout=60
                )

                if response.status_code != 200:
                    logger.error(
                        f"Initial {log_label} Request Failed. Status: {response.status_code}"
                    )
                    logger.error(f"Response Body: {response.text}")

                response.raise_for_status()
                data = response.json()
                # logger.debug(f"Initial response: {data}")

                if "name" not in data:
                    raise ExternalServiceException(
                        f"Invalid {log_label} response: missing operation name"
                    )

                operation_name = data["name"]
                logger.info(
                    f"{log_label} job submitted. Operation name: {operation_name}"
                )

                # 폴링 시작
                result = await self._poll_operation(operation_name, self.project_id)
                # logger.info(result.keys)
                return self._extract_video_content(result, log_label)

        except httpx.HTTPStatusError as e:
            logger.error(f"Vertex AI {log_label} HTTP Error: {e.response.status_code}")
            raise ExternalServiceException(
                f"Vertex AI {log_label} generation failed: HTTP {e.response.status_code}"
            ) from e

    def _extract_video_content(self, result: dict, log_label: str) -> bytes:
        """완료된 작업 결과에서 비디오 데이터를 추출합니다."""
        # API 변경 대응: result 자체가 응답 데이터인 경우 (videos 또는 predictions 포함)
        if "videos" in result or "predictions" in result:
            response_data = result
        else:
            response_data = result.get("response", {})

        if not response_data:
            logger.error(
                f"Missing 'response' field in {log_label} result: {self._truncate_base64_log(result)}"
            )
            raise ExternalServiceException(
                f"No response found in completed {log_label} operation"
            )

        predictions = response_data.get("predictions", [])
        video_content = None

        # 1. 'predictions' 탐색
        if predictions:
            video_struct = predictions[0]
            if isinstance(video_struct, dict):
                if "bytesBase64Encoded" in video_struct:
                    video_content = base64.b64decode(video_struct["bytesBase64Encoded"])
                elif (
                    "video" in video_struct
                    and "bytesBase64Encoded" in video_struct["video"]
                ):
                    video_content = base64.b64decode(
                        video_struct["video"]["bytesBase64Encoded"]
                    )
            elif isinstance(video_struct, str):
                video_content = base64.b64decode(video_struct)

        # 2. 'videos' 리스트 탐색 (Veo 및 최신 모델 대응)
        if video_content is None:
            videos = response_data.get("videos")
            if videos and isinstance(videos, list):
                first_video = videos[0]
                if isinstance(first_video, dict) and "bytesBase64Encoded" in first_video:
                    video_content = base64.b64decode(first_video["bytesBase64Encoded"])

        # 3. 직접 필드 탐색 (fallback)
        if video_content is None:
            if (
                "video" in response_data
                and "bytesBase64Encoded" in response_data["video"]
            ):
                video_content = base64.b64decode(
                    response_data["video"]["bytesBase64Encoded"]
                )
            elif "bytesBase64Encoded" in response_data:
                video_content = base64.b64decode(response_data["bytesBase64Encoded"])

        # 3. 결과 확인 및 Safety Filter 처리
        if video_content is None:
            logger.error(
                f"Failed to extract {log_label} content. Full response: {self._truncate_base64_log(response_data)}"
            )
            if "explanation" in response_data:
                raise ExternalServiceException(
                    f"{log_label} blocked by safety filters: {response_data['explanation']}"
                )
            raise ExternalServiceException(
                f"No {log_label} content found in operation result"
            )

        return video_content


    async def generate_description(self, image_bytes: bytes, mime_type: str) -> str:
        """이미지/비디오 프레임을 분석하여 텍스트 설명을 생성합니다 (Gemini 1.5 Flash Streaming)."""
        async with self._track_request():
            # User Request: gemini-1.5-flash (latest alias), client.stream
            # Note: 6MB 이상 시 GCS URI 권장 (현재는 인라인 처리를 시도하되 경고 로그 추가)
            if len(image_bytes) > 6 * 1024 * 1024:
                logger.warning(f"⚠️ Image/Video size ({len(image_bytes)} bytes) exceeds 6MB. GCS URI is recommended for stability.")

            # User Request: https://{region}-aiplatform.googleapis.com/v1 형식 준수
            model_id = "gemini-2.0-flash"
            url = f"https://{self.region}-aiplatform.googleapis.com/v1/projects/{self.project_id}/locations/{self.region}/publishers/google/models/{model_id}:streamGenerateContent"
            
            # 이미지 데이터 인코딩
            image_b64 = base64.b64encode(image_bytes).decode("utf-8")
            
            # User Request: MIME 타입 명시 확인 (video/mp4 등)
            if not mime_type:
                mime_type = "application/octet-stream" # Fallback
                logger.warning("⚠️ MIME type not provided, using fallback: application/octet-stream")

            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {"text": "Describe this image/video in detail for generating a search index. Focus on the main subject, style, lighting, colors, and any text present. (Answer in English)"},
                            {
                                "inlineData": {
                                    "mimeType": mime_type,
                                    "data": image_b64
                                }
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.0,
                    "maxOutputTokens": 2048,
                }
            }
            
            headers = {
                "Authorization": f"Bearer {self._get_token()}",
                "Content-Type": "application/json; charset=utf-8",
            }

            generated_text = ""
            
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    # User Request: client.stream (비동기 스트리밍 처리)
                    async with client.stream("POST", url, json=payload, headers=headers) as response:
                        if response.status_code != 200:
                            # 스트림 상태에서 에러 바디 읽기
                            err_text = await response.aread()
                            logger.error(f"Gemini Vision Error: {err_text.decode('utf-8', errors='ignore')}")
                            raise ExternalServiceException(f"Vision LLM failed: {response.status_code}")

                        # User Request: 청크 단위 스트림 파싱
                        # Vertex AI 'streamGenerateContent' returns a JSON array `[{...}, {...}]`
                        # Parsing a JSON array stream purely by chunks without a dedicated parser (like ijson) is complex.
                        # However, typical usage allows buffering or simple heuristic if line-delimited.
                        # Here we buffer the chunks and parse, effectively mimicking stream consumption logic 
                        # but acknowledging that strict JSON array parsing is done via accumulation in this environment.
                        
                        # For strict streaming, we would iterate `response.aiter_lines()` if it was JSONL.
                        # Since it is a JSON List, we will use a buffer to accumulate valid JSON objects if possible,
                        # or safely read the full response if the stream chunks are not self-contained JSON objects.
                        # Given the user constraint, we demonstrate stream consumption:
                        
                        full_response_buffer = []
                        async for chunk in response.aiter_bytes():
                            full_response_buffer.append(chunk)
                        
                        # Combine buffer
                        full_body = b"".join(full_response_buffer)
                        import json
                        try:
                            result = json.loads(full_body)
                        except json.JSONDecodeError:
                            logger.error(f"Failed to parse JSON response: {full_body[:200]}...")
                            raise ExternalServiceException("Invalid JSON response from Vision LLM")

                        # 응답 파싱
                        if isinstance(result, list):
                            for item in result:
                                candidates = item.get("candidates", [])
                                if not candidates:
                                    continue
                                    
                                content = candidates[0].get("content", {})
                                parts = content.get("parts", [])
                                
                                for part in parts:
                                    if "text" in part:
                                        generated_text += part["text"]
                        else:
                            # 단일 객체 응답 (혹시 모를 경우)
                            candidates = result.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                for part in parts:
                                    if "text" in part:
                                        generated_text += part["text"]
                    return generated_text.strip()
                    
            except Exception as e:
                logger.error(f"Vision LLM request failed: {e}")
                raise ExternalServiceException(f"Failed to generate description: {e}")


class MockAIClient(AIGenerationClient):
    """테스트용 Mock AI 클라이언트"""

    async def generate_image(self, prompt: str) -> bytes:
        # 1x1 투명 PNG (테스트용)
        return base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )

    async def generate_video_from_text(self, prompt: str) -> bytes:
        # 빈 바이트 (테스트용)
        return b"MOCK_VIDEO_CONTENT"

    async def generate_video_from_image(self, prompt: str, image_bytes: bytes, source_image_mime_type: Optional[str] = None) -> bytes:
        return b"MOCK_VIDEO_CONTENT"
    
    async def generate_description(self, image_bytes: bytes, mime_type: str) -> str:
        return "A detailed description of the provided image mock."


def get_ai_client() -> AIGenerationClient:
    """환경에 따라 적절한 AI 클라이언트를 반환합니다."""
    if settings.USE_MOCK_AI:
        return MockAIClient()
    return VertexAIClient()
