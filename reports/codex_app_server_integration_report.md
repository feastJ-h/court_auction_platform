# Codex app-server 연동 검증 리포트

## 1. 목적
`codex exec` 단발 실행 기반의 비동기 분석 구조를 확장해, Codex app-server의 thread/turn 기반 분석 흐름을 웹앱에서 추적할 수 있도록 구현하고 검증했다.

## 2. 구현 범위
- app-server WebSocket JSON-RPC 클라이언트
- app-server 워커
- app-server 프로토콜 요청 빌더
- 이벤트 스트림 파서
- 분석 이벤트 저장소
- job 취소 요청 API
- job 이벤트 조회 API
- 이어서 분석 API
- 관리자/사용자 UI 진행 로그 표시
- app-server 실행 및 워커 실행 PowerShell 스크립트

## 3. 주요 파일
- `backend/analysis_worker/app_server_client.py`
- `backend/analysis_worker/app_server_worker.py`
- `backend/analysis_worker/app_server_protocol.py`
- `backend/analysis_worker/event_stream.py`
- `backend/jobs/event_repository.py`
- `backend/jobs/service.py`
- `backend/jobs/repository.py`
- `backend/database/models.py`
- `backend/database/session.py`
- `main_app.py`
- `frontend/templates/admin/dashboard.html`
- `frontend/static/app.js`
- `run_codex_app_server.ps1`
- `run_codex_app_server_worker.ps1`
- `run_codex_app_server_worker_forever.ps1`

## 4. 검증 결과
- `codex app-server --help`로 로컬 CLI에서 app-server 기능 사용 가능 확인.
- `websockets` 패키지 설치 및 import 확인.
- Mock app-server 모드:
  - 성공 job 처리
  - 취소 요청 처리
  - 이어서 분석 처리
  - 실패 격리 처리
- 실제 app-server 모드:
  - `ws://127.0.0.1:4500` 연결 성공
  - initialize 성공
  - thread/start 성공
  - turn/start 성공
  - event stream 수신 성공
  - delta 응답 누적 및 JSON 파싱 성공
  - 상세 분석 결과 DB 및 파일 저장 성공
- 브라우저 검증:
  - `/admin`에서 `SUCCEEDED 8`, `FAILED 4`, `CANCELED 1` 표시 확인
  - `/admin`에서 실제 thread ID `019f2e2e-2892-7f93-bf2e-5da8a8102edc` 표시 확인
  - `/admin`에서 최근 이벤트 로그 표시 확인
  - `/user`에서 상세 분석 탭과 원문/심층 분석 패널 렌더링 확인

## 5. 실제 분석 성공 사례
- Job ID: 13
- Provider mode: `app_server`
- Thread ID: `019f2e2e-2892-7f93-bf2e-5da8a8102edc`
- Turn ID: `019f2e2e-28f7-7920-894c-7ade80966b8e`
- Status: `SUCCEEDED`
- Output:
  - `storage/analysis_jobs/13/output.json`
  - `storage/analysis_jobs/13/output.md`
- 요약:
  - 회생·파산 절차상 채권 매각 공고를 분석했다.
  - 최저입찰가와 회차별 일정, 권리/회수 리스크, 추가 확인 서류가 구조화되어 저장됐다.

## 6. 운영상 주의점
- app-server는 현재 로컬 전용으로 사용해야 한다.
- app-server 프로세스와 FastAPI 서버, 워커는 별도 터미널에서 분리 실행하는 것이 안정적이다.
- 실제 app-server 이벤트는 매우 촘촘한 delta 스트림이므로, 운영 데이터가 늘어나면 이벤트 보관 정책이 필요하다.
- 현재 실패 job 일부는 프로토콜 보강 전 검증 중 생성된 기록이며, 장애 추적 사례로 DB에 유지했다.
