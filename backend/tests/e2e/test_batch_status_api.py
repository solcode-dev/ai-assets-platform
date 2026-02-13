"""
E2E Test: Batch Status API

배치 상태 조회 API의 전체 플로우 테스트
- 다중 Job ID 조회 검증
- 최대 100개 제한 검증
- 개별 조회 실패 핸들링 검증
"""
import pytest
from unittest.mock import patch


pytestmark = pytest.mark.e2e


class TestBatchStatusAPI:
    """Batch Status API E2E Test"""
    
    async def test_batch_status_success(self, async_test_client):
        """여러 Job ID의 상태를 한 번에 조회 성공"""
        # Given - 3개의 에셋 생성
        job_ids = []
        
        with patch('app.services.assets.generate_asset_task'):
            for i in range(3):
                payload = {
                    "prompt": f"Test asset {i}",
                    "mode": "text-to-image"
                }
                response = await async_test_client.post("/api/assets/generate", data=payload)
                assert response.status_code == 200
                job_ids.append(response.json()["job_id"])
        
        # When - 배치 상태 조회
        batch_request = {"task_ids": job_ids}
        response = await async_test_client.post("/api/assets/batch-status", json=batch_request)
        
        # Then
        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert len(data["tasks"]) == 3
        
        # 모든 job_id가 응답에 포함되어 있는지 검증
        response_job_ids = {task["job_id"] for task in data["tasks"]}
        assert response_job_ids == set(job_ids)
    
    async def test_batch_status_max_100_limit(self, async_test_client):
        """최대 100개 제한 검증 → 400 Error"""
        # Given - 101개의 Job ID
        job_ids = [f"job-{i}" for i in range(101)]
        batch_request = {"task_ids": job_ids}
        
        # When
        response = await async_test_client.post("/api/assets/batch-status", json=batch_request)
        
        # Then
        assert response.status_code == 400
        # FastAPI HTTPException은 detail만 포함하는 응답을 반환
        # (StandardResponse 형식이 아님)
    
    async def test_batch_status_empty_list(self, async_test_client):
        """빈 리스트 조회 → 빈 응답"""
        # Given
        batch_request = {"task_ids": []}
        
        # When
        response = await async_test_client.post("/api/assets/batch-status", json=batch_request)
        
        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["tasks"] == []
    
    async def test_batch_status_partial_failure(self, async_test_client):
        """일부 Job ID가 없어도 나머지는 정상 반환"""
        # Given - 1개의 실제 에셋 + 2개의 가짜 ID
        with patch('app.services.assets.generate_asset_task'):
            response = await async_test_client.post(
                "/api/assets/generate", 
                data={"prompt": "Real asset", "mode": "text-to-image"}
            )
            real_job_id = response.json()["job_id"]
        
        job_ids = [real_job_id, "fake-job-1", "fake-job-2"]
        batch_request = {"task_ids": job_ids}
        
        # When
        response = await async_test_client.post("/api/assets/batch-status", json=batch_request)
        
        # Then
        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) == 1  # 실제 존재하는 것만 반환
        assert data["tasks"][0]["job_id"] == real_job_id
    
    async def test_batch_status_performance(self, async_test_client):
        """50개 태스크 조회 시 500ms 이내 응답 (성능 목표)"""
        import time
        
        # Given - 50개의 에셋 생성
        job_ids = []
        with patch('app.services.assets.generate_asset_task'):
            for i in range(50):
                response = await async_test_client.post(
                    "/api/assets/generate",
                    data={"prompt": f"Asset {i}", "mode": "text-to-image"}
                )
                job_ids.append(response.json()["job_id"])
        
        # When
        start_time = time.time()
        batch_request = {"task_ids": job_ids}
        response = await async_test_client.post("/api/assets/batch-status", json=batch_request)
        elapsed = time.time() - start_time
        
        # Then
        assert response.status_code == 200
        assert elapsed < 0.5, f"Response time {elapsed:.3f}s exceeds 500ms target"
        assert len(response.json()["tasks"]) == 50
    
    async def test_batch_status_duplicate_ids(self, async_test_client):
        """중복된 Job ID가 있어도 한 번만 조회 (DB 쿼리 최적화)"""
        # Given - 1개의 실제 에셋 생성
        with patch('app.services.assets.generate_asset_task'):
            response = await async_test_client.post(
                "/api/assets/generate",
                data={"prompt": "Single asset", "mode": "text-to-image"}
            )
            job_id = response.json()["job_id"]
        
        # When - 같은 ID를 3번 요청
        batch_request = {"task_ids": [job_id, job_id, job_id]}
        response = await async_test_client.post("/api/assets/batch-status", json=batch_request)
        
        # Then - 응답에는 1개만 포함되어야 함
        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["job_id"] == job_id
    
    async def test_batch_status_preserves_client_order(self, async_test_client):
        """클라이언트가 보낸 순서대로 응답 반환 (SQL IN 절은 순서 무관)"""
        # Given - 3개의 에셋 생성
        job_ids = []
        with patch('app.services.assets.generate_asset_task'):
            for i in range(3):
                response = await async_test_client.post(
                    "/api/assets/generate",
                    data={"prompt": f"Asset {i}", "mode": "text-to-image"}
                )
                job_ids.append(response.json()["job_id"])
        
        # When - 역순으로 요청 (job_ids[2], job_ids[1], job_ids[0])
        reversed_ids = list(reversed(job_ids))
        batch_request = {"task_ids": reversed_ids}
        response = await async_test_client.post("/api/assets/batch-status", json=batch_request)
        
        # Then - 응답도 역순으로 반환되어야 함
        assert response.status_code == 200
        data = response.json()
        response_ids = [task["job_id"] for task in data["tasks"]]
        assert response_ids == reversed_ids, "Response order must match client request order"
