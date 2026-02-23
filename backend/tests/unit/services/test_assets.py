"""
Unit Test: BaseAssetService

행위(Behavior) 검증 + 상태(Result) 검증을 모두 수행합니다.
- Mock 객체의 메서드 호출 여부 및 인자 확인
- 반환값 검증
- 예외 발생 시나리오 검증
"""
import pytest
from unittest.mock import patch, MagicMock
from app.services.assets import BaseAssetService
from app.schemas.asset import AssetCreate, GenerationMode, AssetType, JobStatus
from app.core.exceptions import ResourceNotFoundException


pytestmark = pytest.mark.unit


class TestBaseAssetService:
    """BaseAssetService Unit Test"""
    
    @pytest.mark.asyncio
    async def test_create_generation_job_success(
        self,
        mock_repository,
        mock_storage_provider,
        sample_asset_data
    ):
        """정상적인 작업 생성 및 UUID 반환 검증"""
        # Given
        service = BaseAssetService(mock_repository, mock_storage_provider)
        asset_in = AssetCreate(**sample_asset_data)
        mock_repository.create.return_value = 1
        
        # When
        with patch('app.services.assets.generate_asset_task') as mock_task:
            job_id = await service.create_generation_job(asset_in)
        
        # Then - 상태 검증
        assert isinstance(job_id, str)
        assert len(job_id) == 36  # UUID 포맷
        
        # Then - 행위 검증
        mock_repository.create.assert_called_once()
        call_args = mock_repository.create.call_args[1]
        assert call_args['job_id'] == job_id
        assert call_args['prompt'] == sample_asset_data['prompt']
        assert call_args['model'] == 'imagen-3.0-fast-generate-001'
        assert call_args['asset_type'] == AssetType.IMAGE.value
        
        # Celery Task 발행 검증
        mock_task.delay.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_generation_job_with_video_mode(
        self,
        mock_repository,
        mock_storage_provider
    ):
        """비디오 생성 모드 검증"""
        # Given
        service = BaseAssetService(mock_repository, mock_storage_provider)
        asset_in = AssetCreate(
            prompt="A flying car",
            mode=GenerationMode.TEXT_TO_VIDEO
        )
        mock_repository.create.return_value = 1
        
        # When
        with patch('app.services.assets.generate_asset_task'):
            _ = await service.create_generation_job(asset_in)
        
        # Then
        call_args = mock_repository.create.call_args[1]
        assert call_args['model'] == 'veo-3.0-fast-generate-001'
        assert call_args['asset_type'] == AssetType.VIDEO.value
    
    @pytest.mark.asyncio
    async def test_get_asset_by_id_found(self, mock_repository, mock_storage_provider):
        """에셋 조회 성공"""
        # Given
        service = BaseAssetService(mock_repository, mock_storage_provider)
        mock_asset = MagicMock()  # AsyncMock -> MagicMock 변경
        mock_asset.id = 1
        mock_asset.job_id = "test-job-id"
        mock_asset.status = JobStatus.COMPLETED
        mock_asset.file_path = "path/to/file.png"
        mock_asset.result_url = None
        mock_repository.get_by_id.return_value = mock_asset
        
        # When
        result = await service.get_asset_by_id(1)
        
        # Then
        assert result == mock_asset
        mock_repository.get_by_id.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_get_asset_by_id_not_found(
        self,
        mock_repository,
        mock_storage_provider
    ):
        """에셋 조회 실패 - ResourceNotFoundException 발생"""
        # Given
        service = BaseAssetService(mock_repository, mock_storage_provider)
        mock_repository.get_by_id.return_value = None
        
        # When / Then
        with pytest.raises(ResourceNotFoundException) as exc_info:
            await service.get_asset_by_id(999)
        
        assert "Asset with ID 999 not found" in str(exc_info.value.message)
        mock_repository.get_by_id.assert_called_once_with(999)
    
    @pytest.mark.asyncio
    async def test_get_asset_by_job_id_found(
        self,
        mock_repository,
        mock_storage_provider,
        sample_job_id
    ):
        """job_id로 에셋 조회 성공"""
        # Given
        service = BaseAssetService(mock_repository, mock_storage_provider)
        mock_asset = MagicMock()  # AsyncMock -> MagicMock 변경
        mock_asset.job_id = sample_job_id
        mock_asset.status = JobStatus.COMPLETED
        mock_asset.file_path = None
        mock_asset.result_url = None
        mock_repository.get_by_job_id.return_value = mock_asset
        
        # When
        result = await service.get_asset_by_job_id(sample_job_id)
        
        # Then
        assert result == mock_asset
        mock_repository.get_by_job_id.assert_called_once_with(sample_job_id)
    
    @pytest.mark.asyncio
    async def test_get_asset_by_job_id_not_found(
        self,
        mock_repository,
        mock_storage_provider
    ):
        """job_id로 에셋 조회 실패 - ResourceNotFoundException 발생"""
        # Given
        service = BaseAssetService(mock_repository, mock_storage_provider)
        mock_repository.get_by_job_id.return_value = None
        
        # When / Then
        with pytest.raises(ResourceNotFoundException) as exc_info:
            await service.get_asset_by_job_id("non-existent-job")
        
        assert "Asset with job_id non-existent-job not found" in str(exc_info.value.message)
    
    @pytest.mark.asyncio
    async def test_update_job_status(
        self,
        mock_repository,
        mock_storage_provider,
        sample_job_id
    ):
        """작업 상태 업데이트 검증"""
        # Given
        service = BaseAssetService(mock_repository, mock_storage_provider)
        
        # When
        await service.update_job_status(sample_job_id, JobStatus.COMPLETED, "path/to/file.png")
        
        # Then - 행위 검증
        mock_repository.update_status.assert_called_once_with(
            sample_job_id,
            JobStatus.COMPLETED.value,
            "path/to/file.png"
        )

    @pytest.mark.asyncio
    async def test_get_asset_with_result_url(self, mock_repository, mock_storage_provider):
        """result_url 생성 로직 검증"""
        # Given
        service = BaseAssetService(mock_repository, mock_storage_provider)
        mock_asset = MagicMock()  # AsyncMock -> MagicMock 변경
        mock_asset.id = 1
        mock_asset.job_id = "test-job-id"
        mock_asset.status = JobStatus.COMPLETED
        mock_asset.file_path = "/app/storage/assets/generated_image.png"
        mock_asset.result_url = None
        mock_repository.get_by_id.return_value = mock_asset
        
        # When
        result = await service.get_asset_by_id(1)
        
        # Then
        assert result.result_url == "http://localhost:8000/storage/assets/generated_image.png"

