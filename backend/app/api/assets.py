from typing import Optional, List
from fastapi import APIRouter, Depends, Form, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from sse_starlette.sse import EventSourceResponse
from app.schemas.asset import AssetCreate, JobResponse, AssetResponse, JobStatus, GenerationMode, BatchStatusRequest, BatchStatusResponse
from app.domain.interfaces import AssetService
from app.api.deps import get_asset_service
import logging
import json
import asyncio
import base64

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/stream")
async def stream_assets():
    """
    에셋 상태 변경 이벤트를 실시간으로 스트리밍하는 SSE 엔드포인트.
    """
    from app.core.events import event_bus
    
    async def event_generator():
        logger.info("New SSE connection established")
        try:
            async for event in event_bus.subscribe("asset_updates"):
                # sse_starlette 형행에 맞춰 yield
                yield {
                    "event": "message",
                    "data": json.dumps(event)
                }
        except asyncio.CancelledError:
            logger.info("SSE connection closed by client")
            raise

    return EventSourceResponse(event_generator())

@router.post("/generate", response_model=JobResponse)
async def generate_asset(
    prompt: str = Form(...),
    mode: GenerationMode = Form(GenerationMode.TEXT_TO_IMAGE),
    source_image: UploadFile = File(None),
    service: AssetService = Depends(get_asset_service)
):
    """
    에셋 생성 요청 엔드포인트.
    Multipart/Form-Data 요청을 처리합니다.
    """
    logger.info(f"Received generation request: prompt='{prompt[:50]}...', mode={mode}, has_image={source_image is not None}")

    source_image_b64 = None
    source_image_mime = None
    if source_image:
        file_content = await source_image.read()
        source_image_b64 = base64.b64encode(file_content).decode("utf-8")
        source_image_mime = source_image.content_type
        logger.info(f"Processed source image: size={len(file_content)} bytes, mime={source_image_mime}")

    asset_in = AssetCreate(
        prompt=prompt,
        mode=mode,
        source_image=source_image_b64,
        source_image_mime_type=source_image_mime
    )

    logger.debug(f"[HAWKEYE] Calling service.create_generation_job with asset_in: {asset_in.dict(exclude={'source_image'})}")
    try:
        job_id, status = await service.create_generation_job(asset_in)
        logger.info(f"[HAWKEYE] Job created/reused: job_id={job_id}, status={status}")
        return JobResponse(job_id=job_id, status=status)
    except Exception as e:
        logger.error(f"Failed to create generation job: {e}", exc_info=True)
        raise

@router.post("/batch-status", response_model=BatchStatusResponse)
async def batch_status(
    request: BatchStatusRequest,
    service: AssetService = Depends(get_asset_service)
):
    """
    여러 Job ID의 상태를 한 번에 조회하는 엔드포인트.
    SSE 연결 끊김 중 누락된 이벤트를 Catch-up하는 데 사용됩니다.
    """
    # Pydantic의 max_length는 list에 작동하지 않으므로 수동 검증
    if len(request.task_ids) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 tasks per request")
    
    # 중복 제거 + 순서 보존 (dict.fromkeys는 삽입 순서 유지)
    unique_task_ids = list(dict.fromkeys(request.task_ids))
    
    logger.info(f"Batch status request: {len(request.task_ids)} tasks ({len(unique_task_ids)} unique)")
    
    # Bulk 조회 (Repository의 IN 절 사용, N+1 문제 해결)
    assets = await service.repository.get_by_job_ids(unique_task_ids)
    
    # job_id → asset 매핑 (O(n) 시간 복잡도)
    job_id_to_asset = {asset.job_id: asset for asset in assets}
    
    # 클라이언트가 보낸 순서대로 재정렬 + Service의 enrich 로직 재사용
    from app.schemas.asset import AssetResponse
    tasks: List[AssetResponse] = []
    for job_id in unique_task_ids:
        if job_id in job_id_to_asset:
            asset = job_id_to_asset[job_id]
            # Service의 _enrich_asset_response 재사용 (result_url 생성 등)
            enriched = service._enrich_asset_response(AssetResponse.model_validate(asset))
            tasks.append(enriched)
    
    logger.info(f"Batch status response: {len(tasks)} tasks found (ordered by client request)")
    return BatchStatusResponse(tasks=tasks)

@router.get("/search", response_model=list[AssetResponse])
async def search_assets(
    q: str,
    limit: int = 20,
    hybrid: bool = True,
    service: AssetService = Depends(get_asset_service)
):
    """
    자연어 및 키워드 쿼리를 이용한 하이브리드 검색 엔드포인트.
    """
    if not q or not q.strip():
        raise HTTPException(status_code=400, detail="Search query (q) is required")
    
    return await service.search_assets(query=q, limit=limit, hybrid=hybrid)

@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: int,
    service: AssetService = Depends(get_asset_service)
):
    """
    에셋 상세 정보 조회 엔드포인트.
    """
    return await service.get_asset_by_id(asset_id)

@router.get("/job/{job_id}", response_model=AssetResponse)
async def get_asset_by_job(
    job_id: str,
    service: AssetService = Depends(get_asset_service)
):
    """
    job_id로 에셋 조회 엔드포인트 (폴링용).
    """
    logger.debug(f"Polling job status: job_id={job_id}")
    return await service.get_asset_by_job_id(job_id)

@router.get("", response_model=list[AssetResponse])
async def list_assets(
    cursor: Optional[int] = None,
    limit: int = 100,
    service: AssetService = Depends(get_asset_service)
):
    """
    에셋 목록 조회 엔드포인트.
    최신순(ID 역순)으로 정렬된 에셋 목록을 반환합니다.
    커서(cursor)는 이전에 받은 마지막 에셋의 ID를 사용합니다.
    """
    return await service.get_assets(cursor=cursor, limit=limit)


@router.get("/{asset_id}/download")
async def download_asset(
    asset_id: int,
    service: AssetService = Depends(get_asset_service)
):
    """
    에셋 다운로드 엔드포인트 (프록시).
    
    브라우저 진행률 표시를 위해 Content-Length 헤더를 포함합니다.
    - Content-Disposition: attachment (강제 다운로드)
    - Content-Length: 파일 크기 (진행률 % 및 남은 시간 표시용)
    - Content-Type: 자동 감지 또는 image/png
    """
    from pathlib import Path
    import mimetypes
    from app.core.config import settings
    
    # 에셋 정보 조회
    asset = await service.get_asset_by_id(asset_id)
    
    # TODO: S3 사용 시 구현 필요

    # 파일 경로 확인 (로컬 파일 시스템)
    filename_from_url = Path(asset.result_url).name
    file_path = settings.STORAGE_BASE / filename_from_url
    
    # MIME 타입 자동 감지 (mimetypes 라이브러리 사용)
    media_type, _ = mimetypes.guess_type(str(file_path))
    if media_type is None:
        media_type = 'application/octet-stream'
    
    logger.info(f"Serving file for download: asset_id={asset_id}, path={file_path}")
    
    # FileResponse는 자동으로 파일 존재 여부 체크 및 Content-Length 헤더 추가
    # 파일이 없으면 자동으로 404 에러 반환
    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=f"generated-{asset_id}{file_path.suffix}",
        headers={
            "Content-Disposition": f'attachment; filename="generated-{asset_id}{file_path.suffix}"'
        }
    )

