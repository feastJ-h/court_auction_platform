# Codex app-server 2차 확장 상세 지시서

## 1. 목표

1차 `codex exec` 기반 워커는 대기 작업을 처리하고 결과를 저장하는 데 적합하다. 2차 확장은 `codex app-server`를 도입해 웹앱과 Codex 사이의 연결을 더 깊게 만든다.

2차 목표:

- Codex thread와 turn을 DB에 저장한다.
- 분석 진행 이벤트를 웹앱에서 볼 수 있게 한다.
- 작업 취소, 이어서 분석, 추가 지시를 지원한다.
- `codex exec` 방식은 fallback으로 유지한다.
- app-server 장애 시 기존 job 구조가 깨지지 않게 한다.

## 2. 최종 구조

```text
웹앱
  - 상세 분석 요청
  - 진행 로그 조회
  - 취소 요청
  - 이어서 분석 요청

FastAPI
  - analysis_jobs 생성/조회
  - analysis_job_events 조회
  - cancel_requested 저장

App-server 워커
  - codex app-server 연결
  - initialize
  - thread/start 또는 thread/resume
  - turn/start
  - 이벤트 수신
  - DB에 진행 이벤트 저장
  - 최종 결과 저장

Codex app-server
  - ChatGPT 로그인 세션 사용
  - thread/turn 처리
  - agent event stream 제공
```

## 3. 2차 구현 원칙

1. 웹앱은 여전히 분석을 직접 실행하지 않는다.
2. app-server는 로컬 루프백 주소에서만 실행한다.
3. app-server 프로세스와 분석 워커는 웹앱 프로세스와 분리한다.
4. 모든 진행 이벤트는 DB에 저장한다.
5. 최종 상세 분석은 기존 `ai_analyses.detailed_analysis`에 저장한다.
6. 기존 `codex exec` 워커를 삭제하지 않는다.
7. app-server 실패 시 job은 `FAILED`로 남기고 재시도 가능하게 한다.

## 4. 실행 방식

### 4.1 app-server 실행

로컬 전용으로 실행한다.

```powershell
cd C:\Users\xogns\Documents\testAuction\court_auction_platform
codex app-server --listen ws://127.0.0.1:4500
```

외부 IP로 열지 않는다. 원격 접근이 필요할 때는 capability token 또는 signed bearer token 인증을 붙인 뒤 진행한다.

### 4.2 app-server 워커 실행

새 스크립트:

```text
run_codex_app_server_worker.ps1
```

예상 실행:

```powershell
cd C:\Users\xogns\Documents\testAuction\court_auction_platform
.\run_codex_app_server_worker.ps1 -Endpoint ws://127.0.0.1:4500 -Limit 1
```

상시 루프 실행:

```powershell
.\run_codex_app_server_worker_forever.ps1 -Endpoint ws://127.0.0.1:4500 -IdleSleepSeconds 10
```

## 5. DB 확장

### 5.1 `analysis_jobs` 컬럼 추가

추가 필드:

```text
codex_thread_id TEXT NOT NULL DEFAULT ''
codex_turn_id TEXT NOT NULL DEFAULT ''
progress_message TEXT NOT NULL DEFAULT ''
progress_percent INTEGER NOT NULL DEFAULT 0
last_event_at DATETIME NULL
cancel_requested BOOLEAN NOT NULL DEFAULT 0
provider_mode TEXT NOT NULL DEFAULT 'exec'
```

`provider_mode` 값:

```text
exec
app_server
app_server_fallback_exec
```

### 5.2 새 테이블: `analysis_job_events`

필드:

```text
id INTEGER PRIMARY KEY
job_id INTEGER NOT NULL
event_type TEXT NOT NULL
event_payload TEXT NOT NULL
message TEXT NOT NULL DEFAULT ''
created_at DATETIME NOT NULL
```

관계:

```text
analysis_job_events.job_id -> analysis_jobs.id
```

### 5.3 마이그레이션 위치

현재 프로젝트는 SQLite 자동 보강을 `backend/database/session.py`의 `ensure_schema_migrations()`에서 처리한다.

2차 구현도 우선 같은 방식으로 추가한다.

주의:

