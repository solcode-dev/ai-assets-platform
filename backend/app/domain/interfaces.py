from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.schemas.asset import AssetCreate, AssetResponse

class StorageProvider(ABC):
    """파일 저장소 인터페이스 (Local/S3 전환 가능)"""
    
    @abstractmethod
    async def save_file(self, content: bytes, filename: str) -> str:
        """파일을 저장하고 접근 경로를 반환합니다."""
        pass
    
    @abstractmethod
    async def get_file_url(self, filename: str) -> str:
        """파일의 접근 URL을 반환합니다."""
        pass

class AssetRepository(ABC):
    """에셋 저장소 인터페이스 (DB 계층 DIP)"""
    
    @abstractmethod
    async def create(self, job_id: str, prompt: str, model: str, asset_type: str) -> int:
        """새 에셋을 생성하고 ID를 반환합니다."""
        pass

    @abstractmethod
    async def get_by_params(self, prompt: str, model: str, asset_type: str) -> Optional[Any]:
        """프롬프트, 모델, 타입이 일치하는 최신 에셋을 조회합니다."""
        pass
    
    @abstractmethod
    async def get_by_id(self, asset_id: int):
        """ID로 에셋을 조회합니다."""
        pass
    
    @abstractmethod
    async def get_by_job_id(self, job_id: str):
        """job_id로 에셋을 조회합니다."""
        pass
    
    @abstractmethod
    async def update_status(self, job_id: str, status: str, file_path: Optional[str] = None, width: Optional[int] = None, height: Optional[int] = None, error_msg: Optional[str] = None) -> None:
        """작업 상태를 업데이트합니다. (너비/높이/에러메시지 포함)"""
        pass

    @abstractmethod
    async def update_metadata(self, asset_id: int, search_document: Optional[str] = None, embedding_kure: Optional[list[float]] = None) -> None:
        """에셋의 메타데이터(검색 문서, 임베딩)를 업데이트합니다."""
        pass

    @abstractmethod
    async def get_all(self, cursor: Optional[int] = None, limit: int = 100) -> list["AssetResponse"]:
        """모든 에셋을 최신순(ID 역순)으로 조회합니다. 커서 기반 페이지네이션."""
        pass
    
    @abstractmethod
    async def search_by_vector(self, vector: list[float], limit: int = 20) -> list[tuple[Any, float]]:
        """벡터 유사도 기반 에셋 검색을 수행합니다. (Asset, Score) 튜플 리스트 반환."""
        pass

    @abstractmethod
    async def search_hybrid(self, query: str, vector: list[float], limit: int = 20) -> list[tuple[Any, float]]:
        """키워드(FTS)와 벡터 검색을 결합한 하이브리드 검색을 수행합니다."""
        pass

class AIGenerationClient(ABC):
    """AI 생성 클라이언트 인터페이스 (Vertex AI 전환/Mock 가능)"""
    
    # 참고 : https://docs.cloud.google.com/vertex-ai/generative-ai/docs/model-reference/veo-video-generation?hl=ko
    
    @abstractmethod
    async def generate_image(self, prompt: str) -> bytes:
        """텍스트로 이미지를 생성합니다."""
        pass
    
    @abstractmethod
    async def generate_video_from_text(self, prompt: str) -> bytes:
        """텍스트로 비디오를 생성합니다."""
        pass
    
    @abstractmethod
    async def generate_video_from_image(self, prompt: str, image_bytes: bytes, source_image_mime_type: Optional[str]) -> bytes:
        """이미지와 텍스트로 비디오를 생성합니다."""
        pass

    @abstractmethod
    async def generate_description(self, image_bytes: bytes, mime_type: str) -> str:
        """이미지/비디오 프레임을 분석하여 텍스트 설명을 생성합니다 (Vision LLM)."""
        pass

class AssetService(ABC):
    """에셋 및 생성 작업을 관리하는 서비스 인터페이스 (DIP)"""

    @abstractmethod
    async def create_generation_job(self, asset_in: "AssetCreate") -> tuple[str, str]:
        """새로운 생성 작업을 만들고 (job_id, status)를 반환합니다."""
        pass

    @abstractmethod
    async def get_asset_by_id(self, asset_id: int) -> Optional["AssetResponse"]:
        """ID로 에셋 정보를 조회합니다."""
        pass

    @abstractmethod
    async def get_asset_by_job_id(self, job_id: str) -> Optional["AssetResponse"]:
        """job_id로 에셋 정보를 조회합니다."""
        pass

    @abstractmethod
    async def update_job_status(self, job_id: str, status: str, file_path: Optional[str] = None) -> None:
        """작업 상태를 업데이트합니다."""
        pass

    @abstractmethod
    async def get_assets(self, cursor: Optional[int] = None, limit: int = 100) -> list["AssetResponse"]:
        """에셋 목록을 조회합니다."""
        pass

    @abstractmethod
    async def search_assets(self, query: str, limit: int = 20, hybrid: bool = True) -> list["AssetResponse"]:
        """자연어 및 키워드 쿼리를 기반으로 에셋을 검색합니다. 하이브리드 모드 지원."""
        pass
