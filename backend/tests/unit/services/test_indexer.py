import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.indexer import IndexerService
from app.domain.interfaces import AssetRepository, AIGenerationClient
from app.infrastructure.models import Asset

# Mock dependencies
@pytest.fixture
def mock_repo():
    return AsyncMock(spec=AssetRepository)

@pytest.fixture
def mock_ai_client():
    return AsyncMock(spec=AIGenerationClient)

@pytest.fixture
def service(mock_repo, mock_ai_client):
    return IndexerService(mock_repo, mock_ai_client)

@pytest.mark.asyncio
async def test_index_asset_success(service, mock_repo, mock_ai_client):
    # Given
    asset_id = 1
    asset = Asset(id=asset_id, file_path="/tmp/test.png")
    mock_repo.get_by_id.return_value = asset
    
    mock_ai_client.generate_description.return_value = "A beautiful scene"
    
    # Mock embedding model
    with patch("app.services.indexer.embedding_model") as mock_embedding_model:
        # 서비스 인스턴스가 생성된 후 patch가 일어나므로 명시적으로 mock을 할당해줍니다.
        service.embedding_model = mock_embedding_model
        
        # Mock encode to return a numpy-like object that has a [0].tolist() method chain
        mock_embedding_vector = MagicMock()
        mock_embedding_vector.tolist.return_value = [0.1] * 1024
        mock_embedding_model.encode.return_value = [mock_embedding_vector]
        
        # Mock asyncio.get_running_loop
        with patch("asyncio.get_running_loop") as mock_loop_factory:
            mock_loop = MagicMock()
            
            # run_in_executor should actually run the lambda to trigger encode()
            async def mock_run_in_executor(executor, func, *args):
                return func(*args)
            
            mock_loop.run_in_executor.side_effect = mock_run_in_executor
            mock_loop_factory.return_value = mock_loop

            # Mock aiofiles and os.path.getsize
            with patch("aiofiles.open", new_callable=MagicMock) as mock_open, \
                patch("os.path.getsize", return_value=1024), \
                patch("mimetypes.guess_type", return_value=("image/png", None)):
                
                mock_file = AsyncMock()
                mock_file.read.return_value = b"fake_image_bytes"
                mock_open.return_value.__aenter__.return_value = mock_file
                
                # When
                await service.index_asset(asset_id)
                
                # Then
                mock_repo.get_by_id.assert_awaited_with(asset_id)
                mock_ai_client.generate_description.assert_awaited_with(b"fake_image_bytes", "image/png")
                
                # Verify encode was called (because mock_run_in_executor ran the lambda)
                mock_embedding_model.encode.assert_called_with("A beautiful scene")
                
                mock_repo.update_metadata.assert_awaited_with(
                    asset_id=asset_id, 
                    search_document="A beautiful scene", 
                    embedding_kure=[0.1] * 1024
                )

@pytest.mark.asyncio
async def test_index_asset_not_found(service, mock_repo):
    # Given
    mock_repo.get_by_id.return_value = None
    
    # When/Then
    try:
        await service.index_asset(999)
    except Exception as e:
        assert "Asset not found" in str(e)
    else:
        pytest.fail("Should raise exception")

@pytest.mark.asyncio
async def test_index_asset_file_not_found(service, mock_repo):
    # Given
    asset = Asset(id=1, file_path="/tmp/missing.png")
    mock_repo.get_by_id.return_value = asset
    
    with patch("os.path.getsize", return_value=1024), \
        patch("aiofiles.open", side_effect=FileNotFoundError):
        # When
        await service.index_asset(1)
        
        # Then
        # Should catch exception and return without error (logged)
        mock_repo.update_metadata.assert_not_called()

@pytest.mark.asyncio
async def test_index_asset_idempotency(service, mock_repo, mock_ai_client):
    # Given
    asset_id = 1
    # search_document가 이미 존재함
    asset = Asset(id=asset_id, file_path="/tmp/test.png", search_document="Existing description")
    mock_repo.get_by_id.return_value = asset
    
    with patch("os.path.getsize", return_value=1024), \
        patch("mimetypes.guess_type", return_value=("image/png", None)), \
        patch("app.services.indexer.embedding_model") as mock_embedding_model, \
        patch("asyncio.get_running_loop") as mock_loop_factory, \
        patch("aiofiles.open", new_callable=MagicMock) as mock_open:
            
            # 명시적으로 mock 할당
            service.embedding_model = mock_embedding_model
            
            mock_loop = MagicMock()
            async def mock_run_in_executor(executor, func, *args):
                return func(*args)
            mock_loop.run_in_executor.side_effect = mock_run_in_executor
            mock_loop_factory.return_value = mock_loop

            mock_embedding_vector = MagicMock()
            mock_embedding_vector.tolist.return_value = [0.1] * 1024
            mock_embedding_model.encode.return_value = [mock_embedding_vector]

            mock_file = AsyncMock()
            mock_file.read.return_value = b"fake_image_bytes"
            mock_open.return_value.__aenter__.return_value = mock_file
            
            # When
            await service.index_asset(asset_id)
            
            # Then
            # 1. Vision API는 호출되지 않아야 함
            mock_ai_client.generate_description.assert_not_called()
            
            # 2. Embedding은 호출되어야 함 (search_document는 있지만 embedding_kure는 없으므로)
            mock_embedding_model.encode.assert_called_with("Existing description")
            
            # 3. DB 업데이트는 embedding_kure만 수행되어야 함 (search_document는 그대로)
            mock_repo.update_metadata.assert_awaited_with(
                asset_id=asset_id, 
                search_document="Existing description", 
                embedding_kure=[0.1] * 1024
            )

@pytest.mark.asyncio
async def test_index_asset_full_skip(service, mock_repo, mock_ai_client):
    # Given
    asset_id = 1
    # 모든 메타데이터가 존재함
    asset = Asset(
        id=asset_id, 
        file_path="/tmp/test.png", 
        search_document="Existing description", 
        embedding_kure=[0.1] * 1024
    )
    mock_repo.get_by_id.return_value = asset
    
    with patch("os.path.getsize", return_value=1024), \
        patch("mimetypes.guess_type", return_value=("image/png", None)), \
        patch("app.services.indexer.embedding_model") as mock_embedding_model:
            
            # When
            await service.index_asset(asset_id)
            
            # Then
            mock_ai_client.generate_description.assert_not_called()
            mock_embedding_model.encode.assert_not_called()
            mock_repo.update_metadata.assert_not_called()
