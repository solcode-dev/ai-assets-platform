# Post-Execution Review Guidelines (Senior Level)

작업 완료 후, 결과물의 품질을 시니어 엔지니어의 시각에서 최종 검토하기 위한 체크리스트입니다. 모든 구현 결과는 이 기준을 통과해야 합니다.

## 1. 지침 준수 여부 (Constitutional Compliance)
- [ ] **기술 헌법 준수**: 수정된 코드가 `.gemini/skills/` 내의 Front/Back/DB 매뉴얼 원칙을 정확히 지켰는가?
- [ ] **계획 일치성**: `implementation_plan.md`에서 제안한 설계 방향과 검증 계획을 충실히 이행했는가?

## 2. 코드 퀄리티 및 안정성 (Code Excellence)
- [ ] **부작용(Side Effects) 최소화**: 수정 범위 외의 기능에 영향을 미칠 가능성이 있는 로직이 포함되지 않았는가?
- [ ] **가독성 및 유지보수성**: 변수명, 함수 구조, 타입 힌트가 명확하며 주석이 적절히 배치되었는가?
- [ ] **에러 핸들링**: 예외 상황에 대한 선언적 처리 및 로깅이 누락되지 않았는가?

## 3. 성능 및 보안 (Efficiency & Security)
- [ ] **성능 최적화**: 렌더링 병목(Front), DB 쿼리 효율(DB), 워커 부하(Back)를 고려했는가? (특히 CLS, LCP 등 Web Vitals 준수 여부)
- [ ] **보안 무결성**: 민감 정보 노출 방지, 데이터 정제(Sanitization), 권한 제어 원칙을 지켰는가?

## 4. 최종 검증 및 문서화 (Validation & Docs)
- [ ] **실제 동작 검증**: 검증 계획에 따른 테스트(Unit/Integration/Manual) 결과가 성공적인가?
- [ ] **문서 최신화**: `walkthrough.md`에 변경 사항과 검증 증거가 상세히 기록되었는가?
- [ ] **지식 전파**: 필요시 새로운 지식이나 트러블슈팅 경험을 KI(Knowledge Item)로 남길 준비가 되었는가?

---
**검토 완료 후, 발견된 미비점은 즉시 수정하거나 `walkthrough.md`에 기술 부채로서 기록하여 명확히 고지합니다.**
