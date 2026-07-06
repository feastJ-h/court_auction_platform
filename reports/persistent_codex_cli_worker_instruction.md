# 상시 Codex CLI 워커 운영 및 웹앱 연동 지시서

## 1. 결론

로그인된 Codex CLI를 이용해 웹앱의 상세 분석을 처리하는 것은 가능하다. 단, 사람이 보는 대화형 CLI 화면을 웹앱이 직접 조작하는 방식으로 구현하지 않는다. 웹앱과 CLI는 DB와 파일 저장소를 통해 데이터를 주고받고, CLI는 상시 켜둔 워커 프로세스가 `analysis_jobs`의 대기 작업을 가져가 처리하는 구조로 만든다.

권장 순서:

1. 1차: PowerShell 창을 열어 `codex exec` 워커 루프를 상시 실행한다.
2. 2차: `codex app-server`를 상시 실행하고 웹앱/워커가 JSON-RPC로 통신한다.

## 2. 가능한 방식과 비권장 방식

### 권장: 상시 워커 창

별도 PowerShell 창을 켜두고 다음 흐름으로 운영한다.

```text
웹앱
  -> analysis_jobs에 PENDING 작업 생성
  -> 화면에서는 3초마다 상태 조회

상시 CLI 워커
  -> PENDING 작업 조회
  -> input.md 생성
  -> codex exec 실행
  -> output.json/output.md 저장
  -> DB를 SUCCEEDED 또는 FAILED로 갱신

웹앱
  -> 완료된 detailed_analysis 표시
```

### 권장: Codex app-server

2차 구현에서는 `codex app-server`를 상시 실행한다. 이 방식은 thread, turn, 진행 이벤트, 중단, 추가 지시를 웹앱과 연결하기 좋다.

```text
웹앱/워커
  -> app-server JSON-RPC 연결
  -> thread/start
  -> turn/start
  -> 이벤트 스트림 수신
  -> 결과 저장
```

### 비권장: 대화형 CLI 화면 직접 조작

대화형 `codex` 화면을 띄워두고 웹앱이 키 입력을 보내거나 화면 텍스트를 긁어오는 방식은 사용하지 않는다.

이유:

- 화면 포커스와 입력 타이밍에 취약하다.
- 결과 파싱이 어렵다.
- 실패/재시도/취소 상태를 DB와 일관되게 맞추기 어렵다.
- 운영 자동화에 적합하지 않다.

## 3. ChatGPT 로그인 기반 사용 가능 여부

Codex CLI는 OpenAI 모델 사용 시 두 가지 인증 방식을 지원한다.

- ChatGPT 로그인 기반 구독 접근
- API key 기반 사용량 과금 접근

현재 목표는 API 비용을 줄이고 로그인된 ChatGPT/Codex 계정을 활용하는 것이므로, CLI는 ChatGPT 로그인 상태를 재사용하는 방향으로 둔다.

주의:

- 이것은 ChatGPT 웹사이트를 조작하는 것이 아니다.
- Codex CLI가 저장된 로그인 세션을 사용해 모델 호출을 수행하는 구조다.
- 로그인 정보는 로컬에 캐시되므로 비밀번호처럼 취급한다.
- 워커는 신뢰된 로컬 PC 또는 내부 서버에서만 실행한다.

## 4. 현재 프로젝트 기준 실행 위치

워커는 반드시 프로젝트 루트에서 실행한다.

```powershell
cd C:\Users\xogns\Documents\testAuction\court_auction_platform
```

이 위치에서 실행해야 다음 경로가 맞는다.

```text
auction_data.db
storage/raw_quarantine/
storage/processed/
storage/analysis_jobs/
backend/
```

## 5. 현재 구현 상태

현재 구조:

- 웹앱은 상세 분석 버튼 클릭 시 job을 생성한다.
- 프론트엔드는 job 상태를 3초마다 조회한다.
- `run_cli_analysis_worker.ps1`는 대기 job을 처리하는 1회성 워커다.
- 기본값은 `Limit = 1`, `TimeoutSeconds = 900`이다.
- 따라서 현재는 워커를 한 번 실행하면 PENDING job 1개만 처리하고 종료한다.

현재 방식으로 1개 처리:

```powershell
.\run_cli_analysis_worker.ps1
```

3개 처리:

```powershell
.\run_cli_analysis_worker.ps1 -Limit 3
```

테스트/mock 처리:

```powershell
.\run_cli_analysis_worker.ps1 -Limit 3 -Mock
```

실제 Codex 분석을 하려면 `-Mock`을 붙이지 않는다.

## 6. 1차 구현: 상시 워커 루프

### 6.1 목표

