import uuid
from typing import Optional
from app.domain.interfaces import AssetService, AssetRepository, StorageProvider
from app.schemas.asset import (
    AssetCreate, AssetResponse, JobStatus, 
    get_asset_type_from_mode, get_model_from_mode
)
from app.worker.celery_app import generate_asset_task
import logging
from app.core.exceptions import ResourceNotFoundException
from app.ml.model import embedding_model
import asyncio

logger = logging.getLogger(__name__)

class BaseAssetService(AssetService):
    """
    에셋 생성 및 관리를 담당하는 기본 서비스 구현체
    """
    def __init__(self, repository: AssetRepository, storage_provider: StorageProvider):
        self.repository = repository
        self.storage_provider = storage_provider

    async def create_generation_job(self, asset_in: AssetCreate) -> tuple[str, str]:
        """
        생성 작업을 요청하고 (job_id, status)를 반환합니다. 
        비즈니스 로직(ID 생성, 정보 매핑, DB 저장, 작업 발행)을 캡슐화합니다.
        """
        job_id = str(uuid.uuid4())
        model = get_model_from_mode(asset_in.mode)
        asset_type = get_asset_type_from_mode(asset_in.mode)
        
        logger.info(f"Creating job: job_id={job_id}, mode={asset_in.mode}, model={model}")

        # 0. 중복 요청 방지 (Duplicate Check)
        # 이미지-비디오 모드는 소스 이미지가 다르므로 프롬프트만으로 중복 체크 불가 (Skip)
        if asset_in.mode != "image-to-video":
            existing_asset = await self.repository.get_by_params(
                prompt=asset_in.prompt, 
                model=model, 
                asset_type=asset_type.value
            )
            
            if existing_asset:
                logger.info(f"♻️  Reuse existing job: {existing_asset.job_id} for prompt: '{asset_in.prompt[:20]}...'")
                return existing_asset.job_id, existing_asset.status.value

        # 1. DB에 PENDING 상태로 저장
        try:
            await self.repository.create(
                job_id=job_id,
                prompt=asset_in.prompt,
                model=model,
                asset_type=asset_type.value
            )
            logger.info(f"Job recorded in DB: job_id={job_id}")
        except Exception as e:
            logger.error(f"Failed to create job in DB: {str(e)}")
            raise

        # 2. Celery Worker에 작업 발행
        try:
            logger.info(f"Dispatching Celery task for job_id={job_id}, asset_in : {asset_in.source_image}")
            generate_asset_task.delay(
                job_id=job_id,
                prompt=asset_in.prompt,
                mode=asset_in.mode.value,
                source_image=asset_in.source_image,
                source_image_mime_type=asset_in.source_image_mime_type
            )
            logger.info(f"Celery task dispatched: job_id={job_id}")
        except Exception as e:
            logger.error(f"Failed to dispatch Celery task: {str(e)}")
            # DB 상태를 FAILED로 업데이트하는 등 복구 로직이 필요할 수 있음
            raise
        
        return job_id, JobStatus.PENDING.value

    def _enrich_asset_response(self, asset: AssetResponse) -> AssetResponse:
        """AssetResponse에 result_url을 추가하여 반환합니다."""
        if asset.file_path and asset.status == JobStatus.COMPLETED:
            # 로컬 스토리지인 경우 정적 파일 URL 생성
            # file_path 예시: /app/storage/assets/image_123.png
            filename = asset.file_path.split('/')[-1]
            if str(filename).endswith(('.png', '.jpg', '.mp4')): # 간단한 유효성 검사
                # TODO: 실제 프로덕션에서는 도메인을 환경변수에서 가져와야 함
                # 현재는 상대 경로로 반환하거나 클라이언트가 base URL을 알고 있다고 가정
                # 여기서는 프론트엔드 프록시 또는 API 서버 주소를 포함한 전체 URL 반환 추천
                # 현재 로컬 개발 환경 기준: http://localhost:8000/storage/assets/{filename}
                asset.result_url = f"/storage/assets/{filename}"
        return asset

    async def get_asset_by_id(self, asset_id: int) -> Optional[AssetResponse]:
        """ID를 기반으로 에셋 정보를 조회합니다."""
        asset = await self.repository.get_by_id(asset_id)
        if not asset:
            raise ResourceNotFoundException("Asset", "ID", asset_id)
        return self._enrich_asset_response(asset)

    async def get_asset_by_job_id(self, job_id: str) -> Optional[AssetResponse]:
        """job_id를 기반으로 에셋 정보를 조회합니다."""
        asset = await self.repository.get_by_job_id(job_id)
        if not asset:
            raise ResourceNotFoundException("Asset", "job_id", job_id)
        return self._enrich_asset_response(asset)

    async def update_job_status(self, job_id: str, status: JobStatus | str, file_path: Optional[str] = None):
        """작업의 진행 상태를 업데이트합니다."""
        # 문자열이 들어올 경우 Enum으로 승격 (대소문자 무시)
        if isinstance(status, str):
            try:
                status = JobStatus(status.upper())
            except ValueError:
                # 정의되지 않은 상태인 경우 그대로 진행 (DB에서 에러 발생 유도 또는 기본값 처리)
                pass
            
        await self.repository.update_status(job_id, getattr(status, 'value', status), file_path)

    async def get_assets(self, cursor: Optional[int] = None, limit: int = 100) -> list[AssetResponse]:
        """에셋 목록을 조회합니다."""
        assets = await self.repository.get_all(cursor=cursor, limit=limit)
        return [self._enrich_asset_response(AssetResponse.model_validate(asset)) for asset in assets]

    async def search_assets(self, query: str, limit: int = 20, hybrid: bool = True) -> list[AssetResponse]:
        """자연어 및 키워드 쿼리를 기반으로 에셋을 검색합니다. 하이브리드 모드 지원."""
        logger.info(f"🔍 Searching assets for query: '{query}' (Mode: {'Hybrid' if hybrid else 'Vector Only'})")
        
        # 1. 자연어 쿼리를 벡터로 변환 (Blocking call을 executor에서 실행)
        loop = asyncio.get_event_loop()
        query_vector = await loop.run_in_executor(
            None, 
            lambda: embedding_model.encode(query)[0].tolist()
        )
        
        # 2. 검색 수행
        if hybrid:
            results = await self.repository.search_hybrid(query, query_vector, limit=limit)
        else:
            results = await self.repository.search_by_vector(query_vector, limit=limit)
        
        # 3. 결과 변환 및 Response 객체 생성
        responses = []
        for asset, score in results:
            response_obj = AssetResponse.model_validate(asset)
            response_obj.similarity_score = float(score)
            responses.append(self._enrich_asset_response(response_obj))
            
        logger.info(f"✨ Found {len(responses)} assets for query.")
        return responses

