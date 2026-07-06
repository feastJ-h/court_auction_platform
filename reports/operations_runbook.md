# 운영 Runbook

## 기본 실행

```powershell
cd C:\Users\xogns\Documents\testAuction\court_auction_platform
.\run_fastapi.ps1
```

웹 접속:

```text
http://127.0.0.1:8000/user
http://127.0.0.1:8000/admin
```

## 로컬 분석 앱 실행

권장 실행:

```powershell
cd C:\Users\xogns\Documents\testAuction\court_auction_platform
.\run_local_analysis_app.ps1 -Limit 1 -TimeoutSeconds 900 -IdleSleepSeconds 10
```

검증용 mock:

```powershell
.\run_local_analysis_app.ps1 -Limit 1 -Mock -RunOnce
```

## 관리자에서 먼저 볼 것

1. `Local Analysis App` 카드
2. `worker` 수와 마지막 worker 감지 시간
3. 실패 Job 섹션
4. 오래 멈춘 RUNNING Job 섹션
5. Collection Quality 섹션의 UNKNOWN/LOCAL_INGESTED/파일 누락

## 장애 대응

분석 요청이 대기 중인데 처리되지 않을 때:

```powershell
.\run_local_analysis_app.ps1 -Limit 1 -Mock -RunOnce
```

Mock이 성공하면 앱 구조는 정상이고, 실제 Codex CLI/app-server 로그인 또는 네트워크 상태를 확인한다.

실패 Job이 있을 때:

1. 관리자 화면에서 실패 사유를 확인한다.
2. 원본 파일 열기 링크가 동작하는지 확인한다.
3. OCR_REQUIRED/MANUAL_REVIEW/PARSE_FAILED 문서는 분석 재시도보다 문서 처리 상태를 먼저 확인한다.
4. 재시도 가능한 Job은 관리자 화면의 `재시도` 버튼을 사용한다.

## 포트 확인

```powershell
netstat -ano | findstr :8000
netstat -ano | findstr :4500
```

8000은 FastAPI, 4500은 Codex app-server 용도다.
