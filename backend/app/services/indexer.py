import asyncio
import logging
import os
import mimetypes
import aiofiles

from app.domain.interfaces import AssetRepository, AIGenerationClient
from app.ml.model import embedding_model
from app.core.exceptions import DomainException

logger = logging.getLogger(__name__)

# Vertex AI REST API payload limit check (approx 10-20MB safety)
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20MB

class IndexerService:
    """
    에셋의 메타데이터(Search Document, Embedding)를 생성하고 업데이트하는 서비스.
    Vision LLM을 사용하여 이미지를 분석하고, 텍스트 임베딩을 생성합니다.
    """

    def __init__(
        self, 
        asset_repo: AssetRepository,
        ai_client: AIGenerationClient
    ):
        self.asset_repo = asset_repo
        self.ai_client = ai_client
        self.embedding_model = embedding_model

    async def index_asset(self, asset_id: int) -> None:
        """
        에셋을 인덱싱합니다 (Description 생성 + Embedding 생성 + DB 업데이트).
        """
        logger.info(f"🔍 에셋 인덱싱 시작 (Asset ID: {asset_id})")
        
        # 1. 에셋 조회
        asset = await self.asset_repo.get_by_id(asset_id)
        if not asset:
            logger.error(f"❌ 에셋을 찾을 수 없습니다 (ID: {asset_id})")
            raise DomainException("Asset not found", status_code=404)

        if not asset.file_path:
            logger.warning(f"⚠️ 파일 경로가 없는 에셋입니다 (ID: {asset_id}). 인덱싱을 건너뜁니다.")
            return

        # 2. 파일 읽기 (로컬 스토리지 가정)
        # TODO: S3 지원 시 StorageProvider를 통해 바이트를 가져오도록 수정 필요
        # 현재 file_path는 컨테이너 내부 절대 경로라고 가정 (/app/storage/assets/...)
        try:
            # OOM 방지를 위한 파일 크기 체크
            file_size = os.path.getsize(asset.file_path)
            if file_size > MAX_FILE_SIZE_BYTES:
                logger.error(f"❌ 파일 크기가 너무 큽니다 ({file_size} bytes). Skipping indexing to prevent OOM/Payload error.")
                return

            async with aiofiles.open(asset.file_path, mode='rb') as f:
                file_bytes = await f.read()
        except FileNotFoundError:
            logger.error(f"❌ 파일을 찾을 수 없습니다: {asset.file_path}")
            return
        except Exception as e:
            logger.error(f"❌ 파일 읽기 실패: {e}")
            raise DomainException(f"Failed to read asset file: {e}")

        # MIME Type 추론 (mimetypes 사용)
        mime_type, _ = mimetypes.guess_type(asset.file_path)
        if not mime_type:
            mime_type = "application/octet-stream" # Fallback
            logger.warning(f"⚠️ MIME type prediction failed. Using fallback: {mime_type}")


        # 3. Vision LLM으로 설명 생성 (Search Document)
        # Idempotency Check: 이미 설명글이 있다면 Vision API 호출 생략
        if asset.search_document:
            logger.info(f"♻️ 이미 설명글이 존재합니다 (ID: {asset_id}). Vision API 호출을 건너뜁니다.")
            description = asset.search_document
        else:
            try:
                logger.info(f"🧠 Vision LLM 분석 요청 (MIME: {mime_type})...")
                description = await self.ai_client.generate_description(file_bytes, mime_type)
                logger.info(f"✅ 설명 생성 완료: {description[:50]}...")
            except Exception as e:
                logger.error(f"❌ Vision LLM 분석 실패: {e}")
                raise DomainException(f"Vision LLM failed: {e}")

        # 4. 임베딩 생성
        # 설명글이 변경되었거나 임베딩이 없는 경우 수행
        if asset.embedding_kure and asset.search_document == description:
            logger.info(f"♻️ 이미 임베딩이 존재합니다 (ID: {asset_id}). 임베딩 생성을 건너뜁니다.")
            return

        try:
            logger.info("🧮 임베딩 벡터 생성 중 (CPU-bound job running in executor)...")
            # CPU-bound 작업을 이벤트 루프가 아닌 별도 스레드 풀에서 실행
            loop = asyncio.get_running_loop()
            
            # encode returns numpy array (1, 1024), convert to list
            embedding_vector = await loop.run_in_executor(
                None,  # Use default ThreadPoolExecutor
                lambda: self.embedding_model.encode(description)[0].tolist()
            )
        except Exception as e:
            logger.error(f"❌ 임베딩 생성 실패: {e}")
            raise DomainException(f"Embedding failed: {e}")

        # 5. DB 업데이트
        await self.asset_repo.update_metadata(
            asset_id=asset_id,
            search_document=description,
            embedding_kure=embedding_vector
        )
        logger.info(f"✨ 에셋 인덱싱 완료 (ID: {asset_id})")
