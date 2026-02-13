from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import select, update, func
from app.core.config import settings
from app.api import assets, system
from app.core.exceptions import DomainException
from app.infrastructure.database import async_session_maker
from app.infrastructure.models import Asset, JobStatus
import os
import logging
import traceback
from app.ml.model import embedding_model

# 로거 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 🚀 Startup Logic
    logger.info("🔄 System Startup: checking for unfinished tasks from previous run...")
    
    # 0. Model Warm-up (ONNX)
    try:
        embedding_model.warmup()
    except Exception as e:
        logger.error(f"❌ Model warm-up failed: {e}")

    try:
        async with async_session_maker() as session:
            # 1. 대상 조회 (PENDING or PROCESSING)
            stmt = select(Asset).where(
                Asset.status.in_([JobStatus.PENDING, JobStatus.PROCESSING])
            )
            result = await session.execute(stmt)
            zombies = result.scalars().all()
            
            if zombies:
                count = len(zombies)
                logger.warning(f"⚠️ Found {count} unfinished tasks. Marking them as FAILED.")
                
                # 2. 일괄 업데이트
                update_stmt = (
                    update(Asset)
                    .where(Asset.status.in_([JobStatus.PENDING, JobStatus.PROCESSING]))
                    .values(
                        status=JobStatus.FAILED,
                        error_message="System Restart: Task aborted during cleanup",
                        updated_at=func.now()
                    )
                )
                await session.execute(update_stmt)
                await session.commit()
                logger.info(f"✅ Successfully cleaned up {count} zombie tasks.")
            else:
                logger.info("✨ No unfinished tasks found. System is clean.")
                
    except Exception as e:
        logger.error(f"❌ Error during startup task cleanup: {e}")
        # 실패하더라도 서버 시작은 막지 않음 (로그만 남김)
    
    yield 
    
    # 👋 Shutdown Logic
    logger.info("🛑 System Shutdown")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI 멀티모달 콘텐츠 생성 플랫폼 - 이미지/비디오 생성",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 미들웨어 (프론트엔드 연동용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 환경용, 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(assets.router, prefix="/api/assets", tags=["assets"])
app.include_router(system.router, prefix="/api/system", tags=["system"])

# 정적 파일 서빙 (생성된 에셋 접근용)
storage_path = settings.STORAGE_PATH
if os.path.exists(storage_path):
    app.mount("/storage/assets", StaticFiles(directory=storage_path), name="storage")


# 중앙 집중식 에러 핸들링
@app.exception_handler(DomainException)
async def domain_exception_handler(request: Request, exc: DomainException):
    logger.warning(f"DomainException: {exc.message} (Path: {request.url.path})")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "data": None,
            "error": exc.message
        },
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTPException: {exc.detail} (Status: {exc.status_code}, Path: {request.url.path})")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "data": None,
            "error": exc.detail
        },
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_msg = f"Internal Server Error: {str(exc)}"
    logger.error(f"Global Exception: {error_msg} (Path: {request.url.path})")
    logger.error(traceback.format_exc())  # 전체 스택 트레이스 로깅
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "data": None,
            "error": error_msg
        },
    )


@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME} API"}

@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    return {"status": "healthy"}

