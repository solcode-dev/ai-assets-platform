# Gemini 3.0 Configuration Folder

이 폴더는 Gemini 3.0 모델의 동작을 제어하고 프롬프트를 관리하기 위한 설정 폴더입니다.

## 파일 구성
- `config.json`: 모델 버전, 파라미터(Temperature, Token 등), 및 엔드포인트 설정.
- `instructions.md`: Gemini 3.0에 전달할 시스템 명령 및 가이드라인.

## 사용 방법
1. `config.json`에서 사용하고자 하는 모델 버전을 확인합니다.
2. `instructions.md`에 프로젝트 특화 페르소나를 정의합니다.
3. 백엔드 코드에서 이 설정을 읽어 Vertex AI API 호출 시 활용합니다.

## 참고
이 설정은 Gemini 3.0 Flash (Preview) 모델을 기준으로 최적화되어 있습니다.
