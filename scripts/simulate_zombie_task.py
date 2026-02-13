import asyncio
import uuid
import sys
import os

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.infrastructure.models import Asset, JobStatus, AssetTypeDB

# Adjust DB URL: Use env var if available (for container), else localhost (for host)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5434/platform")

async def create_zombie_task():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        job_id = str(uuid.uuid4())
        print(f"Creating Zombie Task with Job ID: {job_id}")
        
        new_asset = Asset(
            job_id=job_id,
            status=JobStatus.PROCESSING,
            asset_type=AssetTypeDB.IMAGE,
            prompt="Zombie Task Test Prompt",
            model="test-model",
            file_path=None
        )
        
        session.add(new_asset)
        await session.commit()
        print(f"✅ Successfully inserted task {job_id} with status PROCESSING")
        
    await engine.dispose()
    return job_id

if __name__ == "__main__":
    asyncio.run(create_zombie_task())