PowerShell 창 하나를 계속 켜두면, 웹앱에서 생성되는 PENDING 작업이 자동으로 처리되게 한다.

### 6.2 추가할 실행 스크립트

새 파일:

```text
run_cli_analysis_worker_forever.ps1
```

권장 내용:

```powershell
param(
    [int]$Limit = 1,
    [int]$TimeoutSeconds = 900,
    [int]$IdleSleepSeconds = 10,
    [string]$CodexCommand = "codex",
    [switch]$Mock
)

$ErrorActionPreference = "Continue"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

while ($true) {
    $startedAt = Get-Date
    Write-Host "[$startedAt] Checking pending Codex CLI analysis jobs..."

    try {
        $arguments = @(
            "-ExecutionPolicy", "Bypass",
            "-File", ".\run_cli_analysis_worker.ps1",
            "-Limit", $Limit,
            "-TimeoutSeconds", $TimeoutSeconds,
            "-CodexCommand", $CodexCommand
        )

        if ($Mock) {
            $arguments += "-Mock"
        }

        powershell @arguments
    }
    catch {
        Write-Host "Worker loop error: $($_.Exception.Message)"
    }

    Start-Sleep -Seconds $IdleSleepSeconds
}
```

### 6.3 실행 방법

운영용 PowerShell 창을 하나 열고 다음을 실행한다.

```powershell
cd C:\Users\xogns\Documents\testAuction\court_auction_platform
.\run_cli_analysis_worker_forever.ps1 -Limit 1 -TimeoutSeconds 900 -IdleSleepSeconds 10
```

이 창을 켜두면 웹앱에서 새 job이 생길 때마다 최대 10초 안에 워커가 확인한다.

### 6.4 동작 방식

```text
1. 웹앱에서 분석 요청
2. analysis_jobs.status = PENDING
3. 워커 루프가 10초마다 실행
4. run_cli_analysis_worker.ps1 실행
5. cli_worker.py가 PENDING job 1개 조회
6. status = RUNNING
7. storage/analysis_jobs/{job_id}/input.md 생성
8. codex exec 실행
9. output.json / output.md / stderr.log 저장
10. ai_analyses.detailed_analysis 저장
11. status = SUCCEEDED
12. 웹앱 폴링이 완료 상태 확인
```

## 7. Codex CLI 실제 분석 호출

워커 내부에서는 다음과 같은 형태로 실행한다.

```powershell
codex exec --json --sandbox workspace-write --output-schema .\backend\analysis_worker\schemas\deep_analysis.schema.json --output-last-message storage\analysis_jobs\{job_id}\codex_last_message.json "storage/analysis_jobs/{job_id}/input.md 파일을 읽고 법원 회생/파산 매각 물건의 상세 분석 JSON을 작성하라."
```

핵심 원칙:

- 입력 본문을 명령줄에 길게 넣지 않는다.
- `input.md` 파일에 분석 자료를 모은다.
- `--output-schema`로 JSON 구조를 강제한다.
- 최종 메시지는 파일로 저장한다.
- `stderr.log`를 남겨 실패 원인을 추적한다.

## 8. 웹앱과 데이터 교환 방식

웹앱과 CLI는 직접 소켓으로 대화하지 않는다. 1차 구현에서는 DB와 파일을 교환 매체로 사용한다.

웹앱이 쓰는 데이터:

```text
analysis_jobs
  - id
  - event_id
  - status
  - requested_at
  - started_at
  - finished_at
  - error_code
  - error_message
```

워커가 쓰는 파일:

```text
storage/analysis_jobs/{job_id}/input.md
storage/analysis_jobs/{job_id}/output.json
storage/analysis_jobs/{job_id}/output.md
storage/analysis_jobs/{job_id}/stderr.log
storage/analysis_jobs/{job_id}/codex_last_message.json
```

웹앱이 최종 표시하는 데이터:

```text
ai_analyses.detailed_analysis
```

## 9. 2차 구현: app-server 상시 연결

### 9.1 app-server를 쓰는 이유

`codex exec`는 job 단위 실행에 좋다. 하지만 다음 기능이 필요하면 `codex app-server`가 더 적합하다.

- 진행 로그 실시간 표시
- 하나의 thread를 유지한 후속 분석
- 분석 도중 추가 지시
- 취소/중단 이벤트 처리
- Codex 이벤트 저장

### 9.2 실행 방식

로컬 전용으로 실행한다.

```powershell
cd C:\Users\xogns\Documents\testAuction\court_auction_platform
codex app-server --listen ws://127.0.0.1:4500
```

보안상 외부 IP에 직접 열지 않는다. 원격 노출이 필요하면 capability token 또는 signed bearer token 인증을 먼저 붙인다.

