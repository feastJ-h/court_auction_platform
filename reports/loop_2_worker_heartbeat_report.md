# Loop 2 보고서

## 목표
관리자 화면과 상태 API에서 로컬 분석 워커가 실제로 살아 있는지 판단할 수 있게 한다.

## 변경한 내용
- `AnalysisWorkerHeartbeat` 모델과 `analysis_worker_heartbeats` 테이블을 추가했다.
- `backend/jobs/worker_heartbeat.py` 저장소를 추가했다.
- Codex CLI 워커와 Codex app-server 워커가 시작, 대기, 진행, 완료, 오류 상태를 heartbeat로 기록하도록 연결했다.
- `/api/local-analysis/status` 응답에 worker 목록, 활성 worker 수, 멈춤 가능 worker 수, 마지막 worker 정보를 포함했다.
- 관리자 화면 Local Analysis App 카드에 마지막 worker, 현재 job, PID, 상태 메시지, 멈춤 가능성 표시를 추가했다.
- worker heartbeat가 없어도 웹앱은 정상 동작하도록 빈 목록을 기본값으로 처리했다.

## 수정한 파일
- `backend/database/models.py`
- `backend/jobs/worker_heartbeat.py`
- `backend/analysis_worker/cli_worker.py`
- `backend/analysis_worker/app_server_worker.py`
- `main_app.py`
- `frontend/templates/admin/dashboard.html`

## 검증 결과
- Python 문법 검증 통과
- JavaScript 문법 검증 통과
- `run_local_analysis_app.ps1 -Limit 1 -Mock -RunOnce` 실행 성공
- `analysis_worker_heartbeats` row 생성 확인
- `/api/local-analysis/status` 200
- `/api/local-analysis/status`에서 `worker_count >= 1`, `latest_worker` 반환 확인
- `/admin` 200 및 `codex_app_server_worker` 표시 확인
- `/user` 200

## 남은 위험
- 현재 heartbeat는 워커 프로세스가 한 번 실행될 때 갱신된다. 실제 장시간 분석 중 세밀한 주기 heartbeat는 app-server 이벤트 수신 시에는 갱신되지만, CLI subprocess가 오래 침묵하면 10분 이후 stale로 보일 수 있다.
- PowerShell 콘솔 출력 인코딩 때문에 한글 문자열 직접 assert는 흔들릴 수 있어 구조/API 중심으로 검증했다.

## 다음 루프 지시
Loop 3에서 `analysis_results` 중복 방지 조건에 `prompt_version`을 포함하고, 같은 event/model/type/source_hash/prompt_version 재요청 시 row와 job이 증가하지 않는지 검증한다.
