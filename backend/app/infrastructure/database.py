from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
from app.core.config import settings

# PostgreSQL 비동기 드라이버 사용
DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
# PostgreSQL 동기 드라이버 사용 (비상 로그 전용)
SYNC_DATABASE_URL = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

# Default Engine (API 서버용 - 풀링 사용)
engine = create_async_engine(DATABASE_URL, echo=False)

# Worker Engine (Celery 워커용 - 비동기)
worker_engine = create_async_engine(DATABASE_URL, echo=False, poolclass=NullPool)

# Sync Worker Engine (최종 실패 기록용 - 동기)
from sqlalchemy import create_engine
sync_worker_engine = create_engine(SYNC_DATABASE_URL, echo=False, poolclass=NullPool)

async_session_maker = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

worker_session_maker = async_sessionmaker(
    worker_engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async def get_db() -> AsyncSession:
    """FastAPI 의존성 주입용 DB 세션 제공자"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
