# 비동기 Codex 분석 Phase 2 완료 리포트

## 1. 구현된 주요 기능
- `codex_app_server_phase_2_instruction.md` 기준으로 `codex app-server` 연동형 상세 분석 워커를 추가했다.
- `analysis_jobs`에 app-server 추적 컬럼을 추가했다.
  - `codex_thread_id`
  - `codex_turn_id`
  - `progress_message`
  - `progress_percent`
  - `last_event_at`
  - `cancel_requested`
  - `provider_mode`
- `analysis_job_events` 테이블을 추가해 app-server 진행 이벤트를 DB에 누적 저장한다.
- 기존 `codex exec` 워커는 fallback 경로로 유지하고, app-server 워커를 별도 프로세스로 실행하도록 분리했다.
- 관리자 화면에 작업 상태별 카운트, provider mode, thread/turn ID, 진행률, 최근 이벤트, 취소 요청, 이어서 분석 폼을 추가했다.
- 사용자 화면의 상세 분석 패널에 진행 상태, 진행률, provider mode, 최근 이벤트 로그를 표시하도록 연결했다.
- `mock` app-server 모드를 추가해 외부 호출 없이 job 생성, 진행 이벤트, 성공/취소/실패 흐름을 반복 검증할 수 있게 했다.

## 2. 보안 및 예외 처리
- app-server는 기본 실행 스크립트에서 `ws://127.0.0.1:4500` 로컬 루프백 주소만 사용한다.
- 웹 요청은 분석을 직접 실행하지 않고 `analysis_jobs`에 작업만 등록한다.
- 취소는 즉시 강제 종료가 아니라 `cancel_requested` 플래그를 저장하고 워커가 안전 지점에서 확인한다.
- 이어서 분석 API는 1000자 이하의 추가 지시만 허용하며, 경로 이동 문자열과 민감 키워드 일부를 차단한다.
- mock thread ID가 실제 app-server로 넘어가면 프로토콜 오류가 발생하므로, 실제 app-server 모드에서는 `mock-` 또는 UUID가 아닌 thread ID를 무시하고 새 thread를 생성하도록 보강했다.
- app-server 연결 실패, 프로토콜 오류, 타임아웃은 job 실패로 격리하고 이벤트 로그에 남긴다.
- 원본 PDF/HWP는 분석 완료 후 `storage/processed/analyzed_documents`로 이동해 반복 분석 요청을 줄이는 기존 구조를 유지했다.

## 3. 단위 및 통합 테스트 결과
- Python 문법 검증:
  - `main_app.py`
  - `backend/database/models.py`
  - `backend/database/session.py`
  - `backend/jobs/*.py`
  - `backend/analysis_worker/app_server_*.py`
- JavaScript 문법 검증:
  - `frontend/static/app.js`
- FastAPI TestClient:
  - `/user` 200
  - `/admin` 200
  - `/api/analyze/jobs/5/events` 200
- SQLite 마이그레이션:
  - `analysis_jobs` app-server 컬럼 추가 확인
  - `analysis_job_events` 테이블 생성 확인
- Mock app-server 워커:
  - 성공 job 처리 확인
  - 사전 취소 요청 job 취소 확인
  - app-server 미실행 시 실패 격리 확인
  - 이어서 분석 job 생성 및 thread 유지 확인
- 실제 `codex app-server` 워커:
  - 연결, initialize, thread/start, turn/start, 이벤트 스트림 수신 확인
  - `item/agentMessage/delta` 누적 후 최종 JSON 파싱 성공 확인
  - job #13 `SUCCEEDED`
  - 결과 저장:
    - `storage/analysis_jobs/13/output.json`
    - `storage/analysis_jobs/13/output.md`
    - `storage/analysis_jobs/13/stderr.log`
- 최종 DB 상태:
  - `SUCCEEDED`: 8
  - `FAILED`: 4
  - `CANCELED`: 1
  - `analysis_job_events`: 4682건

## 4. 실제 app-server 검증 중 발견 및 보완한 이슈
- 실제 app-server의 `thread/start` 응답은 `{ "thread": { "id": "..." } }` 구조였다.
  - `CodexAppServerClient.start_thread()`가 중첩된 `thread.id`를 읽도록 수정했다.
- 실제 app-server의 agent 응답은 최종 메시지 단일 이벤트가 아니라 `item/agentMessage/delta` 스트림으로 전달됐다.
  - 워커가 delta를 누적해 최종 JSON으로 파싱하도록 수정했다.
- mock thread ID를 실제 app-server에 resume하려 하면 `invalid thread id` 오류가 발생했다.
  - 실제 app-server 모드에서는 UUID/`urn:uuid:` 형식이 아닌 thread ID를 resume하지 않도록 수정했다.

## 5. 실행 방법
```powershell
# FastAPI 웹 서버
powershell -ExecutionPolicy Bypass -File .\run_fastapi.ps1

# Codex app-server 실행
powershell -ExecutionPolicy Bypass -File .\run_codex_app_server.ps1 -Endpoint ws://127.0.0.1:4500

# app-server 워커 1건 처리
powershell -ExecutionPolicy Bypass -File .\run_codex_app_server_worker.ps1 -Endpoint ws://127.0.0.1:4500 -Limit 1

# app-server 워커 상시 루프
powershell -ExecutionPolicy Bypass -File .\run_codex_app_server_worker_forever.ps1 -Endpoint ws://127.0.0.1:4500 -IdleSleepSeconds 10

# 외부 호출 없는 mock 검증
powershell -ExecutionPolicy Bypass -File .\run_codex_app_server_worker.ps1 -Limit 1 -Mock

# 기존 codex exec 워커 상시 루프
powershell -ExecutionPolicy Bypass -File .\run_cli_analysis_worker_forever.ps1 -Limit 1 -IdleSleepSeconds 10
```

## 6. 다음 검토 필요 사항
- 실제 app-server delta 이벤트는 매우 세밀해 1건에 약 2000개 이상의 이벤트가 저장될 수 있다. 운영 전에는 delta 이벤트를 N자 단위 또는 시간 단위로 묶어 저장하는 압축 전략을 검토하는 것이 좋다.
- 현재 app-server는 로컬 루프백 전용으로 검증했다. 외부 접근이 필요해지면 인증 토큰과 방화벽 정책을 먼저 설계해야 한다.
- OCR이 필요한 스캔 PDF와 HWP 변환 실패 문서는 별도 `OCR_REQUIRED`/`CONVERSION_FAILED` 큐로 분리하는 것이 다음 고도화 과제다.
