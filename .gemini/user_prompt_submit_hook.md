# AI Agent Workflow (Constitution & Integrity Hook)

본 프로젝트는 상용 수준의 안정성과 품질을 유지하기 위해, 모든 작업 단계에서 **'기술 헌법(Source of Truth)'**을 준수해야 합니다.

## 1단계: 프롬프트 분석 및 영역 분류 (MANDATORY)
- 모든 사용자 요청은 가장 먼저 다음 세 가지 영역 중 하나 이상으로 분류되어야 합니다:
  - **Front-end**: Next.js, UI 컴포넌트, 상태 관리 등. (지침: `.gemini/skills/frontend_skill.md`)
  - **Back-end**: FastAPI, Celery, Worker 로직 등. (지침: `.gemini/skills/backend_skill.md`)
  - **Database**: PostgreSQL, Redis, 스키마 등. (지침: `.gemini/skills/database_skill.md`)
- **기술 헌법 로드 (MANDATORY)**: 분류된 영역에 해당하는 `.gemini/skills/` 내의 모든 스킬 파일을 **반드시 `view_file` 도구를 사용하여 읽고 내용을 내재화**해야 합니다. 이는 어떠한 예외도 허용되지 않는 필수 절차입니다.
- 분류 결과와 읽어들인 스킬 파일 목록은 `implementation_plan.md` 서두에 명시합니다.

## 2단계: 관련 지식 탐색 (Knowledge Discovery)
- 프로젝트 내 **Knowledge Items(KI)**와 과거 대화 로그를 확인하여 기술적 맥락을 확보합니다.
- 기존의 결정 사항이 현재 작업에 미치는 영향을 분석하여 일관성을 유지합니다.

## 3단계: 작업 체크리스트 및 계획 수립
- `task.md`를 통해 전체 작업 경로를 가시화합니다.
- `implementation_plan.md`를 작성하여 다음을 명시합니다:
    - 참조한 **기술 헌법** 및 **KI** 목록.
    - 지침에 근거한 설계 방향 및 구체적인 파일 변경 제안.
    - 기술 헌법의 기준을 충족하는지 확인할 수 있는 검증 계획.

## 4단계: 사용자 승인 및 피드백 반영
- 작성된 계획을 사용자에게 공유하고 승인을 받습니다. **승인 전까지는 코드 수정을 절대 시작하지 않습니다.**

## 5단계: 승인된 문서 확정 및 최종 아티팩트 공유 (MANDATORY)
- 사용자 승인 직후, **최종 계획(`implementation_plan.md`), 맥락(`KI`), 체크리스트(`task.md`)**를 공식 아티팩트로 작성/확정합니다.
- `notify_user` 도구를 사용하여 사용자에게 최종 확정된 문서들의 경로를 공유하고, 실행 단계로 진입함을 공식적으로 알립니다.

## 6단계: 실행 및 구현
- 승인 및 공유된 계획과 **기술 헌법**의 세부 지침에 따라 코드를 작성합니다.

## 7단계: 최종 결과 검토 (Post-Execution Review)
- 모든 도구 사용이 끝난 후, [PostToolUse.md](file:///Users/soyoungan/dev/test_kr/.gemini/PostToolUse.md)를 로딩하여 결과물을 최종 검토합니다.
- 자가 검토 체크리스트를 통해 기술 헌법 준수 여부와 완결성을 확인하고 미비점은 즉시 보완합니다.

## 8단계: 성과 보고 (Reporting)
- 최종 검토를 마친 후 `walkthrough.md`를 통해 변경 사항과 검증 결과를 상세히 보고하며 작업을 마무리합니다.