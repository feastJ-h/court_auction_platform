# 운영용 크롤링 스케줄 및 관리자 수집 관리 스프린트 리포트

## 1. 구현된 주요 기능
- `production_crawling_schedule_instruction.md`를 기준으로 운영용 정기 수집 골격을 구현했습니다.
- `CrawlRun` 모델을 추가해 정기/수동/보정/재시도 수집 실행 이력을 DB에 저장합니다.
- `backend/workers/scheduled_crawl.py`를 추가해 최근 14일 기본 수집과 DryRun 검증을 지원합니다.
- `run_scheduled_crawl.ps1`을 추가해 Windows 작업 스케줄러에서 실행 가능한 운영 스크립트를 만들었습니다.
- `/admin/collection`을 placeholder에서 실제 수집 관리 화면으로 전환했습니다.
- `docs/production_crawling_schedule_runbook.md`에 PowerShell 수동 실행, DryRun, 작업 스케줄러 등록 방법을 문서화했습니다.
- `PROJECT_BRIEF.md`에 운영 수집 진입점과 로그/DB/화면 위치를 추가했습니다.

## 2. 보안 및 예외 처리 내역
- 정기 수집 스크립트는 `storage/scheduled_crawl.lock` 파일을 독점 잠금으로 열어 중복 실행을 방지합니다.
- 실행 로그는 `storage/logs/crawl_runs`에 남기고, DB에는 로그 경로만 저장합니다.
- 실패 시 `crawl_runs.status=FAILED`와 축약된 오류 메시지를 남기도록 했습니다.
- 테스트는 외부 법원 사이트 접속 없이 `-DryRun`으로 수행해 운영 스크립트와 DB 기록만 검증했습니다.
- 정기 수집과 2026-06-15 이후 보정 수집은 `run_type`으로 분리했습니다.

## 3. 테스트 결과
- 문법 검사:
  - `main_app.py`
  - `backend/database/models.py`
  - `backend/services/crawl_runs.py`
  - `backend/workers/scheduled_crawl.py`
- DryRun 실행:
  - `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_scheduled_crawl.ps1 -DryRun`
  - 결과: `ExitCode=0`
  - 로그: `storage/logs/crawl_runs/crawl_scheduled_20260705_163728.log`
- DB 확인:
  - `crawl_runs`에 `scheduled / SUCCEEDED / 2026-06-21 ~ 2026-07-05` 이력 저장 확인
- 기존 격리 테스트:
  - `tests/isolated_operations_test.py` 통과
- 관리자 화면:
  - `/admin/collection` 로그인 후 `HTTP 200`
  - `수집 관리`, `SUCCEEDED`, `다음 예정 수집` 렌더링 확인

## 4. 다음 스프린트 큐
- `/admin/assets`, `/admin/analysis`, `/admin/reviews`를 placeholder에서 실제 화면으로 분리.
- `run_scheduled_crawl.ps1` 실제 수집 모드에서 결과 수치 정확도 보강: 다운로드 실패, 파싱 실패, AI 실패를 별도 컬럼으로 확장.
- 실패 다운로드만 재시도하는 `retry_failed` 흐름 구현.
- UNKNOWN 날짜 보정 큐와 2026-06-15 이후 보정 수집을 별도 관리자 버튼으로 제공.
- 정기 수집 후 OCR_REQUIRED 자동 큐 적재 여부를 운영 토글로 분리.