- 기존 DB를 삭제하지 않는다.
- 컬럼 존재 여부를 확인한 뒤 없을 때만 `ALTER TABLE`을 실행한다.
- 새 테이블은 `Base.metadata.create_all()`로 생성되게 모델에 추가한다.

## 6. 파일 구조

추가 파일:

```text
backend/analysis_worker/app_server_client.py
backend/analysis_worker/app_server_worker.py
backend/analysis_worker/event_stream.py
backend/analysis_worker/app_server_protocol.py
backend/jobs/event_repository.py
run_codex_app_server.ps1
run_codex_app_server_worker.ps1
run_codex_app_server_worker_forever.ps1
```

기존 파일 확장:

```text
backend/database/models.py
backend/database/session.py
backend/jobs/repository.py
backend/jobs/service.py
main_app.py
frontend/static/app.js
frontend/templates/admin/dashboard.html
```

## 7. app-server 클라이언트 설계

### 7.1 연결

`app_server_client.py` 역할:

- WebSocket 연결
- JSON-RPC 요청 전송
- 응답 id 매칭
- notification 수신
- timeout 처리
- 연결 종료 처리

권장 클래스:

```python
class CodexAppServerClient:
    def __init__(self, endpoint: str, timeout_seconds: int = 900): ...
    async def connect(self) -> None: ...
    async def initialize(self) -> None: ...
    async def start_thread(self, model: str | None = None) -> str: ...
    async def start_turn(self, thread_id: str, input_text: str, cwd: str) -> str: ...
    async def interrupt_turn(self, thread_id: str, turn_id: str) -> None: ...
    async def events(self): ...
    async def close(self) -> None: ...
```

### 7.2 초기화 메시지

연결 후 반드시 수행한다.

```json
{
  "method": "initialize",
  "id": 1,
  "params": {
    "clientInfo": {
      "name": "court_auction_platform",
      "title": "Court Auction Platform",
      "version": "0.1.0"
    },
    "capabilities": {
      "experimentalApi": true
    }
  }
}
```

이후 notification:

```json
{
  "method": "initialized",
  "params": {}
}
```

### 7.3 thread 시작

새 분석 job이면 `thread/start`를 사용한다.

```json
{
  "method": "thread/start",
  "id": 2,
  "params": {
    "model": "gpt-5.4"
  }
}
```

모델명은 실제 설치/계정에서 가능한 값으로 조정한다. 모델 지정이 불안정하면 우선 생략하고 Codex 기본값을 사용한다.

### 7.4 turn 시작

```json
{
  "method": "turn/start",
  "id": 3,
  "params": {
    "threadId": "THREAD_ID",
    "cwd": "C:\\Users\\xogns\\Documents\\testAuction\\court_auction_platform",
    "input": [
      {
        "type": "text",
        "text": "storage/analysis_jobs/3/input.md 파일을 읽고 지정된 JSON 스키마에 맞춰 경매/공매 상세 분석을 작성하라."
      }
    ]
  }
}
```

## 8. 워커 처리 흐름

`app_server_worker.py` 처리 순서:

```text
1. init_db()
2. PENDING job 조회
3. job.provider_mode = app_server
4. job.status = RUNNING
5. input.md 생성
6. app-server 연결
7. initialize
8. thread/start
9. thread id 저장
10. turn/start
11. turn id 저장
12. 이벤트 수신 loop
13. 이벤트를 analysis_job_events에 저장
14. agent final message 추출
15. JSON 파싱
16. output.json/output.md 저장
17. ai_analyses.detailed_analysis 저장
18. job.status = SUCCEEDED
```

취소 요청 처리:

```text
1. 웹앱에서 cancel_requested = true 저장
2. 워커 이벤트 loop 중 cancel_requested 확인
3. turn/interrupt 전송
4. job.status = CANCELED
```

실패 처리:

```text
1. 연결 실패
2. initialize 실패
3. thread/start 실패
4. turn/start 실패
5. timeout
6. output JSON 파싱 실패
7. cancel 처리 실패
```

각 실패는 `analysis_jobs.error_code`, `analysis_jobs.error_message`, `analysis_job_events`에 저장한다.

## 9. 이벤트 저장 규칙

저장할 이벤트:

