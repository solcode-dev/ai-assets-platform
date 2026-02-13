from typing import Optional
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import logging
from app.domain.interfaces import AssetRepository
from app.infrastructure.models import Asset, JobStatus, AssetTypeDB
from app.core.exceptions import DomainException

logger = logging.getLogger(__name__)

class SQLAlchemyAssetRepository(AssetRepository):
    """SQLAlchemy 기반 AssetRepository 구현체"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, job_id: str, prompt: str, model: str, asset_type: str) -> int:
        """새 에셋을 생성하고 ID를 반환합니다."""
        try:
            asset = Asset(
                job_id=job_id,
                prompt=prompt,
                model=model,
                asset_type=AssetTypeDB(asset_type),
                status=JobStatus.PENDING
            )
            self.session.add(asset)
            await self.session.flush() # ID 생성을 위해 먼저 flush
            await self.session.commit()
            await self.session.refresh(asset)
            return asset.id
            
        except IntegrityError as e:
            await self.session.rollback()
            logger.exception(f"Duplicate job_id or integrity violation: {job_id}")
            raise DomainException(
                f"Asset with job_id {job_id} already exists", 
                status_code=409
            ) from e
            
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.exception(f"Database error creating asset for job {job_id}")
            raise DomainException(
                "Failed to create asset due to database error",
                status_code=500
            ) from e
    
    async def get_by_params(self, prompt: str, model: str, asset_type: str) -> Optional[Asset]:
        """프롬프트, 모델, 타입이 일치하는 최신 에셋을 조회합니다."""
        try:
            # FAILED 상태가 아닌 최신 에셋 조회
            stmt = select(Asset).where(
                Asset.prompt == prompt,
                Asset.model == model,
                Asset.asset_type == AssetTypeDB(asset_type),
                Asset.status != JobStatus.FAILED
            ).order_by(Asset.id.desc()).limit(1)
            
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
            
        except SQLAlchemyError:
            logger.exception(f"Database error fetching asset by params: {prompt[:20]}...")
            # 조회 실패는 치명적이지 않으므로 None 반환 (새로 생성하도록 유도)
            return None

    async def get_by_id(self, asset_id: int) -> Optional[Asset]:
        """ID로 에셋을 조회합니다."""
        try:
            result = await self.session.execute(
                select(Asset).where(Asset.id == asset_id)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.exception(f"Database error fetching asset {asset_id}")
            raise DomainException(
                "Failed to fetch asset due to database error",
                status_code=500
            ) from e
    
    async def get_by_job_id(self, job_id: str) -> Optional[Asset]:
        """job_id로 에셋을 조회합니다."""
        try:
            result = await self.session.execute(
                select(Asset).where(Asset.job_id == job_id)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.exception(f"Database error fetching job {job_id}")
            raise DomainException(
                "Failed to fetch asset due to database error",
                status_code=500
            ) from e
    
    async def get_by_job_ids(self, job_ids: list[str]) -> list[Asset]:
        """여러 job_id로 에셋을 일괄 조회합니다."""
        try:
            result = await self.session.execute(
                select(Asset).where(Asset.job_id.in_(job_ids))
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.exception(f"Database error fetching jobs: {job_ids[:5]}...")
            raise DomainException(
                "Failed to fetch assets due to database error",
                status_code=500
            ) from e
    
    async def update_status(
        self, 
        job_id: str, 
        status: str, 
        file_path: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        error_msg: Optional[str] = None
    ) -> None:
        """작업 상태 및 정보를 업데이트합니다."""
        try:
            stmt = update(Asset).where(Asset.job_id == job_id).values(
                status=JobStatus(status)
            )
            if file_path is not None:
                stmt = stmt.values(file_path=file_path)
            if width is not None:
                stmt = stmt.values(width=width)
            if height is not None:
                stmt = stmt.values(height=height)
            if error_msg is not None:
                stmt = stmt.values(error_message=error_msg)
            
            logger.debug(f"[HAWKEYE:REPO] Executing update_status for {job_id}: status={status}")
            await self.session.execute(stmt)
            await self.session.commit()
            logger.info(f"[HAWKEYE:REPO] Status update committed for {job_id}: {status}")
            
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.exception(f"Database error updating status for job {job_id}")
            raise DomainException(
                "Failed to update asset status due to database error",
                status_code=500
            ) from e

    async def update_metadata(self, asset_id: int, search_document: Optional[str] = None, embedding_kure: Optional[list[float]] = None) -> None:
        """에셋의 메타데이터(검색 문서, 임베딩)를 업데이트합니다."""
        try:
            stmt = update(Asset).where(Asset.id == asset_id)
            values = {}
            if search_document is not None:
                values["search_document"] = search_document
            if embedding_kure is not None:
                values["embedding_kure"] = embedding_kure
            
            if not values:
                return

            stmt = stmt.values(**values)
            
            logger.debug(f"[HAWKEYE:REPO] Executing update_metadata for asset {asset_id}")
            await self.session.execute(stmt)
            await self.session.commit()
            logger.info(f"[HAWKEYE:REPO] Metadata updated for asset {asset_id}")
            
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.exception(f"Database error updating metadata for asset {asset_id}")
            raise DomainException(
                "Failed to update asset metadata due to database error",
                status_code=500
            ) from e

    async def get_all(self, cursor: Optional[int] = None, limit: int = 100) -> list[Asset]:
        """모든 에셋을 최신순(ID 역순)으로 조회합니다. (FAILED 상태 제외)"""
        try:
            # ID 역순 정렬 (최신순)
            # FAILED 상태인 에셋은 제외
            stmt = select(Asset).where(Asset.status != JobStatus.FAILED).order_by(Asset.id.desc()).limit(limit)
            
            # 커서(마지막으로 본 ID)가 있으면 그보다 작은 ID들만 조회
            if cursor is not None:
                stmt = stmt.where(Asset.id < cursor)
                
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.exception("Database error fetching all assets")
            raise DomainException(
                "Failed to fetch assets due to database error",
                status_code=500
            ) from e

    async def search_by_vector(self, vector: list[float], limit: int = 20) -> list[tuple[Asset, float]]:
        """벡터 유사도 기반 에셋 검색 (pgvector <=> 사용)"""
        try:
            # pgvector의 cosine_distance (<=>) 사용
            # distance가 0에 가까울수록 유사함. score = 1 - distance (cosine similarity)
            distance = Asset.embedding_kure.cosine_distance(vector)
            
            # 유사도가 높은 순(거리 짧은 순)으로 정렬
            stmt = select(
                Asset, 
                (1 - distance).label("score")
            ).where(
                Asset.embedding_kure.is_not(None)
            ).order_by(
                distance
            ).limit(limit)

            result = await self.session.execute(stmt)
            return result.all() # list of (Asset, score)
        except SQLAlchemyError as e:
            logger.exception("Database error during vector search")
            raise DomainException(
                "Failed to search assets due to database error",
                status_code=500
            ) from e
    async def search_hybrid(self, query: str, vector: list[float], limit: int = 20) -> list[tuple[Asset, float]]:
        """키워드(FTS)와 벡터 검색을 결합한 하이브리드 검색 (RRF 알고리즘)"""
        try:
            # RRF(Reciprocal Rank Fusion) 상수
            K = 60
            
            # 1. 벡터 검색 순위 (CTE)
            vector_dist = Asset.embedding_kure.cosine_distance(vector)
            vector_subq = (
                select(
                    Asset.id,
                    func.row_number().over(order_by=vector_dist).label("rank")
                )
                .where(Asset.embedding_kure.is_not(None))
                .limit(100)
                .cte("vector_matches")
            )
            
            # 2. 키워드 검색 순위 (CTE)
            # prompt와 search_document를 합쳐서 한국어 검색 수행 (simple 파서 사용)
            search_text = Asset.prompt + " " + func.coalesce(Asset.search_document, "")
            ts_vector = func.to_tsvector("simple", search_text)
            ts_query = func.websearch_to_tsquery("simple", query)
            
            keyword_subq = (
                select(
                    Asset.id,
                    func.row_number().over(order_by=func.ts_rank_cd(ts_vector, ts_query).desc()).label("rank")
                )
                .where(ts_vector.op("@@")(ts_query))
                .limit(100)
                .cte("keyword_matches")
            )
            
            # 3. RRF 점수 결합 및 최종 정렬
            # Score = 1/(rank_vector + K) + 1/(rank_keyword + K)
            score = (
                func.coalesce(1.0 / (vector_subq.c.rank + K), 0.0) +
                func.coalesce(1.0 / (keyword_subq.c.rank + K), 0.0)
            ).label("score")
            
            stmt = (
                select(Asset, score)
                .outerjoin(vector_subq, Asset.id == vector_subq.c.id)
                .outerjoin(keyword_subq, Asset.id == keyword_subq.c.id)
                .where((vector_subq.c.id.is_not(None)) | (keyword_subq.c.id.is_not(None)))
                .order_by(score.desc())
                .limit(limit)
            )
            
            result = await self.session.execute(stmt)
            return result.all() # list of (Asset, rrf_score)
            
        except SQLAlchemyError as e:
            logger.exception("Database error during hybrid search")
            raise DomainException(
                "Failed to perform hybrid search due to database error",
                status_code=500
            ) from e
