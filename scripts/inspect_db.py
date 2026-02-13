import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))

from app.infrastructure.database import async_session_maker
from app.infrastructure.models import Asset, JobStatus
from sqlalchemy import select

async def main():
    async with async_session_maker() as session:
        stmt = select(Asset).order_by(Asset.id.desc()).limit(10)
        result = await session.execute(stmt)
        assets = result.scalars().all()
        
        print(f"Recent Assets (Last 10):")
        for asset in assets:
            print(f"ID: {asset.id}, JobID: {asset.job_id}, Status: {asset.status}, Error: {asset.error_message}")

        # Check for any PROCESSING
        print("-" * 20)
        stmt = select(Asset).where(Asset.status == JobStatus.PROCESSING)
        result = await session.execute(stmt)
        processing = result.scalars().all()
        print(f"Currently PROCESSING: {len(processing)} tasks")
        for p in processing:
             print(f"STUCK: {p.job_id}, Created: {p.created_at}")

if __name__ == "__main__":
    asyncio.run(main())