```text
thread/started
turn/started
item/started
item/completed
item/agentMessage/delta
turn/completed
turn/failed
error
```

`item/agentMessage/delta`는 너무 많아질 수 있으므로 다음 중 하나로 처리한다.

1. 모든 delta 저장
2. 1초 단위로 합쳐 저장
3. 최종 메시지만 저장

1차 app-server 구현에서는 2번을 권장한다.

## 10. API 추가

추가 API:

```text
GET  /api/analyze/jobs/{job_id}/events
POST /api/analyze/jobs/{job_id}/continue
POST /api/analyze/jobs/{job_id}/cancel-request
```

기존 `cancel` API는 즉시 `CANCELED` 처리하는 방식이다. app-server에서는 실제 turn interrupt가 필요하므로 `cancel-request`를 별도로 둔다.

### 10.1 이벤트 조회 응답

```json
{
  "job": {},
  "events": [
    {
      "id": 1,
      "event_type": "turn/started",
      "message": "분석을 시작했습니다.",
      "created_at": "..."
    }
  ]
}
```

### 10.2 이어서 분석 요청

`continue`는 기존 thread id가 있을 때만 허용한다.

입력:

```json
{
  "instruction": "권리관계 부분을 더 자세히 정리해줘."
}
```

보안 기준:

- 사용자 자유 입력은 그대로 셸 명령에 넣지 않는다.
- app-server turn input에는 넣을 수 있지만, 서버에서 길이 제한과 금칙어/경로 검증을 한다.
- 1차 구현에서는 관리자 화면에서만 허용한다.

## 11. UI 확장

### 11.1 사용자 화면

상세 분석 탭에 추가:

- 현재 상태
- 마지막 진행 메시지
- 진행 로그 접기/펼치기
- 완료 결과
- 실패 사유

사용자에게 너무 많은 raw event를 보여주지 않는다.

### 11.2 관리자 화면

추가:

- job 목록
- PENDING/RUNNING/FAILED/SUCCEEDED 카운트
- app-server 연결 상태
- 최근 이벤트
- 실패 로그
- cancel 요청
- 이어서 분석 입력

### 11.3 폴링

기존 job 상태 폴링은 유지한다.

추가 폴링:

```text
RUNNING 상태일 때 /api/analyze/jobs/{job_id}/events를 3초마다 호출
```

## 12. fallback 전략

app-server가 실패하면 다음 선택지를 둔다.

### 옵션 A: 실패만 기록

```text
job.status = FAILED
error_code = APP_SERVER_UNAVAILABLE
```

관리자가 재시도한다.

### 옵션 B: exec fallback

```text
provider_mode = app_server_fallback_exec
codex exec 워커로 재처리
```

초기 2차 구현에서는 옵션 A를 먼저 사용한다. 안정화 후 옵션 B를 추가한다.

## 13. 보안 기준

- app-server는 `127.0.0.1`에만 바인딩한다.
- 외부 네트워크에 열지 않는다.
- WebSocket transport는 실험적일 수 있으므로 로컬 전용으로 사용한다.
- 원격 노출 전에는 capability token 또는 signed bearer token 인증을 적용한다.
- 사용자 입력은 길이 제한과 검증을 거친다.
- 인증 파일은 비밀번호처럼 취급한다.
- job input/output에는 개인정보가 포함될 수 있으므로 관리자 접근으로 제한한다.

## 14. 구현 순서

### Sprint 2-1: DB와 이벤트 저장

1. `AnalysisJobEvent` 모델 추가
2. `analysis_jobs` 추가 컬럼 반영
3. `ensure_schema_migrations()` 확장
4. `backend/jobs/event_repository.py` 추가
5. 이벤트 조회 API 추가
6. 단위 테스트 또는 간단 DB 검증

완료 기준:

- 이벤트를 DB에 저장/조회할 수 있다.
- 기존 `analysis_jobs` 데이터가 유지된다.

### Sprint 2-2: app-server 연결 검증

1. `run_codex_app_server.ps1` 추가
2. `app_server_client.py` 추가
3. initialize 테스트
4. thread/start 테스트
5. turn/start 테스트
6. 이벤트 수신 로그 저장

완료 기준:

