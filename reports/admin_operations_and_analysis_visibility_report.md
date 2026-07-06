# 관리자 운영 화면 및 분석 가시성 보강 리포트

## 1. 구현된 주요 기능
- 기본 분석 provider를 `chatgpt`로 정리했다.
  - `.env`: `ANALYSIS_PROVIDER=chatgpt`
  - `runtime_settings.json`: `chatgpt`
  - `backend/config.py` 기본값: `chatgpt`
  - `backend/database/models.py` 신규 `AiAnalysis.analysis_provider` 기본값: `chatgpt`
  - `backend/database/crud.py` 신규 분석 저장 기본값: `chatgpt`
- 사용자 화면 목록 정렬을 상세 분석 완료 우선으로 변경했다.
  - 1순위: 상세 분석 완료
  - 2순위: 상세 분석 미완료
  - 그룹 내부: 법원 등록일 최신순
  - 동일 등록일: 내부 id 오름차순
- 관리자 화면을 운영 카드형 구조로 정리했다.
  - 전체 물건 수
  - 대기/진행/완료/실패 job 수
  - Local Analysis App 상태
  - 기본 분석 도구 선택
  - 물건별 기본 분석
  - 물건별 상세 분석
  - 상세 분석 job 상태
  - 최근 job 이벤트
  - 실패 사유
  - 취소 요청
  - 실패/취소 job 재시도 버튼
- `analysis_jobs.execution_mode` 컬럼을 추가했다.
  - `mock`
  - `codex_exec`
  - `codex_app_server`
- 기존 job의 `execution_mode`을 마이그레이션 시 자동 보정했다.

## 2. 운영 상태
- 웹앱:
  - `http://127.0.0.1:8000`
  - `/admin` 200
  - `/user` 200
  - `/api/local-analysis/status` 200
- Codex app-server:
  - `ws://127.0.0.1:4500`
  - 현재 ON 상태
- Local Analysis App 상태 API:
  - state: `failed`
  - message: 실패한 분석 작업이 있으므로 실패 사유 확인 및 재시도 필요
  - pending_jobs: 0
  - running_jobs: 0
  - failed_jobs: 4

## 3. 현재 DB 상태
- raw_documents: 50건
- asset_events: 50건
- ai_analyses: 16건
- analysis_jobs: 13건

## 4. 분석 job 상태
- SUCCEEDED: 8건
- FAILED: 4건
- CANCELED: 1건

## 5. 실행 모드 분포
- codex_app_server: 3건
- codex_exec: 3건
- mock: 7건

## 6. 검증 결과
- Python 문법 검증 통과:
  - `main_app.py`
  - `backend/config.py`
  - `backend/runtime_settings.py`
  - `backend/database/models.py`
  - `backend/database/session.py`
  - `backend/database/crud.py`
  - `backend/jobs/repository.py`
  - `backend/jobs/service.py`
  - `backend/analysis_worker/cli_worker.py`
  - `backend/analysis_worker/app_server_worker.py`
- JavaScript 문법 검증 통과:
  - `frontend/static/app.js`
- DB 마이그레이션 확인:
  - `analysis_jobs.execution_mode` 컬럼 생성
  - 기존 job execution mode 보정
  - 빈 execution mode 0건
- 사용자 화면 정렬 확인:
  - 첫 페이지 상단에 상세 분석 완료 물건이 먼저 노출됨
- 관리자 화면 HTML 확인:
  - 기본 분석 문구 표시
  - 상세 분석 문구 표시
  - 실패 문구 표시
  - 재시도 버튼 표시
  - 최근 이벤트 영역 표시

## 7. 관리자 운영 명령
```powershell
cd C:\Users\xogns\Documents\testAuction\court_auction_platform

# 웹앱 실행
.\run_fastapi.ps1

# 로컬 분석 앱 실행
.\run_local_analysis_app.ps1 -Limit 1 -TimeoutSeconds 900 -IdleSleepSeconds 10

# 로컬 분석 앱 1회 mock 테스트
.\run_local_analysis_app.ps1 -Limit 1 -Mock -RunOnce
```

## 8. 다음 권장 작업
- 실패 job 4건의 오류 원인을 관리자 화면에서 확인한 뒤 재시도 또는 취소/보류 정책을 결정한다.
- worker heartbeat 테이블을 추가하면 app-server 포트 ON/OFF뿐 아니라 worker loop 생존 여부까지 표시할 수 있다.
- 상세 분석 결과 버전 관리를 위해 `analysis_outputs` 테이블을 추가하는 것이 좋다.
