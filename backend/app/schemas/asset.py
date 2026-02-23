from datetime import datetime
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field

class JobStatus(str, Enum):
    """작업 상태"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class GenerationMode(str, Enum):
    """생성 모드 (API 요청 시 사용)"""
    TEXT_TO_IMAGE = "text-to-image"
    TEXT_TO_VIDEO = "text-to-video"
    IMAGE_TO_VIDEO = "image-to-video"

class AssetType(str, Enum):
    """에셋 타입 (DB 저장용, 과제 요구사항)"""
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"

# 모델 매핑
MODEL_MAPPING = {
    GenerationMode.TEXT_TO_IMAGE: "imagen-3.0-fast-generate-001",
    GenerationMode.TEXT_TO_VIDEO: "veo-3.0-fast-generate-001",
    GenerationMode.IMAGE_TO_VIDEO: "veo-3.0-fast-generate-001",
}

def get_asset_type_from_mode(mode: GenerationMode) -> AssetType:
    """GenerationMode를 AssetType으로 변환"""
    if mode == GenerationMode.TEXT_TO_IMAGE:
        return AssetType.IMAGE
    return AssetType.VIDEO

def get_model_from_mode(mode: GenerationMode) -> str:
    """GenerationMode에 해당하는 Vertex AI 모델명 반환"""
    return MODEL_MAPPING[mode]

class AssetCreate(BaseModel):
    """에셋 생성 요청 스키마"""
    prompt: str = Field(..., min_length=1, max_length=1000, description="에셋 생성을 위한 텍스트 프롬프트")
    mode: GenerationMode = Field(default=GenerationMode.TEXT_TO_IMAGE, description="생성 모드")
    # Image-to-Video 모드 시 사용할 이미지 (Base64 또는 URL)
    source_image: Optional[str] = Field(default=None, description="Image-to-Video 모드 시 소스 이미지")
    source_image_mime_type: Optional[str] = Field(default=None, description="소스 이미지의 MIME 타입")

class JobResponse(BaseModel):
    """작업 생성 응답 스키마"""
    job_id: str
    status: JobStatus
    message: Optional[str] = None

class AssetResponse(BaseModel):
    """에셋 조회 응답 스키마"""
    id: int
    file_path: Optional[str] = None
    prompt: str
    model: str
    asset_type: AssetType
    created_at: datetime
    width: Optional[int] = None
    height: Optional[int] = None
    
    # 작업 상태 확인용
    job_id: str
    status: JobStatus
    updated_at: datetime
    result_url: Optional[str] = None
    similarity_score: Optional[float] = Field(default=None, description="검색 시 유사도 점수 (0~1)")
    error_message: Optional[str] = Field(default=None, description="에러 메시지 또는 재시도 알림")

    model_config = {
        "from_attributes": True
    }

class BatchStatusRequest(BaseModel):
    """배치 상태 조회 요청 스키마"""
    task_ids: list[str] = Field(..., description="조회할 Job ID 목록 (최대 100개)")
    last_sync_time: Optional[datetime] = Field(default=None, description="마지막 동기화 시점 (누락 이벤트 확인용)")

class BatchStatusResponse(BaseModel):
    """배치 상태 조회 응답 스키마"""
    tasks: list[AssetResponse] = Field(description="조회된 태스크 목록")

class StandardResponse(BaseModel):
    """표준 API 응답 스키마"""
    success: bool
    data: Any = None
    error: Optional[str] = None
