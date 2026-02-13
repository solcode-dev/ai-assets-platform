import os
import pytest
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from httpx import AsyncClient
from fastapi.testclient import TestClient
from alembic import command
from alembic.config import Config

# ============================================================================
# Environment Config (pytest 전역 설정)
# ============================================================================
def pytest_configure(config):
    """pytest 시작 시 환경 변수 강제 주입"""
    os.environ["APP_ENV"] = "test"

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment(monkeypatch_session):
    """테스트 환경 초기화 및 Alembic 마이그레이션 실행"""
    # 1. 환경 변수 복구 보장을 위해 monkeypatch 사용
    monkeypatch_session.setenv("APP_ENV", "test")
    
    # 2. 지연 임포트: 환경 변수가 설정된 후 설정을 로드해야 함
    from app.core.config import settings
    
    # DATABASE_URL 검증 (운영 DB 오염 방지)
    if not any(keyword in settings.DATABASE_URL for keyword in ["localhost", "127.0.0.1", "test_db", "platform"]):
        pytest.exit(f"🛑 CRITICAL: Invalid test database URL: {settings.DATABASE_URL}. "
                    "Tests must run against a local or dedicated test database.")

    # Storage 디렉토리 준비
    os.makedirs(settings.STORAGE_PATH, exist_ok=True)
    
    # 3. Alembic upgrade head 실행
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    alembic_cfg_path = os.path.join(backend_dir, "alembic.ini")
    
    if not os.path.exists(alembic_cfg_path):
        pytest.exit(f"🛑 CRITICAL: alembic.ini not found at {alembic_cfg_path}")
        
    alembic_cfg = Config(alembic_cfg_path)
    
    # 테스트 세션 시작 시 한 번만 스키마를 최신화
    command.upgrade(alembic_cfg, "head")
    
    yield settings

@pytest.fixture(scope="session")
def monkeypatch_session():
    """세션 스코프를 지원하는 monkeypatch fixture"""
    from _pytest.monkeypatch import MonkeyPatch
    m = MonkeyPatch()
    yield m
    m.undo()

# ============================================================================
# Core Fixtures
# ============================================================================
@pytest.fixture(scope="session")
def app_instance():
    """FastAPI 앱 인스턴스 (지연 임포트)"""
    from app.main import app
    return app

# ============================================================================
# Unit Test Fixtures (Mock 객체)
# ============================================================================
@pytest.fixture
def mock_repository() -> AsyncMock:
    """AssetRepository Mock"""
    from app.domain.interfaces import AssetRepository
    mock = AsyncMock(spec=AssetRepository)
    mock.create.return_value = 1
    mock.get_by_id.return_value = None
    mock.get_by_job_id.return_value = None
    mock.update_status.return_value = None
    return mock

@pytest.fixture
def mock_storage_provider() -> MagicMock:
    """StorageProvider Mock"""
    from app.domain.interfaces import StorageProvider
    mock = MagicMock(spec=StorageProvider)
    mock.save_file.return_value = "storage/test.png"
    mock.get_file_url.return_value = "http://localhost/storage/test.png"
    return mock

@pytest.fixture
def mock_ai_client() -> AsyncMock:
    """AIGenerationClient Mock"""
    from app.domain.interfaces import AIGenerationClient
    mock = AsyncMock(spec=AIGenerationClient)
    mock.generate_image.return_value = b"fake_image_data"
    mock.generate_video_from_text.return_value = b"fake_video_data"
    mock.generate_video_from_image.return_value = b"fake_video_data"
    return mock

# ============================================================================
# Integration Test Fixtures (실제 DB)
# ============================================================================
@pytest.fixture(scope="session")
async def test_db_engine():
    """테스트 DB 엔진 생성 (NullPool로 이벤트 루프 충돌 방지)"""
    from app.core.config import settings
    
    # NullPool: 커넥션을 풀링하지 않고 매번 새로 생성/소멸
    # 이로써 이벤트 루프 불일치 문제를 근본적으로 해결
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        future=True,
        poolclass=NullPool,
    )
    
    yield engine
    await engine.dispose()

@pytest.fixture
async def test_db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """테스트 DB 세션 (매 테스트 후 데이터 클린업 - 정밀 제어 버전)"""
    from app.infrastructure.models import Base
    
    async_session = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False # 의도치 않은 flush로 인한 InterfaceError 방지
    )
    
    async with async_session() as session:
        yield session
        
        try:
            await session.rollback() # 진행 중인 트랜잭션 종료
            # 삭제 순서: 자식 테이블 -> 부모 테이블 (reversed 사용)
            for table in reversed(Base.metadata.sorted_tables):
                await session.execute(table.delete())
            await session.commit()
        except Exception as e:
            await session.rollback()
            print(f"⚠️ Cleanup failed: {e}")
        finally:
            await session.close()

# ============================================================================
# E2E Test Fixtures
# ============================================================================
@pytest.fixture
def test_client(app_instance, test_db_session) -> TestClient:
    """FastAPI TestClient (Dependency Override 적용)"""
    from app.infrastructure.database import get_db
    
    # 테스트 세션을 앱에 주입
    app_instance.dependency_overrides[get_db] = lambda: test_db_session
    yield TestClient(app_instance)
    app_instance.dependency_overrides.clear()

@pytest.fixture
async def async_test_client(app_instance, test_db_session) -> AsyncGenerator[AsyncClient, None]:
    """FastAPI AsyncClient (Dependency Override 적용 - 고성능/안정성 특화)"""
    from app.infrastructure.database import get_db
    
    # 팩토리 함수를 넘겨서 앱이 직접 세션 수명주기를 제어하게 함
    async def _get_db_override():
        yield test_db_session

    app_instance.dependency_overrides[get_db] = _get_db_override
    async with AsyncClient(app=app_instance, base_url="http://testserver") as client:
        yield client
    app_instance.dependency_overrides.clear()

# ============================================================================
# 공통 테스트 데이터
# ============================================================================
@pytest.fixture
def sample_asset_data():
    return {
        "prompt": "A beautiful sunset over the ocean",
        "mode": "text-to-image",
        "source_image": None
    }

@pytest.fixture
def sample_job_id():
    return "test-job-12345"