- app-server에 연결하고 간단한 turn을 완료할 수 있다.
- thread id와 turn id를 확인할 수 있다.

### Sprint 2-3: app-server 워커

1. `app_server_worker.py` 추가
2. PENDING job 처리
3. input snapshot 생성 재사용
4. event 저장
5. final output 파싱
6. 상세 분석 저장
7. 실패 처리

완료 기준:

- 실제 PENDING job 1개가 app-server 방식으로 완료된다.
- output.json/output.md가 저장된다.
- 웹앱에서 완료 결과가 보인다.

### Sprint 2-4: UI 확장

1. 사용자 상세 분석 탭에 진행 로그 표시
2. 관리자 화면에 job 카운트 표시
3. 관리자 화면에 event timeline 표시
4. cancel-request 버튼 추가
5. 이어서 분석 관리자 기능 추가

완료 기준:

- RUNNING job의 진행 이벤트가 웹에서 보인다.
- 관리자 화면에서 실패 원인을 확인할 수 있다.

### Sprint 2-5: 운영화

1. `run_codex_app_server_worker_forever.ps1` 추가
2. loop 로그 저장
3. app-server health check
4. exec fallback 정책 결정
5. phase 2 보고서 작성

완료 기준:

- PowerShell 창 2개만 켜두면 동작한다.
- 하나는 app-server, 하나는 app-server worker다.
- 장애와 재시도 절차가 문서화되어 있다.

## 15. 운영 명령

터미널 1: 웹앱

```powershell
cd C:\Users\xogns\Documents\testAuction\court_auction_platform
.\run_fastapi.ps1
```

터미널 2: Codex app-server

```powershell
cd C:\Users\xogns\Documents\testAuction\court_auction_platform
codex app-server --listen ws://127.0.0.1:4500
```

터미널 3: app-server worker

```powershell
cd C:\Users\xogns\Documents\testAuction\court_auction_platform
.\run_codex_app_server_worker_forever.ps1 -Endpoint ws://127.0.0.1:4500 -Limit 1 -IdleSleepSeconds 10
```

fallback 터미널: 기존 exec worker

```powershell
.\run_cli_analysis_worker_forever.ps1 -Limit 1 -TimeoutSeconds 900 -IdleSleepSeconds 10
```

## 16. 검증 시나리오

### 시나리오 A: 정상 분석

1. 웹에서 상세 분석 요청
2. job 생성 확인
3. app-server worker가 RUNNING으로 변경
4. thread id 저장 확인
5. 이벤트 저장 확인
6. SUCCEEDED 확인
7. 웹 상세 분석 표시 확인

### 시나리오 B: app-server 미실행

1. app-server를 끈다.
2. job을 생성한다.
3. worker 실행
4. `APP_SERVER_UNAVAILABLE` 또는 연결 실패 기록 확인
5. retry 가능 여부 확인

### 시나리오 C: 취소

1. 긴 분석 job 생성
2. RUNNING 상태 확인
3. cancel-request 실행
4. worker가 interrupt 전송
5. CANCELED 저장 확인

### 시나리오 D: 이어서 분석

1. 완료된 job 선택
2. 관리자 화면에서 추가 지시 입력
3. 기존 thread id로 새 turn 실행
4. 결과가 추가 저장되는지 확인

## 17. 완료 후 작성 문서

2차 구현 완료 후 반드시 작성한다.

```text
reports/async_cli_analysis_phase_2_report.md
reports/codex_app_server_integration_report.md
reports/project_build_summary_and_next_instructions.md
```

포함 내용:

- 구현 범위
- app-server 실행 방법
- DB 변경
- API 변경
- UI 변경
- 검증 결과
- 실패 사례
- 남은 위험
- 다음 Sprint 지시

## 18. 최종 완료 기준

- `codex app-server`가 로컬에서 실행된다.
- app-server worker가 PENDING job을 처리한다.
- thread id와 turn id가 DB에 저장된다.
- 진행 이벤트가 DB에 저장된다.
- 웹앱에서 진행 로그를 볼 수 있다.
- 완료 결과가 `ai_analyses.detailed_analysis`에 저장된다.
- 취소 요청이 가능하다.
- 기존 `codex exec` worker fallback 경로가 유지된다.

