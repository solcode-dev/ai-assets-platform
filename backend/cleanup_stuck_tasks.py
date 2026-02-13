
import asyncio
import sys
import os

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from sqlalchemy import update, select
from app.infrastructure.database import async_session_maker
from app.infrastructure.models import Asset, JobStatus

async def cleanup_stuck_tasks():
    print("🧹 Cleaning up stuck PROCESSING tasks...")
    
    async with async_session_maker() as session:
        # Find stuck tasks (PENDING or PROCESSING)
        # 10분 이상 지났다면 확실한 좀비로 간주할 수 있음 (현재는 전체 조회)
        stmt = select(Asset).where(Asset.status.in_([JobStatus.PROCESSING, JobStatus.PENDING]))
        result = await session.execute(stmt)
        stuck_assets = result.scalars().all()
        
        if not stuck_assets:
            print("✅ No stuck tasks (PENDING/PROCESSING) found.")
            return

        print(f"⚠️ Found {len(stuck_assets)} active tasks:")
        for asset in stuck_assets:
            print(f"   - Job ID: {asset.job_id} | Status: {asset.status} | Created: {asset.created_at}")

        # Update confirmed stuck tasks
        update_stmt = (
            update(Asset)
            .where(Asset.status.in_([JobStatus.PROCESSING, JobStatus.PENDING]))
            .values(
                status=JobStatus.FAILED,
                error_message="System restart: Zombie task cleanup"
            )
        )
        
        await session.execute(update_stmt)
        await session.commit()
        
        print(f"✅ Successfully marked {len(stuck_assets)} tasks as FAILED.")

if __name__ == "__main__":
    try:
        asyncio.run(cleanup_stuck_tasks())
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
