import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.models import Asset, JobStatus, AssetTypeDB
from app.main import app

@pytest.mark.asyncio
async def test_cursor_pagination(
    async_test_client: AsyncClient, 
    test_db_session: AsyncSession
):
    """
    커서 기반 페이지네이션 테스트.
    1. 10개의 더미 에셋 생성 (ID 1~10 가정, 실제로는 Auto Increment)
    2. 첫 페이지 조회 (limit=3) -> ID 10, 9, 8 기대 (최신순)
    3. 커서(ID 8)를 이용해 두 번째 페이지 조회 -> ID 7, 6, 5 기대
    """
    
    # 1. Setup: 10개의 에셋 생성
    created_assets = []
    for i in range(10):
        asset = Asset(
            job_id=f"job_{i}",
            prompt=f"prompt_{i}",
            model="test-model",
            asset_type=AssetTypeDB.IMAGE,
            status=JobStatus.COMPLETED,
            width=1024,
            height=1024
        )
        test_db_session.add(asset)
        created_assets.append(asset)
    
    await test_db_session.commit()
    # ID 역순 정렬을 위해 최신 데이터가 가장 큰 ID를 가짐
    # (주의: 병렬 테스트 시 ID가 불연속적일 수 있으나 대소 관계는 유지됨)
    
    # 2. 첫 페이지 조회 (Limit 3)
    response = await async_test_client.get("/api/assets?limit=3")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) == 3
    # ID 역순 정렬 확인
    assert data[0]["id"] > data[1]["id"] 
    assert data[1]["id"] > data[2]["id"]
    
    last_id = data[-1]["id"]
    
    # 3. 두 번째 페이지 조회 (Cursor = last_id)
    response_page_2 = await async_test_client.get(f"/api/assets?limit=3&cursor={last_id}")
    assert response_page_2.status_code == 200
    data_page_2 = response_page_2.json()
    
    assert len(data_page_2) == 3
    # 두 번째 페이지의 첫 번째 아이템은 이전 페이지의 마지막 아이템보다 ID가 작아야 함
    assert data_page_2[0]["id"] < last_id
    # 정렬 유지 확인
    assert data_page_2[0]["id"] > data_page_2[1]["id"]
    
    # 4. 빈 페이지 조회 (매우 작은 커서)
    very_small_cursor = 0
    response_empty = await async_test_client.get(f"/api/assets?limit=3&cursor={very_small_cursor}")
    assert response_empty.status_code == 200
    assert len(response_empty.json()) == 0
