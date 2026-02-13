from enum import Enum

class AIVideoModelVeo(str, Enum):
    """Veo API 지원되는 모델"""
    VEO_2_0_GENERATE_001 = "veo-2.0-generate-001"
    VEO_2_0_GENERATE_EXP = "veo-2.0-generate-exp"
    VEO_2_0_GENERATE_PREVIEW = "veo-2.0-generate-preview"
    VEO_3_0_GENERATE_001 = "veo-3.0-generate-001"
    VEO_3_0_FAST_GENERATE_001 = "veo-3.0-fast-generate-001"
    VEO_3_1_GENERATE_001 = "veo-3.1-generate-001"
    VEO_3_1_FAST_GENERATE_001 = "veo-3.1-fast-generate-001"
    VEO_3_1_GENERATE_PREVIEW = "veo-3.1-generate-preview"


class AIImageModelImageGen(str, Enum):
    """ImageGen API 지원되는 모델"""
    IMAGEN_3_0_GENERATE_002 = "imagen-3.0-generate-002"
    IMAGEN_3_0_GENERATE_001 = "imagen-3.0-generate-001"
    IMAGEN_3_0_FAST_GENERATE_001 = "imagen-3.0-fast-generate-001"
    IMAGEN_3_0_CAPABILITY_001 = "imagen-3.0-capability-001"
    IMAGEN_4_0_GENERATE_001 = "imagen-4.0-generate-001"
    IMAGEN_4_0_FAST_GENERATE_001 = "imagen-4.0-fast-generate-001"
    IMAGEN_4_0_ULTRA_GENERATE_001 = "imagen-4.0-ultra-generate-001"

