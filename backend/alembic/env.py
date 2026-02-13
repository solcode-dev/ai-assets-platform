import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context
import sys
import os

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.infrastructure.models import Base

# Alembic Config 객체
config = context.config

# 환경변수에서 DATABASE_URL 가져오기
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# 로깅 설정
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 메타데이터 (자동 마이그레이션 생성용)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """오프라인 모드로 마이그레이션 실행"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """실제 마이그레이션을 수행하는 동기 헬퍼 함수"""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()



async def run_migrations_online() -> None:
    """비동기 엔진을 사용하여 온라인 모드로 마이그레이션 실행"""
    connectable = create_async_engine(
        settings.DATABASE_URL,
        poolclass=pool.NullPool,
        future=True,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    # 비동기 실행을 위해 이벤트 루프 감지 및 실행
    asyncio.run(run_migrations_online())
