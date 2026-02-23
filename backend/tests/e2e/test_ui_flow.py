"""
E2E Test: Playwright UI Flow (선택적)

Playwright를 사용한 브라우저 자동화 테스트
실제 프런트엔드가 있을 경우 사용
"""
import pytest
from playwright.async_api import async_playwright


pytestmark = pytest.mark.e2e


class TestUIFlow:
    """Playwright 기반 UI E2E Test (활성화)"""
    
    @pytest.mark.asyncio
    async def test_generate_image_flow(self):
        """이미지 생성 및 결과 확인 플로우"""
        async with async_playwright() as p:
            # Given - 브라우저 실행 (Mac ARM 안정성을 위해 webkit 사용)
            browser = await p.webkit.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # When - 메인 페이지 접속 (GenerationContainer가 있는 곳)
                await page.goto("http://localhost:3000")
                
                # 프롬프트 입력
                prompt_text = "A beautiful sunset over a calm ocean"
                textarea = page.locator('textarea')
                await textarea.wait_for(state="visible", timeout=10000)
                await textarea.fill(prompt_text)
                
                # 생성 버튼 클릭 (Generate 버튼이 활성화될 때까지 대기 후 클릭)
                # exact=True를 사용하여 'Regenerate'와 혼동 방지
                generate_button = page.get_by_role("button", name="Generate", exact=True)
                await generate_button.wait_for(state="visible", timeout=10000)
                
                # Playwright의 click()은 자동으로 버튼이 enabled 될 때까지 대기합니다.
                await generate_button.click()
                
                # 로딩 상태 확인 ("Generating..." 텍스트 감지)
                await page.wait_for_selector('text=Generating...', timeout=10000)
                
                # Then - 결과 이미지 렌더링 확인 (최대 60초 대기)
                await page.wait_for_selector('img[alt*="Generated"]', timeout=60000)
                
                # 재생성 버튼 존재 확인
                assert await page.get_by_role("button", name="Generate New").is_visible()
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_validation_error_ui(self):
        """UI에서 유효성 검사 버튼 비활성화 확인"""
        async with async_playwright() as p:
            browser = await p.webkit.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # Given
                await page.goto("http://localhost:3000")
                
                # When - 빈 프롬프트 확인
                generate_button = await page.query_selector('button:has-text("Generate")')
                
                # Then - 버튼이 비활성화(disabled) 상태여야 함 (프롬프트가 비어있으므로)
                is_disabled = await generate_button.is_disabled()
                assert is_disabled is True
                
            finally:
                await browser.close()
