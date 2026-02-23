import pytest
import numpy as np
from app.ml.model import EmbeddingModel, embedding_model

def test_singleton_pattern():
    """EmbeddingModel이 Singleton으로 동작하는지 확인"""
    model1 = EmbeddingModel()
    model2 = EmbeddingModel()
    assert model1 is model2
    assert model1 is embedding_model

def test_model_warmup():
    """Warm-up이 예외 없이 실행되는지 확인"""
    try:
        embedding_model.warmup()
    except Exception as e:
        pytest.fail(f"Warm-up failed: {e}")

def test_encode_shape():
    """임베딩 벡터의 차원이 1024인지 확인"""
    text = "Hello, world!"
    vector = embedding_model.encode(text)
    
    # KURE-v1 output dimension: 1024
    assert vector.shape == (1, 1024)
    assert isinstance(vector, np.ndarray)
    assert vector.dtype == np.float32

def test_encode_normalization():
    """임베딩 벡터가 정규화(L2 Norm = 1.0) 되어 있는지 확인"""
    text = "Testing normalization"
    vector = embedding_model.encode(text)
    
    norm = np.linalg.norm(vector)
    assert np.isclose(norm, 1.0, atol=1e-5)

def test_batch_encode():
    """배치 처리 확인"""
    texts = ["First sentence", "Second sentence"]
    vectors = embedding_model.encode(texts)
    
    assert vectors.shape == (2, 1024)
    
    # 각 벡터가 정규화되어 있어야 함
    norm1 = np.linalg.norm(vectors[0])
    norm2 = np.linalg.norm(vectors[1])
    assert np.isclose(norm1, 1.0, atol=1e-5)
    assert np.isclose(norm2, 1.0, atol=1e-5)
