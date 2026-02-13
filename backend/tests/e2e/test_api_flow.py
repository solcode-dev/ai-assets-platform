"""
E2E Test: API Flow (HTTPX 기반)

전체 API 엔드포인트 플로우 테스트
- 실제 HTTP 요청/응답 검증
- 에러 핸들링 검증
"""
import pytest
from unittest.mock import patch
from app.schemas.asset import JobStatus


pytestmark = pytest.mark.e2e


class TestAPIFlow:
    """API E2E Test (HTTPX)"""
    
    async def test_generate_asset_success(self, async_test_client):
        """에셋 생성 API 전체 플로우"""
        # Given
        payload = {
            "prompt": "A beautiful sunset",
            "mode": "text-to-image"
        }
        
        # When
        with patch('app.services.assets.generate_asset_task'):  # Celery Mock
            response = await async_test_client.post("/api/assets/generate", data=payload)
        
        # Then
        assert response.status_code == 200, f"Generate request failed: {response.text}"
        data = response.json()
        assert "job_id" in data
        assert data["status"] == JobStatus.PENDING.value
        assert len(data["job_id"]) == 36  # UUID
    
    async def test_generate_asset_validation_error(self, async_test_client):
        """잘못된 입력값 → 422 Validation Error"""
        # Given
        payload = {
            "prompt": "",  # 빈 프롬프트
            "mode": "text-to-image"
        }
        
        # When
        response = await async_test_client.post("/api/assets/generate", data=payload)
        
        # Then
        assert response.status_code == 422
    
    async def test_get_asset_by_id_not_found(self, async_test_client):
        """존재하지 않는 에셋 조회 → 404"""
        # When
        response = await async_test_client.get("/api/assets/99999")
        
        # Then
        assert response.status_code == 404
        data = response.json()
        assert not data["success"]
        assert "not found" in data["error"].lower()
    
    async def test_get_asset_by_job_id_success(self, async_test_client):
        """job_id로 에셋 조회 성공"""
        # Given - 먼저 에셋 생성
        create_payload = {
            "prompt": "Test asset for retrieval",
            "mode": "text-to-image"
        }
        
        with patch('app.services.assets.generate_asset_task'):
            create_response = await async_test_client.post("/api/assets/generate", data=create_payload)
            create_data = create_response.json()
            assert create_response.status_code == 200, f"Dependency generation failed: {create_data}"
            job_id = create_data["job_id"]
        
        # When - job_id로 조회
        response = await async_test_client.get(f"/api/assets/job/{job_id}")
        
        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == job_id
    
    async def test_domain_exception_handling(self, async_test_client):
        """전역 예외 핸들러 검증 (DomainException → JSON 응답)"""
        # Given
        # ResourceNotFoundException (404)
        response = await async_test_client.get("/api/assets/99999")
        
        # Then
        assert response.status_code == 404
        data = response.json()
        assert "success" in data
        assert "error" in data
        assert not data["success"]
