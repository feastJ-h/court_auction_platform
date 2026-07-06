# 로컬 CLI 분석 앱 / 웹앱 재연결 / 2026-06-15 이후 수집 진행 리포트

## 1. 구현된 주요 기능
- `run_local_analysis_app.ps1`를 표준 로컬 분석 앱 실행 명령으로 보강했다.
  - app-server가 이미 `ws://127.0.0.1:4500`에서 실행 중이면 재사용한다.
  - `-Mock` 모드에서는 app-server를 띄우지 않는다.
  - app-server 시작 실패 시 로그 파일 위치를 안내한다.
  - `-RunOnce` 옵션을 추가해 테스트 시 1회만 처리하고 종료할 수 있게 했다.
- 관리자 화면에 Local Analysis App 상태 배너를 추가했다.
  - app-server ON/OFF
  - PENDING/RUNNING job 수
  - 로컬 분석 앱 실행 필요 메시지
- `/api/local-analysis/status` API를 추가했다.
- `analysis_jobs.backup_path` 컬럼을 추가하고, 분석 완료 후 원본 문서 백업 경로를 job에 저장하도록 연결했다.
- 법원 수집기가 첫 페이지만 보지 않고 여러 페이지를 순회할 수 있도록 `max_pages` 기반 페이지네이션을 추가했다.
- `collect_since_2026_06_15.ps1`에 `-MaxPages` 옵션을 추가했다.
- 수집 실행 결과를 `reports/collection_since_2026_06_15_report.md`에 기록하도록 했다.
- 다운로드는 되었지만 DB에 아직 없는 격리소 파일을 법원에 다시 요청하지 않고 인입하는 `ingest_local_quarantine.ps1`를 추가했다.

## 2. 수집 및 인입 결과
- 소규모 실제 수집 테스트:
  - 명령: `collect_since_2026_06_15.ps1 -Limit 1 -MaxPages 1`
  - 결과: 다운로드 1건, 중복 스킵 1건
- 확장 수집:
  - 명령: `collect_since_2026_06_15.ps1 -Limit 50 -MaxPages 15`
  - 결과: 5분 실행 제한으로 중단됐지만, 중간 저장으로 `2026-06-30` 공고 10건 이상이 DB에 추가됐다.
- 로컬 격리소 인입:
  - 명령: `ingest_local_quarantine.ps1 -Limit 100`
  - 대상 파일: 46건
  - 새 DB 저장: 27건
  - 중복 스킵: 19건
  - 리포트: `reports/local_quarantine_ingest_report.md`

## 3. 최종 DB 상태
- raw_documents: 50건
- asset_events: 50건
- ai_analyses: 16건
- analysis_jobs: 13건
- 중복 raw_doc 이벤트: 0건

## 4. 최종 공고일 분포
- 2026-06-22: 2건
- 2026-06-24: 1건
- 2026-06-25: 4건
- 2026-06-26: 2건
- 2026-06-30: 10건
- 2026-07-01: 1건
- 2026-07-02: 1건
- 2026-07-03: 10건
- 2026-07-08: 1건
- 2026-07-09: 6건
- UNKNOWN: 12건

## 5. 품질 보정 내역
- 로컬 격리소 파일은 원 상세 페이지 작성일을 잃은 상태일 수 있으므로, PDF/HWP 본문에서 추출된 과거 사건일을 공고일로 오인하지 않게 보정했다.
- 로컬 인입 중 `2026-06-15` 이전으로 추출된 날짜는 `UNKNOWN`으로 정정했다.
- 정상 `AI_ANALYZED` 이벤트가 뒤늦게 생성된 원본 문서의 중복 `LOCAL_INGESTED` 이벤트 1건을 정리했다.

## 6. 검증 결과
- Python 문법 검증 통과:
  - `orchestrator.py`
  - `main_app.py`
  - `backend/crawler/scraper.py`
  - `backend/database/models.py`
  - `backend/database/session.py`
  - `backend/jobs/repository.py`
  - `backend/jobs/service.py`
  - `backend/analysis_worker/cli_worker.py`
  - `backend/analysis_worker/app_server_worker.py`
- JavaScript 문법 검증 통과:
  - `frontend/static/app.js`
- FastAPI TestClient:
  - `/admin` 200
  - `/user` 200
  - `/api/local-analysis/status` 200
- 로컬 분석 앱 mock 실행:
  - `run_local_analysis_app.ps1 -Limit 1 -Mock -RunOnce`
  - 결과: `{"processed": []}`
- 포트 상태:
  - `127.0.0.1:8000` 웹앱 실행 중
  - `127.0.0.1:4500` 닫힘
  - `0.0.0.0:8080` 닫힘

## 7. 사용자 실행 명령
```powershell
cd C:\Users\xogns\Documents\testAuction\court_auction_platform

# 웹앱
.\run_fastapi.ps1

# 로컬 분석 앱: app-server + worker loop
.\run_local_analysis_app.ps1 -Limit 1 -TimeoutSeconds 900 -IdleSleepSeconds 10

# 로컬 분석 앱 1회 테스트
.\run_local_analysis_app.ps1 -Limit 1 -Mock -RunOnce

# 2026-06-15 이후 수집
.\collect_since_2026_06_15.ps1 -Limit 50 -MaxPages 15

# 이미 다운로드된 격리소 파일 DB 인입
.\ingest_local_quarantine.ps1 -Limit 100
```

## 8. 다음 권장 작업
- 수집 파이프라인을 “다운로드 전체 완료 후 처리”가 아니라 “파일 1건 다운로드 즉시 DB 저장” 방식으로 바꾸면 장시간 실행 중단에도 유실 위험이 더 줄어든다.
- `LOCAL_INGESTED` 항목은 원 상세 페이지 메타데이터가 부족하므로, 추후 상세 URL 재매칭 또는 관리자 검수 큐가 필요하다.
- `UNKNOWN` 날짜 12건은 관리자 화면에서 별도 필터로 분리해 검수하는 것이 좋다.
