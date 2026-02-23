"""
Unit Test: API Dependencies

의존성 주입 함수 테스트
"""
import pytest
from unittest.mock import AsyncMock, patch
from app.api.deps import get_asset_service
from app.services.assets import BaseAssetService


pytestmark = pytest.mark.unit


class TestAPIDependencies:
    """API 의존성 주입 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_asset_service_returns_base_asset_service(self):
        """get_asset_service가 BaseAssetService 인스턴스를 반환하는지 검증"""
        # Given
        mock_db = AsyncMock()
        
        # When
        with patch('app.api.deps.get_db', return_value=mock_db):
            with patch('app.api.deps.get_storage_provider') as mock_storage:
                service = await get_asset_service(mock_db)
        
        # Then
        assert isinstance(service, BaseAssetService)
    
    @pytest.mark.asyncio
    async def test_get_asset_service_injects_dependencies(self):
        """get_asset_service가 올바른 의존성을 주입하는지 검증"""
        # Given
        mock_db = AsyncMock()
        
        # When
        with patch('app.api.deps.get_db', return_value=mock_db):
            with patch('app.api.deps.get_storage_provider') as mock_storage:
                service = await get_asset_service(mock_db)
        
        # Then
        assert service.repository is not None
        assert service.storage_provider is not None
