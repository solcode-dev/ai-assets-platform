from app.schemas.asset import AssetType
from app.schemas.aimodel import AIImageModelImageGen, AIVideoModelVeo

from fastapi import APIRouter
import logging
import time
from datetime import datetime
from google.cloud import monitoring_v3
import google.auth
from pydantic import BaseModel
from typing import List
from redis.asyncio import from_url
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

class VertexAIStats(BaseModel):
    active_requests: int
    completed_requests: int
    limit_requests: int

class VertexAIStatsResponse(BaseModel):
    success: bool
    data: VertexAIStats

@router.get("/stats", response_model=VertexAIStatsResponse)
async def get_vertex_ai_stats():
    """
    Redis에서 Vertex AI 요청 통계를 조회합니다.
    """
    try:
        r = from_url(settings.REDIS_URL, decode_responses=True)
        active = await r.get("vertex_ai:active_requests")
        completed = await r.get("vertex_ai:completed_requests")
        await r.close()
        
        return VertexAIStatsResponse(
            success=True,
            data=VertexAIStats(
                active_requests=int(active) if active else 0,
                completed_requests=int(completed) if completed else 0,
                limit_requests=1
            )
        )
    except Exception as e:
        logger.error(f"Failed to fetch Vertex AI stats from Redis: {e}")
        # 에러 시에도 스키마를 맞추기 위해 0으로 반환하거나 에러 처리 필요
        # 여기서는 우선 기본값 0으로 반환하도록 함 (success=False 버전 스키마는 선택사항)
        return VertexAIStatsResponse(
            success=False,
            data=VertexAIStats(active_requests=0, completed_requests=0)
        )

def get_gcp_metric(project_id: str, credentials, metric_type: str, hours: int = 1):
    """
    GCP Cloud Monitoring API를 통해 특정 메트릭 데이터를 조회합니다.
    """
    try:
        logger.info(f"Connecting to GCP Monitoring for project: {project_id}")
        # credentials를 명시적으로 전달
        client = monitoring_v3.MetricServiceClient(credentials=credentials)
        project_name = f"projects/{project_id}"
        
        now = time.time()
        seconds = int(now)
        nanos = int((now - seconds) * 10**9)
        
        interval = monitoring_v3.TimeInterval(
            {
                "end_time": {"seconds": seconds, "nanos": nanos},
                "start_time": {"seconds": int(now - 3600 * hours), "nanos": nanos},
            }
        )
        
        # Vertex AI Prediction 서비스의 API 요청 수 조회
        # 필터: aiplatform.googleapis.com 서비스에 대한 요청
        filter_str = (
            f'metric.type = "{metric_type}" '
            'AND resource.type = "consumed_api" '
            'AND resource.labels.service = "aiplatform.googleapis.com"'
        )
        
        results = client.list_time_series(
            request={
                "name": project_name,
                "filter": filter_str,
                "interval": interval,
                "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
            }
        )
        
        total_count = 0
        
        for result in results:
            for point in result.points:
                total_count += point.value.int64_value
                
        return total_count
        
    except Exception as e:
        logger.error(f"Failed to fetch GCP metrics: {e}")
        return -1  # 에러 발생 시 -1 반환



class AIModelInfo(BaseModel):
    name: str
    model: AIImageModelImageGen | AIVideoModelVeo
    

class AIModelsResponse(BaseModel):
    asset_type: AssetType
    models: List[AIModelInfo]

