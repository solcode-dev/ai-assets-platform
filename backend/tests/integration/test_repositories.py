"""
Integration Test: Repository

실제 PostgreSQL DB를 사용한 Repository 테스트
- Mock 없이 실제 쿼리 검증
- 트랜잭션 롤백 확인
- 제약조건 검증
"""
import pytest
from app.infrastructure.repositories import SQLAlchemyAssetRepository
from app.infrastructure.models import JobStatus, AssetTypeDB
from app.core.exceptions import DomainException


pytestmark = pytest.mark.integration


class TestSQLAlchemyAssetRepository:
    """Repository Integration Test (실제 DB 사용)"""
    
    @pytest.mark.asyncio
    async def test_create_asset_success(self, test_db_session):
        """실제 DB에 에셋 생성 및 조회"""
        # Given
        repository = SQLAlchemyAssetRepository(test_db_session)
        job_id = "test-job-integration-001"
        
        # When
        asset_id = await repository.create(
            job_id=job_id,
            prompt="Integration test prompt",
            model="imagen-3.0-fast-generate-001",
            asset_type=AssetTypeDB.IMAGE.value
        )
        
        # Then
        assert isinstance(asset_id, int)
        assert asset_id > 0
        
        # 실제로 조회되는지 확인
        asset = await repository.get_by_id(asset_id)
        assert asset is not None
        assert asset.job_id == job_id
        assert asset.prompt == "Integration test prompt"
        assert asset.status == JobStatus.PENDING
    
    @pytest.mark.asyncio
    async def test_create_duplicate_job_id_raises_exception(self, test_db_session):
        """중복된 job_id 생성 시 DomainException 발생"""
        # Given
        repository = SQLAlchemyAssetRepository(test_db_session)
        job_id = "duplicate-job-id"
        
        # 첫 번째 생성
        await repository.create(
            job_id=job_id,
            prompt="First",
            model="test-model",
            asset_type=AssetTypeDB.IMAGE.value
        )
        
        # When / Then - 동일한 job_id로 재생성 시도
        with pytest.raises(DomainException) as exc_info:
            await repository.create(
                job_id=job_id,
                prompt="Second",
                model="test-model",
                asset_type=AssetTypeDB.IMAGE.value
            )
        
        assert "already exists" in str(exc_info.value.message)
        assert exc_info.value.status_code == 409
    
    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, test_db_session):
        """존재하지 않는 ID 조회 시 None 반환"""
        # Given
        repository = SQLAlchemyAssetRepository(test_db_session)
        
        # When
        asset = await repository.get_by_id(99999)
        
        # Then
        assert asset is None
    
    @pytest.mark.asyncio
    async def test_get_by_job_id_success(self, test_db_session):
        """job_id로 에셋 조회 성공"""
        # Given
        repository = SQLAlchemyAssetRepository(test_db_session)
        job_id = "find-by-job-id-test"
        
        await repository.create(
            job_id=job_id,
            prompt="Test",
            model="test-model",
            asset_type=AssetTypeDB.VIDEO.value
        )
        
        # When
        asset = await repository.get_by_job_id(job_id)
        
        # Then
        assert asset is not None
        assert asset.job_id == job_id
        assert asset.asset_type == AssetTypeDB.VIDEO
    
    @pytest.mark.asyncio
    async def test_update_status_success(self, test_db_session):
        """작업 상태 업데이트 검증"""
        # Given
        repository = SQLAlchemyAssetRepository(test_db_session)
        job_id = "update-status-test"
        
        await repository.create(
            job_id=job_id,
            prompt="Test",
            model="test-model",
            asset_type=AssetTypeDB.IMAGE.value
        )
        
        # When
        await repository.update_status(
            job_id=job_id,
            status=JobStatus.COMPLETED.value,
            file_path="storage/test.png"
        )
        
        # Then - 실제로 업데이트되었는지 확인
        asset = await repository.get_by_job_id(job_id)
        assert asset.status == JobStatus.COMPLETED
        assert asset.file_path == "storage/test.png"
    
    @pytest.mark.asyncio
    async def test_transaction_rollback(self, test_db_session):
        """트랜잭션 롤백 동작 확인"""
        # Given
        repository = SQLAlchemyAssetRepository(test_db_session)
        
        # When - 의도적으로 에러 발생 (중복 job_id)
        await repository.create(
            job_id="rollback-test",
            prompt="Test",
            model="test-model",
            asset_type=AssetTypeDB.IMAGE.value
        )
        
        try:
            await repository.create(
                job_id="rollback-test",  # 중복
                prompt="Test2",
                model="test-model",
                asset_type=AssetTypeDB.IMAGE.value
            )
        except DomainException:
            pass
        
        # Then - 첫 번째 데이터는 여전히 존재해야 함
        asset = await repository.get_by_job_id("rollback-test")
        assert asset is not None
        assert asset.prompt == "Test"
