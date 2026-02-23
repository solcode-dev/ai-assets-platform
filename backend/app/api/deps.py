from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database import get_db
from app.infrastructure.repositories import SQLAlchemyAssetRepository
from app.infrastructure.storage import get_storage_provider
from app.services.assets import BaseAssetService
from app.domain.interfaces import AssetService

async def get_asset_service(
    db: AsyncSession = Depends(get_db)
) -> AssetService:
    """ 
    AssetService 인터페이스를 구현한 구체 클래스를 주입합니다. 
    """
    repository = SQLAlchemyAssetRepository(db)
    storage_provider = get_storage_provider()
    return BaseAssetService(repository, storage_provider)
