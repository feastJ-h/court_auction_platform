# Codex 작업 가이드

이 프로젝트에서 작업을 시작할 때 전체 소스를 무작정 스캔하지 않는다.

## 읽기 순서
1. `PROJECT_BRIEF.md`
2. `reports/project_build_summary_and_next_instructions.md`
3. 현재 요청과 직접 관련된 모듈만 확인
4. 마지막 스프린트 리포트 1개

## 작업 원칙
- 운영 DB `auction_data.db`를 테스트로 오염시키지 않는다. 라우터 테스트는 가능한 `run_isolated_operations_test.ps1` 또는 별도 테스트 DB를 사용한다.
- 관리자/사용자 인증이 필요한 API는 반드시 권한 검사를 유지한다.
- 원문 텍스트, 주민번호, 전화번호는 로그와 감사 로그에 남기지 않는다.
- OCR/AI/크롤링 실패는 실패 사유를 DB job 또는 report에 남기고 앱 전체를 죽이지 않는다.
- 새 기능은 스프린트 단위로 구현, 검증, 리포트 작성 순서로 닫는다.

## 자주 쓰는 명령
```powershell
powershell -ExecutionPolicy Bypass -File .\start_fastapi_background.ps1
powershell -ExecutionPolicy Bypass -File .\run_isolated_operations_test.ps1
powershell -ExecutionPolicy Bypass -File .\run_ocr_worker.ps1 -Limit 1 -DryRun
powershell -ExecutionPolicy Bypass -File .\run_ocr_worker.ps1 -Limit 1 -Enqueue
```
