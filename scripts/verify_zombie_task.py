import asyncio
import sys
import os
from sqlalchemy import select

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.infrastructure.models import Asset, JobStatus

# Adjust DB URL: Use env var if available (for container), else localhost (for host)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5434/platform")

async def verify_zombie_task(job_id):
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        print(f"Verifying task {job_id}...")
        result = await session.execute(select(Asset).where(Asset.job_id == job_id))
        task = result.scalar_one_or_none()
        
        if not task:
            print("❌ Task not found!")
            return
            
        print(f"Current Status: {task.status}")
        print(f"Error Message: {task.error_message}")
        
        if task.status == JobStatus.FAILED and "System Restart" in (task.error_message or ""):
            print("✅ TEST PASSED: Task is FAILED and has correct error message.")
        else:
            print("❌ TEST FAILED: Status or error message is incorrect.")

    await engine.dispose()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python verify_zombie_task.py <job_id>")
        sys.exit(1)
        
    job_id = sys.argv[1]
    asyncio.run(verify_zombie_task(job_id))
