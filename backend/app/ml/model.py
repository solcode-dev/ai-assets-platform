import os
import time
import logging
from typing import List, Union
import numpy as np
from threading import Lock
from pathlib import Path

# optimum & onnxruntime은 설치 여부가 확인되었으므로 직접 임포트합니다.
from optimum.onnxruntime import ORTModelForFeatureExtraction
from optimum.exporters.onnx import main_export
from transformers import AutoTokenizer

# 로깅 설정 (라이브러리 로그는 숨기고 앱 로그만 표시)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app.ml.model")
logger.setLevel(logging.INFO)

class EmbeddingModel:
    _instance = None
    _lock = Lock()
    
    MODEL_ID = "nlpai-lab/KURE-v1"
    # Docker 볼륨 마운트 경로에 맞춰 설정
    CACHE_DIR = "/app/storage/model_cache"

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(EmbeddingModel, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        logger.info(f"🚀 임베딩 모델 초기화 시작 (Target: {self.MODEL_ID})")
        self.model = None
        self.tokenizer = None
        
        # 캐시 디렉토리 생성
        os.makedirs(self.CACHE_DIR, exist_ok=True)
        
        self._load_model()
        self._initialized = True

    def _load_model(self):
        try:
            start_time = time.time()
            logger.info("📦 토크나이저 로딩 중...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.MODEL_ID)
            
            # 모델 파일 경로 확인
            model_path = Path(self.CACHE_DIR) / "model.onnx"
            
            if not model_path.exists():
                logger.info(f"📦 ONNX 모델 변환 및 내보내기 시작 (경로: {self.CACHE_DIR})...")
                # optimum.exporters.onnx.main_export를 사용하여 직접 변환
                # export=True 옵션의 숨겨진 임시 파일 오류를 방지하기 위함
                main_export(
                    self.MODEL_ID,
                    output=Path(self.CACHE_DIR),
                    task="feature-extraction",
                    opset=17, # 안정적인 opset 버전 사용
                    do_validation=False
                )
                logger.info("📦 모델 변환 완료.")
            else:
                logger.info("📦 기존 캐시된 ONNX 모델을 로드합니다...")

            # 변환된 모델 로드 (export=False)
            self.model = ORTModelForFeatureExtraction.from_pretrained(
                self.CACHE_DIR,
                file_name="model.onnx",
                provider="CPUExecutionProvider" 
            )
            
            elapsed = time.time() - start_time
            logger.info(f"✅ 모델 로드 완료 ({elapsed:.2f}초)")
            
        except Exception as e:
            logger.error(f"❌ 모델 로드 실패: {e}")
            raise e

    def encode(self, texts: Union[str, List[str]]) -> np.ndarray:
        """
        입력된 텍스트에 대한 임베딩을 생성합니다.
        반환값: (N, 1024) 크기의 numpy 배열
        """
        if isinstance(texts, str):
            texts = [texts]
            
        if not self.model or not self.tokenizer:
            raise RuntimeError("모델이 초기화되지 않았습니다.")

        # 토크나이징 (PyTorch Tensor 반환)
        inputs = self.tokenizer(
            texts, 
            padding=True, 
            truncation=True, 
            max_length=512, 
            return_tensors="pt"
        )
        
        # ONNX Runtime 직접 실행을 위해 입력 변환 (Tensor -> Numpy)
        ort_inputs = {k: v.cpu().numpy() for k, v in inputs.items()}
        
        # 추론 (Bypass optimum forward to avoid KeyError)
        # self.model.model 은 onnxruntime.InferenceSession 객체입니다.
        ort_outputs = self.model.model.run(None, ort_inputs)
        
        # 출력 이름 확인 및 데이터 추출
        output_names = [output.name for output in self.model.model.get_outputs()]
        
        embeddings = None
        
        # 1. sentence_embedding이 있으면 우선 사용 (이미 Pooling 됨)
        if "sentence_embedding" in output_names:
            idx = output_names.index("sentence_embedding")
            embeddings = ort_outputs[idx]
        
        # 2. 없으면 token_embeddings(또는 last_hidden_state)를 찾아 Mean Pooling 수행
        elif "token_embeddings" in output_names or "last_hidden_state" in output_names:
            name = "token_embeddings" if "token_embeddings" in output_names else "last_hidden_state"
            idx = output_names.index(name)
            token_embeddings = ort_outputs[idx] # [batch, seq_len, hidden]
            
            # Numpy로 Mean Pooling 구현
            attention_mask = ort_inputs['attention_mask'] # [batch, seq_len]
            
            # 차원 확장
            input_mask_expanded = np.expand_dims(attention_mask, axis=-1)
            token_embeddings = token_embeddings * input_mask_expanded
            
            sum_embeddings = np.sum(token_embeddings, axis=1)
            sum_mask = np.sum(input_mask_expanded, axis=1)
            sum_mask = np.maximum(sum_mask, 1e-9) # 0 나누기 방지
            
            embeddings = sum_embeddings / sum_mask
            
        else:
            raise KeyError(f"지원되지 않는 모델 출력 형식입니다: {output_names}")
        
        # 임베딩 정규화 (L2 Norm)
        norm = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings = embeddings / norm
        
        return embeddings

    def warmup(self):
        """
        ONNX 세션 초기화를 위한 더미 추론을 수행합니다.
        """
        logger.info("🔥 모델 웜업(Warm-up) 시작...")
        try:
            dummy_text = "Warm up the model."
            start = time.time()
            vectors = self.encode(dummy_text)
            elapsed = (time.time() - start) * 1000
            
            dim = vectors.shape[1]
            logger.info(f"🔥 웜업 완료! (차원: {dim}, 소요시간: {elapsed:.2f}ms)")
            
            if dim != 1024:
                logger.warning(f"⚠️ 예상 차원(1024)과 다릅니다: {dim}")
                
        except Exception as e:
            logger.error(f"❌ 웜업 실패: {e}")
            # 여기서 에러를 발생시키지 않고 로그만 남깁니다.

# 전역 인스턴스 생성
embedding_model = EmbeddingModel()
