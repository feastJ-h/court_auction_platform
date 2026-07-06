# 관리자 운영 화면 및 분석 가시성 보강 지시서

## 1. 목적

웹앱은 계속 켜두고, 분석은 로컬 CLI 분석 앱이 비동기로 처리하는 구조다. 따라서 운영자는 관리자 화면에서 다음을 즉시 확인할 수 있어야 한다.

- 로컬 분석 앱이 켜져 있는지
- 분석 요청이 큐에 들어갔는지
- 어떤 물건이 분석 대기/진행/완료/실패 상태인지
- 기본 분석과 상세 분석 내용이 각각 무엇인지
- 실패한 경우 어떤 사유로 실패했는지
- 사용자 화면에서 분석 완료 물건이 먼저 보이는지

## 2. 이번 변경 기준

### 기본 분석 도구

기본 분석 provider는 `chatgpt`로 변경한다.

변경 대상:

```text
runtime_settings.json
backend/config.py
backend/runtime_settings.py
backend/database/models.py
backend/database/crud.py
```

주의:

- `chatgpt` 기본값은 신규 기본 분석에 적용된다.
- 기존에 저장된 Gemini 분석 결과는 그대로 보존한다.
- API 키가 없는 경우 기본 분석은 실패할 수 있으나, 상세 분석은 로컬 Codex CLI/app-server 워커로 처리할 수 있다.

### 사용자 화면 정렬

사용자 화면 목록은 다음 순서로 정렬한다.

```text
1. 상세 분석 완료 물건
2. 상세 분석 미완료 물건
3. 각 그룹 안에서는 법원 등록일 최신순
4. 같은 등록일이면 내부 id 오름차순
```

목표:

- 분석이 완료된 물건은 앞쪽에서 바로 확인한다.
- 분석이 안 된 물건은 뒤쪽으로 밀어 운영자가 큐 처리 대상으로 볼 수 있게 한다.
- 법원 등록 순서 흐름은 유지한다.

### 관리자 화면

관리자 화면에는 다음 영역을 둔다.

```text
상단 요약
  - 전체 물건 수
  - 대기/진행/완료/실패 job 수

로컬 분석 앱 상태
  - app-server ON/OFF
  - 대기/진행/실패 수
  - 실행 명령

기본 분석 도구
  - ChatGPT/Gemini 선택
  - ChatGPT 설정 여부

물건별 운영 카드
  - 기본 정보
  - 기본 분석 내용
  - 상세 분석 내용
  - 상세 분석 job 상태
  - 최근 job 이벤트
  - 실패 사유
  - 취소 요청
```

## 3. 운영 방식

### 웹앱

```powershell
cd C:\Users\xogns\Documents\testAuction\court_auction_platform
.\run_fastapi.ps1
```

### 로컬 분석 앱

```powershell
cd C:\Users\xogns\Documents\testAuction\court_auction_platform
.\run_local_analysis_app.ps1 -Limit 1 -TimeoutSeconds 900 -IdleSleepSeconds 10
```

### 상태 확인

관리자 화면:

```text
http://127.0.0.1:8000/admin
```

웹앱은 분석을 직접 실행하지 않는다. 분석 요청은 `analysis_jobs` 큐에 들어가고, 로컬 분석 앱이 실행 중일 때 처리된다.

## 4. 운영 안정화 추가 개발 권장

### 4.1 관리자 화면 자동 갱신 개선

현재는 대기/진행 작업이 있을 때 일정 시간 후 새로고침하는 방식이다. 다음 단계에서는 `/api/local-analysis/status`와 `/api/analyze/jobs/{job_id}/events`를 이용해 화면 일부만 갱신한다.

### 4.2 워커 헬스체크

app-server 포트만 열려 있어도 worker loop가 멈췄을 수 있다. 다음 필드를 추가하는 것을 권장한다.

```text
analysis_worker_heartbeats
  id
  worker_type
  last_seen_at
  current_job_id
  status_message
```

### 4.3 분석 결과 버전 관리

상세 분석을 여러 번 수행할 수 있으므로, 최신 결과만 `ai_analyses.detailed_analysis`에 두고 과거 결과는 별도 테이블에 보관한다.

```text
analysis_outputs
  id
  job_id
  event_id
  output_json_path
  output_markdown_path
  markdown_report
  created_at
```

### 4.4 mock/실제 분석 구분

개발 중 mock 분석과 실제 Codex 분석이 섞일 수 있다. 다음 필드를 명확히 기록한다.

```text
analysis_jobs.execution_mode
  mock
  codex_exec
  codex_app_server
```

### 4.5 크롤링/분석/웹앱 분리

장기 운영 구조:

```text
crawler tool
  - 법원 공고 수집
  - PDF/HWP 다운로드
  - DB 저장

analysis app
  - 로컬 Codex CLI/app-server
  - 큐 처리
  - 결과 저장

web app
  - 상태 표시
  - 결과 조회
  - 관리자 운영
```

## 5. 완료 기준

- 관리자 화면에서 분석 진행 여부를 확인할 수 있다.
- 관리자 화면에서 기본 분석과 상세 분석 내용을 각각 볼 수 있다.
- 관리자 화면에서 실패 사유와 최근 이벤트를 볼 수 있다.
- 기본 provider가 ChatGPT로 설정되어 있다.
- 사용자 화면은 상세 분석 완료 물건을 먼저 보여준다.
- 상세 분석 미완료 물건은 뒤쪽으로 정렬된다.
- 문서와 운영 명령이 다음 작업자가 이어받을 수 있게 정리되어 있다.

