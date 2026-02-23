"""
Unit Test: Schema Validators

Pydantic 검증 로직 및 헬퍼 함수 테스트
- 입력값 검증 (타입, 길이 등)
- 모델 매핑 함수
- Edge Case 검증
"""
import pytest
from pydantic import ValidationError
from app.schemas.asset import (
    AssetCreate,
    GenerationMode,
    AssetType,
    get_asset_type_from_mode,
    get_model_from_mode,
)


pytestmark = pytest.mark.unit


class TestSchemaValidators:
    """Schema 검증 로직 테스트"""
    
    def test_asset_create_valid_data(self):
        """정상적인 데이터 검증"""
        # Given / When
        asset = AssetCreate(
            prompt="A beautiful landscape",
            mode=GenerationMode.TEXT_TO_IMAGE
        )
        
        # Then
        assert asset.prompt == "A beautiful landscape"
        assert asset.mode == GenerationMode.TEXT_TO_IMAGE
        assert asset.source_image is None
    
    def test_asset_create_empty_prompt(self):
        """빈 프롬프트 검증 실패"""
        # Given / When / Then
        with pytest.raises(ValidationError) as exc_info:
            AssetCreate(prompt="", mode=GenerationMode.TEXT_TO_IMAGE)
        
        errors = exc_info.value.errors()
        # Pydantic 버전에 따라 메시지가 다를 수 있으므로 핵심 키워드 위주로 검증
        assert any("at least 1" in str(e).lower() for e in errors)
    
    def test_asset_create_prompt_too_long(self):
        """프롬프트 길이 초과 검증"""
        # Given
        long_prompt = "A" * 1001  # max_length=1000
        
        # When / Then
        with pytest.raises(ValidationError) as exc_info:
            AssetCreate(prompt=long_prompt, mode=GenerationMode.TEXT_TO_IMAGE)
        
        errors = exc_info.value.errors()
        assert any("at most 1000" in str(e).lower() for e in errors)
    
    def test_asset_create_invalid_mode(self):
        """잘못된 모드 검증"""
        # Given / When / Then
        with pytest.raises(ValidationError):
            AssetCreate(prompt="test", mode="invalid-mode")
    
    def test_asset_create_with_source_image(self):
        """소스 이미지 포함 검증"""
        # Given / When
        asset = AssetCreate(
            prompt="Make it move",
            mode=GenerationMode.IMAGE_TO_VIDEO,
            source_image="base64encodedimage=="
        )
        
        # Then
        assert asset.source_image == "base64encodedimage=="
    
    def test_get_asset_type_from_mode_image(self):
        """GenerationMode → AssetType 변환 (이미지)"""
        # Given / When
        asset_type = get_asset_type_from_mode(GenerationMode.TEXT_TO_IMAGE)
        
        # Then
        assert asset_type == AssetType.IMAGE
    
    def test_get_asset_type_from_mode_video(self):
        """GenerationMode → AssetType 변환 (비디오)"""
        # Given / When
        result1 = get_asset_type_from_mode(GenerationMode.TEXT_TO_VIDEO)
        result2 = get_asset_type_from_mode(GenerationMode.IMAGE_TO_VIDEO)
        
        # Then
        assert result1 == AssetType.VIDEO
        assert result2 == AssetType.VIDEO
    
    def test_get_model_from_mode_image(self):
        """GenerationMode → Model 이름 매핑 (이미지)"""
        # Given / When
        model = get_model_from_mode(GenerationMode.TEXT_TO_IMAGE)
        
        # Then
        assert model == "imagen-3.0-fast-generate-001"
    
    def test_get_model_from_mode_text_to_video(self):
        """GenerationMode → Model 이름 매핑 (텍스트→비디오)"""
        # Given / When
        model = get_model_from_mode(GenerationMode.TEXT_TO_VIDEO)
        
        # Then
        assert model == "veo-3.0-fast-generate-001"
    
    def test_get_model_from_mode_image_to_video(self):
        """GenerationMode → Model 이름 매핑 (이미지→비디오)"""
        # Given / When
        model = get_model_from_mode(GenerationMode.IMAGE_TO_VIDEO)
        
        # Then
        assert model == "veo-3.0-fast-generate-001"
    
    def test_asset_create_default_mode(self):
        """기본 모드 검증"""
        # Given / When
        asset = AssetCreate(prompt="test prompt")
        
        # Then
        assert asset.mode == GenerationMode.TEXT_TO_IMAGE