### 9.3 추가 구현 파일

```text
backend/analysis_worker/app_server_client.py
backend/analysis_worker/app_server_worker.py
backend/analysis_worker/event_stream.py
run_codex_app_server_worker.ps1
run_codex_app_server.ps1
```

### 9.4 DB 확장

`analysis_jobs` 추가 필드:

```text
codex_thread_id
codex_turn_id
progress_message
progress_percent
last_event_at
cancel_requested
```

새 테이블:

```text
analysis_job_events
  id
  job_id
  event_type
  event_payload
  created_at
```

### 9.5 app-server 처리 흐름

```text
1. app-server 실행
2. 워커가 websocket 연결
3. initialize
4. initialized
5. thread/start 또는 thread/resume
6. turn/start
7. item/started, item/completed, agentMessage/delta 이벤트 수신
8. analysis_job_events에 저장
9. 최종 응답 파싱
10. ai_analyses.detailed_analysis 저장
11. analysis_jobs.status = SUCCEEDED
```

## 10. 운영 확인 방법

### 10.1 대기 작업 확인

```powershell
cd C:\Users\xogns\Documents\testAuction\court_auction_platform
& 'C:\Users\xogns\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -c "import sqlite3; con=sqlite3.connect('auction_data.db'); con.row_factory=sqlite3.Row; [print(dict(r)) for r in con.execute('select id,event_id,status,requested_at,started_at,finished_at,error_code,error_message from analysis_jobs order by id')]"
```

### 10.2 결과 파일 확인

```powershell
Get-ChildItem -Recurse .\storage\analysis_jobs | Sort-Object LastWriteTime -Descending | Select-Object -First 20
```

### 10.3 웹앱 표시 확인

웹앱은 `ai_analyses.detailed_analysis`가 비어 있지 않으면 상세 분석 완료로 표시한다.

```text
상세 분석 완료 표시 수 = detailed_analysis가 있는 ai_analyses 수
job 완료 수 = analysis_jobs.status가 SUCCEEDED인 수
```

두 숫자는 항상 같지 않을 수 있다. 기존 Gemini 상세 분석 또는 수동 저장 결과가 있을 수 있기 때문이다.

## 11. 예상 소요 시간

테스트/mock:

```text
1초 이내
```

실제 `codex exec`:

```text
짧은 텍스트: 1~3분
일반 PDF/HWP 추출 텍스트: 3~10분
긴 문서 또는 복잡한 권리 분석: 10~15분
```

현재 기본 제한:

```text
TimeoutSeconds = 900초 = 15분
```

15분을 넘기면 `CLI_TIMEOUT`으로 실패 처리한다.

## 12. 구현 체크리스트

1. `run_cli_analysis_worker_forever.ps1` 추가
2. 워커 루프 로그 파일 저장 기능 추가
3. 관리자 화면에 워커 실행 안내 추가
4. 관리자 화면에 PENDING/RUNNING/FAILED job 수 표시
5. `-Mock` 실행 결과와 실제 Codex 실행 결과를 UI에서 구분
6. 실제 Codex 실행 시 한글 프롬프트 인코딩 점검
7. `codex` 명령이 PATH에서 잡히지 않을 때 명확한 오류 표시
8. app-server 2차 구현 전까지는 DB+파일 교환 방식을 유지

## 13. 권장 운영 명령

웹앱:

```powershell
cd C:\Users\xogns\Documents\testAuction\court_auction_platform
.\run_fastapi.ps1
```

상시 Codex CLI 워커:

```powershell
cd C:\Users\xogns\Documents\testAuction\court_auction_platform
.\run_cli_analysis_worker_forever.ps1 -Limit 1 -TimeoutSeconds 900 -IdleSleepSeconds 10
```

대량 대기 job 등록:

```powershell
.\enqueue_deep_analysis_jobs.ps1 -Limit 20
```

대기 job 3개만 즉시 처리:

```powershell
.\run_cli_analysis_worker.ps1 -Limit 3 -TimeoutSeconds 900
```

## 14. 최종 권장안

현재 단계에서는 대화형 CLI 화면을 켜두는 방식이 아니라, PowerShell 창에 상시 워커 루프를 띄워두는 방식으로 구현한다.

이후 웹앱에서 진행 로그와 추가 지시가 필요해지면 `codex app-server`를 도입한다.

따라서 구현 우선순위는 다음과 같다.

1. `run_cli_analysis_worker_forever.ps1` 구현
2. 실제 Codex CLI 분석 1건 검증
3. 관리자 화면에 워커 상태와 job 카운트 표시
4. 실패/타임아웃 로그 정리
5. `codex app-server` 2차 확장

