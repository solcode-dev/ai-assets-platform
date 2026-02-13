import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Multimodal Platform"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/platform"
    
    # Redis & Celery
    REDIS_URL: str = "redis://redis:6379/0"
    MAX_TASK_RETRIES: int = 1
    
    # Storage
    STORAGE_TYPE: str = "local"  # "local" or "s3"
    STORAGE_PATH: str = "/app/storage/assets"
    
    @property
    def STORAGE_BASE(self) -> Path:
        """스토리지 기본 경로를 Path 객체로 반환"""
        return Path(self.STORAGE_PATH)
    
    # AWS S3 (Optional if STORAGE_TYPE=local)
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_S3_BUCKET_NAME: str = "ai-platform-assets"
    AWS_REGION: str = "ap-northeast-2"
    
    # Google Cloud Platform / Vertex AI
    GCP_PROJECT_ID: str = ""
    GCP_REGION: str = "us-central1"
    GCP_ACCESS_TOKEN: str = ""  # 72시간 후 만료되는 인증 키 (Optional)
    
    # AI Client (테스트 환경용)
    USE_MOCK_AI: bool = False  # True로 설정하면 MockAIClient 사용

    # 환경 설정
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.test") if os.getenv("APP_ENV") == "test" else ".env",
        env_file_encoding='utf-8',
        extra='ignore'
    )

settings = Settings()
