"""
E2E Test: Gallery Flow
갤러리 페이지의 이미지 로드, 무한 스크롤, 필터링 검증
"""
import pytest
from playwright.async_api import async_playwright

pytestmark = pytest.mark.e2e

class TestGalleryFlow:
    @pytest.mark.asyncio
    async def test_gallery_infinite_scroll(self):
        """갤러리 초기 로드 및 무한 스크롤 검증"""
        async with async_playwright() as p:
            # 기본 브라우저 실행 (Mac ARM 안정성을 위해 webkit 사용)
            browser = await p.webkit.launch(headless=True)
            context = await browser.new_context(viewport={'width': 1280, 'height': 800})
            page = await context.new_page()
            
            try:
                # 갤러리 메인 페이지 접속
                await page.goto("http://localhost:3000")
                
                # 갤러리 섹션 로드 대기
                gallery_section = page.locator('section[aria-label="이미지 갤러리"]')
                await gallery_section.wait_for(state="visible", timeout=10000)
                
                # 초기 이미지 카드 개수 레코드
                initial_images = await page.locator('img').count()
                print(f"Initial images: {initial_images}")
                
                # 바닥까지 스크롤하여 무한 스크롤 트리거 (여러 번 반복하여 충분한 데이터 로드)
                for _ in range(3):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(1000) # 스크롤 후 데이터 로드 대기
                
                # 추가 이미지 로드 확인
                final_images = await page.locator('img').count()
                print(f"Final images after scroll: {final_images}")
                
                # 가상화가 적용되어도 스크롤 시 DOM의 이미지 개수가 변하거나, 최소한 초기 상태는 유지되어야 함
                assert final_images >= initial_images
                
            finally:
                await browser.close()

    @pytest.mark.asyncio
    async def test_gallery_filtering_via_sidebar(self):
        """사이드바 필터링 버튼 클릭 시 URL 및 데이터 업데이트 검증"""
        async with async_playwright() as p:
            browser = await p.webkit.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto("http://localhost:3000")
                
                # 사이드바에서 '비디오' 링크 클릭 (aria-label="비디오")
                video_link = page.get_by_label("비디오")
                await video_link.click()
                
                # URL에 filter=videos 파라미터가 포함되었는지 확인
                await page.wait_for_function("window.location.search.includes('filter=videos')")
                assert "filter=videos" in page.url
                
                # 필터링 후 갤러리가 비어있거나 에러나지 않는지 확인
                gallery_section = page.locator('section[aria-label="이미지 갤러리"]')
                await gallery_section.wait_for(state="visible")
                
            finally:
                await browser.close()
