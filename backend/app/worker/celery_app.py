import base64
import logging
from typing import Optional
from celery import Celery
from app.core.config import settings
from app.core.exceptions import ExternalServiceException, ValidationException

logger = logging.getLogger(__name__)

celery_app = Celery(
    "worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

# Pillow import for dimension extraction
import io
from PIL import Image

celery_app.conf.task_routes = {
    "generate_asset_task": {"queue": "main_queue"},
    "process_asset_metadata": {"queue": "analysis_queue"},
    "app.worker.tasks.*": {"queue": "main_queue"}
}

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# -------------------------------------------------------------------------
# Worker Process Initialization Check
# -------------------------------------------------------------------------
from celery.signals import worker_process_init
from app.infrastructure.database import worker_engine

@worker_process_init.connect
def init_worker(**kwargs):
    """
    워커 프로세스가 포크된 직후 호출됩니다.
    부모 프로세스로부터 상속받은 커넥션 풀을 폐기하고,
    새로운 프로세스에서 자체적인 커넥션을 맺도록 강제합니다.
    """
    try:
        worker_engine.sync_engine.dispose()
        # ✨ Redis 커넥션도 초기화하여 자식 프로세스 간 충돌 방지
        from app.core.events import event_bus
        import asyncio
        try:
            # 동기 환경이므로 새로운 루프로 닫기 시도
            loop = asyncio.new_event_loop()
            loop.run_until_complete(event_bus.close())
            loop.close()
        except:
            pass
        logger.info("✅ Worker engine and EventBus reset completed.")
    except Exception as e:
        logger.error(f"❌ Failed to reset worker resources: {e}")



@celery_app.task(name="generate_asset_task", bind=True, max_retries=settings.MAX_TASK_RETRIES)
def generate_asset_task(
    self,
    job_id: str, 
    prompt: str, 
    mode: str,
    source_image: Optional[str] = None,
    source_image_mime_type: Optional[str] = None
):
    from app.infrastructure.database import worker_session_maker
    from app.infrastructure.repositories import SQLAlchemyAssetRepository
    from app.infrastructure.storage import get_storage_provider
    from app.infrastructure.vertex_ai import get_ai_client
    from app.infrastructure.models import JobStatus

    # 상태 업데이트 전용 헬퍼 (충돌 방지를 위해 항상 새 세션 사용)
    async def _safe_update_status(status_val: str, path: Optional[str] = None, width: Optional[int] = None, height: Optional[int] = None, error_msg: Optional[str] = None):
        logger.debug(f"[HAWKEYE:WORKER] _safe_update_status called: job_id={job_id}, status={status_val}, error={error_msg[:30] if error_msg else None}")
        try:
            # NullPool 엔진을 사용하는 워커 전용 세션 생성
            async with worker_session_maker() as temp_session:
                async with temp_session.begin():
                    repo = SQLAlchemyAssetRepository(temp_session)
                    await repo.update_status(job_id, status_val, file_path=path, width=width, height=height, error_msg=error_msg)
            
            # 실시간 이벤트 브로드캐스팅 (Redis Pub/Sub)
            from app.core.events import event_bus
            from datetime import datetime
            event_data = {
                "job_id": job_id,
                "status": status_val,
                "result_url": path,
                "error": error_msg,
                "updated_at": datetime.utcnow().isoformat() + "Z"
            }
            # Redis 발행 시 타임아웃/예외에 더 민감하게 대응
            import asyncio
            try:
                await asyncio.wait_for(event_bus.publish("asset_updates", event_data), timeout=1.5)
                logger.debug(f"[HAWKEYE:WORKER] Broadcast success: {status_val} for {job_id}")
            except Exception as eb_err:
                logger.warning(f"[HAWKEYE:WORKER] Broadcast delayed/failed (non-critical): {eb_err}")

        except Exception as e:
            logger.error(f"[HAWKEYE:WORKER] CRITICAL: Status update FAILED for {job_id}: {e}")


    async def _process():
        logger.info(f"🚀 Worker started processing job: job_id={job_id}, mode={mode}")
        
        try:
            # 1. 상태를 PROCESSING으로 변경 (재시도 중이면 이미 PROCESSING이므로 업데이트 생략)
            retry_count = self.request.retries
            if retry_count == 0:
                await _safe_update_status(JobStatus.PROCESSING.value, error_msg="")
            else:
                logger.info(f"[HAWKEYE:WORKER] Task resumed (Retry {retry_count}). Skipping redundant PROCESSING update to preserve message.")

            
            # 2. AI 모델 호출
            logger.info(f"Calling Vertex AI client for job_id={job_id}, mode={mode}")
            
            storage = get_storage_provider()
            ai_client = get_ai_client()
            
            if mode == "text-to-image":
                content = await ai_client.generate_image(prompt)
                extension = "png"
            elif mode == "text-to-video":
                content = await ai_client.generate_video_from_text(prompt)
                extension = "mp4"
            elif mode == "image-to-video":
                if not source_image:
                    raise ValidationException("Image-to-Video mode requires source_image")
                try:
                    image_bytes = base64.b64decode(source_image)
                except Exception as e:
                    raise ValidationException(f"Invalid base64 image: {e}") from e
                
                content = await ai_client.generate_video_from_image(prompt, image_bytes, source_image_mime_type)
                extension = "mp4"
            else:
                raise ValidationException(f"Unknown generation mode: {mode}")
            
            logger.info(f"AI content generated for job_id={job_id}, size={len(content)} bytes")

            # 2.5 이미지 크기 측정 (Lazy Loading)
            width = None
            height = None
            if mode == "text-to-image" and content:
                try:
                    with Image.open(io.BytesIO(content)) as img:
                        width, height = img.size
                        logger.info(f"Image dimensions extracted: {width}x{height}")
                except Exception as e:
                    logger.warning(f"Failed to extract image dimensions: {e}")

            # 3. 파일 저장
            filename = f"{job_id}.{extension}"
            logger.info(f"Saving file for job_id={job_id}: {filename}")
            file_path = await storage.save_file(content, filename)
            logger.info(f"File saved at: {file_path}")
            
            # 4. DB 업데이트 (COMPLETED)
            logger.info(f"Finalizing job status to COMPLETED for job_id={job_id}")
            await _safe_update_status(JobStatus.COMPLETED.value, path=file_path, width=width, height=height, error_msg="")
            logger.info(f"✅ Job {job_id} completed successfully: {file_path}")

            # 5. 메타데이터 생성 트리거 (비동기)
            logger.info(f"Triggering metadata processing for job_id={job_id}")
            process_asset_metadata.delay(job_id)
            
        except Exception as e:
            logger.exception(f"❌ Job {job_id} processing error: {e}")
            raise
    
    from asgiref.sync import async_to_sync
    import sqlalchemy as sa
    from app.infrastructure.database import sync_worker_engine
    
    # [Emergency Sync Update] 비동기 루프가 꼬였을 때를 위한 동기식 상태 업데이트 함수
    def _sync_update_status(status_val: str, error_msg: Optional[str] = None):
        logger.warning(f"[HAWKEYE:SYNC] Emergency SYNC update initiated: {job_id} -> {status_val}")
        try:
            with sync_worker_engine.connect() as conn:
                assets_t = sa.table("assets", sa.column("job_id"), sa.column("status"), sa.column("error_message"))
                stmt = sa.update(assets_t).where(assets_t.c.job_id == job_id).values(
                    status=status_val
                )
                if error_msg is not None:
                    stmt = stmt.values(error_message=error_msg)
                result = conn.execute(stmt)
                conn.commit()
                logger.info(f"[HAWKEYE:SYNC] Emergency update SUCCESS: {result.rowcount} row(s) updated")
            
            # 🚀 [CRITICAL] 동기식 Redis 발행 추가
            from app.core.events import event_bus
            from datetime import datetime
            event_data = {
                "job_id": job_id,
                "status": status_val,
                "result_url": None,
                "error": error_msg,
                "updated_at": datetime.utcnow().isoformat() + "Z"
            }
            event_bus.publish_sync("asset_updates", event_data)
            logger.info(f"[HAWKEYE:SYNC] Emergency broadcast sent: {status_val}")
            
        except Exception as se:
            logger.error(f"[HAWKEYE:SYNC] CRITICAL: SYNC fallback failed: {se}")

    try:
        async_to_sync(_process)()
        logger.info(f"[HAWKEYE:WORKER] _process() async_to_sync finished normally for {job_id}")
    except Exception as exc:
        retry_count = self.request.retries
        max_retries = self.max_retries

        # 디버깅을 위한 코드
        exc_name = type(exc).__name__
        logger.error(f"[HAWKEYE:WORKER] Exception caught: {exc_name} for {job_id}. Current retry pool: {retry_count}/{max_retries}")
        # 끝.

        if isinstance(exc, (ExternalServiceException, Exception)) and not isinstance(exc, ValidationException):
            if retry_count < max_retries:
                msg = f"일시적 오류로 재시도 중 ({retry_count + 1}/{max_retries})..."
                logger.info(f"[HAWKEYE:WORKER] Decision: RETRY. Attempt {retry_count + 1}")
                try:
                    async_to_sync(_safe_update_status)("PROCESSING", error_msg=msg)
                except Exception as update_err:
                    logger.warning(f"[HAWKEYE:WORKER] Async update failed before retry: {update_err}")
                    _sync_update_status("PROCESSING", error_msg=msg)
                
                raise self.retry(exc=exc, countdown=2 ** retry_count)
            else:
                error_detail = f"최종 실패 ({max_retries}/{max_retries}): {str(exc)}"
                logger.error(f"[HAWKEYE:WORKER] Decision: PERMANENT FAILURE for {job_id}. Force-killing with SYNC update.")
                _sync_update_status("FAILED", error_msg=error_detail)
                raise exc
        elif isinstance(exc, ValidationException):
            logger.error(f"[HAWKEYE:WORKER] Decision: VALIDATION FAILURE. No retry.")
            _sync_update_status("FAILED", error_msg=str(exc))
            return
        else:
            _sync_update_status("FAILED", error_msg=f"Unexpected: {str(exc)}")
            raise exc

@celery_app.task(name="process_asset_metadata", bind=True, max_retries=3, soft_time_limit=60, time_limit=120)
def process_asset_metadata(self, job_id: str):
    """
    에셋의 메타데이터(Search Document, Embedding)를 생성하는 후처리 작업
    """
    from app.infrastructure.database import worker_session_maker
    from app.infrastructure.repositories import SQLAlchemyAssetRepository
    from app.infrastructure.vertex_ai import get_ai_client
    from app.services.indexer import IndexerService
    from asgiref.sync import async_to_sync

    async def _process_metadata():
        logger.info(f"🔍 Starting metadata processing for job_id={job_id}")
        async with worker_session_maker() as session:
            async with session.begin():
                repo = SQLAlchemyAssetRepository(session)
                ai_client = get_ai_client()
                indexer = IndexerService(repo, ai_client)

                # job_id로 asset 조회
                asset = await repo.get_by_job_id(job_id)
                if not asset:
                    logger.error(f"❌ Asset not found for metadata processing: {job_id}")
                    return

                await indexer.index_asset(asset.id)
                logger.info(f"✨ Metadata processing completed for job_id={job_id}")

    try:
        # async_to_sync를 사용하여 비동기 함수(_process_metadata)를 동기식 Celery 워커에서 안전하게 실행합니다.
        # 내부적으로 새로운 이벤트 루프를 생성하고 실행 완료 후 정리합니다.
        async_to_sync(_process_metadata)()
    except Exception as e:
        logger.exception(f"❌ Metadata processing failed for job_id={job_id}: {e}")
        # 메타데이터 생성 실패는 치명적이지 않으므로 태스크 실패로만 기록하고 재시도
        retry_count = self.request.retries
        if retry_count < self.max_retries:
             raise self.retry(exc=e, countdown=2 ** retry_count)
        else:
            logger.error(f"❌ Metadata processing permanently failed for {job_id}")
