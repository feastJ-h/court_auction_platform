# 로컬 분석 워커 Runbook

## 권장 방식

```powershell
cd C:\Users\xogns\Documents\testAuction\court_auction_platform
.\run_local_analysis_app.ps1 -Limit 1 -TimeoutSeconds 900 -IdleSleepSeconds 10
```

이 명령은 Codex app-server와 app-server worker를 함께 다루는 로컬 운영 명령이다.

## Mock 검증

```powershell
.\run_local_analysis_app.ps1 -Limit 1 -Mock -RunOnce
```

Mock이 성공하면 다음이 정상이다.

```text
DB 연결
analysis_jobs 조회
worker heartbeat 기록
job 이벤트 기록
결과 파일 저장 경로
웹앱 상태 API
```

## Worker Heartbeat

관리자 화면과 `/api/local-analysis/status`에서 다음 정보를 확인한다.

```text
worker_id
worker_type
provider_mode
status
current_job_id
last_seen_at
status_message
pid
```

RUNNING 또는 STARTING 상태에서 10분 이상 heartbeat가 갱신되지 않으면 멈춤 가능성으로 표시된다.

## 분석하지 말아야 하는 문서 상태

다음 상태는 AI 분석 job으로 보내지 않는다.

```text
EMPTY_TEXT
OCR_REQUIRED
OCR_FAILED
HWP_CONVERSION_REQUIRED
HWP_CONVERSION_FAILED
TEXT_EXTRACTION_FAILED
PARSE_FAILED
MANUAL_REVIEW
```

이 상태는 OCR/HWP/수동 검수 흐름으로 먼저 보낸다.
