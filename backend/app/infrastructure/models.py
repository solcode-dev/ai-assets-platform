from sqlalchemy import Column, Integer, String, Enum as SQLEnum, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import DeclarativeBase
from enum import Enum
from pgvector.sqlalchemy import Vector

class Base(DeclarativeBase):
    pass

class JobStatus(str, Enum):
    """작업 상태 (내부 관리용)"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class AssetTypeDB(str, Enum):
    """에셋 타입 (과제 요구사항: image/video)"""
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"

class Asset(Base):
    """
    에셋 테이블
    
    과제 요구사항 필드:
    - id, file_path, prompt, model, asset_type (image/video), created_at
    
    추가 필드 (비동기 작업 관리용):
    - job_id, status, updated_at
    """
    __tablename__ = "assets"

    # 과제 요구사항 필드
    id = Column(
        Integer, 
        primary_key=True, 
        index=True,
        comment="에셋 고유 식별자 (Primary Key)"
    )
    file_path = Column(
        String, 
        nullable=True,
        comment="생성된 에셋 파일의 저장 경로 (로컬 또는 S3)"
    )
    prompt = Column(
        Text, 
        nullable=False,
        comment="에셋 생성에 사용된 텍스트 프롬프트"
    )
    model = Column(
        String, 
        nullable=False,
        comment="사용된 AI 모델명 (예: imagen-3.0-fast-generate-001, veo-3.0-fast-generate-001)"
    )
    asset_type = Column(
        SQLEnum(AssetTypeDB), 
        nullable=False,
        comment="에셋 타입: IMAGE(이미지) 또는 VIDEO(비디오)"
    )
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        comment="에셋 레코드 생성 시간"
    )
    
    # 비동기 작업 관리용 추가 필드
    job_id = Column(
        String, 
        unique=True, 
        index=True, 
        nullable=False,
        comment="비동기 작업 추적을 위한 고유 작업 ID (UUID)"
    )
    status = Column(
        SQLEnum(JobStatus), 
        default=JobStatus.PENDING, 
        nullable=False,
        comment="작업 상태: PENDING(대기) -> PROCESSING(처리중) -> COMPLETED(완료) 또는 FAILED(실패)"
    )
    updated_at = Column(
        DateTime(timezone=True), 
        onupdate=func.now(), 
        server_default=func.now(),
        comment="에셋 레코드 최종 수정 시간"
    )
    error_message = Column(
        Text,
        nullable=True,
        comment="작업 실패 시 에러 메시지"
    )
    width = Column(
        Integer,
        nullable=True,
        comment="이미지 너비 (픽셀)"
    )
    height = Column(
        Integer,
        nullable=True,
        comment="이미지 높이 (픽셀)"
    )
    embedding_kure = Column(
        Vector(1024),
        nullable=True,
        comment="Koure AI 임베딩 벡터 (1024차원)"
    )
    search_document = Column(
        Text,
        nullable=True,
        comment="검색을 위한 문서화된 텍스트 (Vision LLM 생성 결과)"
    )