@router.get("/models", response_model=AIModelsResponse)
async def get_supported_ai_models(asset_type: AssetType):
    """
    지원하는 AI 모델 목록을 반환합니다.
    """

    if asset_type == AssetType.IMAGE:
        models = [
            AIModelInfo(name=AIImageModelImageGen.IMAGEN_3_0_GENERATE_002, model=AIImageModelImageGen.IMAGEN_3_0_GENERATE_002),
            AIModelInfo(name=AIImageModelImageGen.IMAGEN_3_0_GENERATE_001, model=AIImageModelImageGen.IMAGEN_3_0_GENERATE_001),
            AIModelInfo(name=AIImageModelImageGen.IMAGEN_3_0_FAST_GENERATE_001, model=AIImageModelImageGen.IMAGEN_3_0_FAST_GENERATE_001),
            AIModelInfo(name=AIImageModelImageGen.IMAGEN_3_0_CAPABILITY_001, model=AIImageModelImageGen.IMAGEN_3_0_CAPABILITY_001),
            AIModelInfo(name=AIImageModelImageGen.IMAGEN_4_0_GENERATE_001, model=AIImageModelImageGen.IMAGEN_4_0_GENERATE_001),
            AIModelInfo(name=AIImageModelImageGen.IMAGEN_4_0_FAST_GENERATE_001, model=AIImageModelImageGen.IMAGEN_4_0_FAST_GENERATE_001),
            AIModelInfo(name=AIImageModelImageGen.IMAGEN_4_0_ULTRA_GENERATE_001, model=AIImageModelImageGen.IMAGEN_4_0_ULTRA_GENERATE_001),
        ]
    elif asset_type == AssetType.VIDEO:
        models = [
            AIModelInfo(name=AIVideoModelVeo.VEO_2_0_GENERATE_001, model=AIVideoModelVeo.VEO_2_0_GENERATE_001),
            AIModelInfo(name=AIVideoModelVeo.VEO_2_0_GENERATE_EXP, model=AIVideoModelVeo.VEO_2_0_GENERATE_EXP),
            AIModelInfo(name=AIVideoModelVeo.VEO_2_0_GENERATE_PREVIEW, model=AIVideoModelVeo.VEO_2_0_GENERATE_PREVIEW),
            AIModelInfo(name=AIVideoModelVeo.VEO_3_0_GENERATE_001, model=AIVideoModelVeo.VEO_3_0_GENERATE_001),
            AIModelInfo(name=AIVideoModelVeo.VEO_3_0_FAST_GENERATE_001, model=AIVideoModelVeo.VEO_3_0_FAST_GENERATE_001),
            AIModelInfo(name=AIVideoModelVeo.VEO_3_1_GENERATE_001, model=AIVideoModelVeo.VEO_3_1_GENERATE_001),
            AIModelInfo(name=AIVideoModelVeo.VEO_3_1_FAST_GENERATE_001, model=AIVideoModelVeo.VEO_3_1_FAST_GENERATE_001),
            AIModelInfo(name=AIVideoModelVeo.VEO_3_1_GENERATE_PREVIEW, model=AIVideoModelVeo.VEO_3_1_GENERATE_PREVIEW),
            AIModelInfo(name=AIVideoModelVeo.VEO_3_1_FAST_GENERATE_001, model=AIVideoModelVeo.VEO_3_1_FAST_GENERATE_001),
        ]
    else:
        models = []

    return AIModelsResponse(asset_type=asset_type, models=models)


@router.get("/quota")
async def get_quota():
    """
    실제 GCP Cloud Monitoring API를 통해 Vertex AI 사용량을 조회합니다.
    """
    try:
        # 서비스 계정 키 파일(JSON) 또는 환경 변수(GOOGLE_APPLICATION_CREDENTIALS)에서 인증 정보 로드
        credentials, project_id = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
    except Exception as e:
        logger.error(f"Failed to load credentials: {e}")
        project_id = None
        credentials = None

    # Project ID가 없는 경우
    if not project_id:
        return {
            "success": False,
            "error": "Could not determine GCP Project ID from credentials",
            "data": None
        }

    # 실제 메트릭 조회 (최근 1시간)
    # serviceruntime.googleapis.com/api/request_count 사용
    request_count = get_gcp_metric(
        project_id, 
        credentials,
        "serviceruntime.googleapis.com/api/request_count"
    )
    
    # GCP 연동 실패 시
    if request_count == -1:
        return {
            "success": False,
            "error": "Failed to fetch GCP metrics (check logs for details)",
            "data": None
        }

    is_real_data = True
    current_usage = request_count
    
    # 할당량(Limit) 설정 (분당 기준 -> 시간당으로 환산 표시)
    limit_per_min = 60
    limit_hourly = limit_per_min * 60
    
    # 상태 결정
    status = "stable"
    if current_usage > limit_hourly * 0.9:
        status = "critical"
    elif current_usage > limit_hourly * 0.7:
        status = "warning"
        
    formatted_status = "active"
    if status == "critical":
        formatted_status = "limited"

    models = [
        {
            "name": "Imagen 3.0 (Image)",
            "type": "image",
            "limit": limit_hourly,
            "used": current_usage if is_real_data else 0, # 현재는 이미지/비디오 구분 없이 통합 카운트
            "remaining": max(0, limit_hourly - (current_usage if is_real_data else 0)),
            "unit": "requests/hour",
            "status": status
        },
        {
            "name": "Veo 3.0 (Video)",
            "type": "video",
            "limit": 10,  # 비디오는 별도 제한
            "used": 0,    # 비디오 별도 필터링 미구현하여 0 처리
            "remaining": 10,
            "unit": "requests/min",
            "status": "stable"
        }
    ]

    return {
        "success": True,
        "data": {
            "models": models,
            "overall_status": formatted_status,
            "last_updated": datetime.utcnow().isoformat() + "Z",
            "is_real_data": is_real_data
        }
    }
