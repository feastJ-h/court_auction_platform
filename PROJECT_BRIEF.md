## Service Boundary Update - 2026-07-05
- Public auction and ONBID web routes are now registered from `backend/web/routers/auctions.py`.
- `main_app.py` should remain the app bootstrap and legacy route holder while each domain is extracted gradually.
- ONBID changes should start from:
  - `backend/web/routers/auctions.py` for web/API routes
  - `backend/onbid/client.py` for external API calls
  - `backend/workers/onbid_sync.py` for collection flow
  - `backend/services/auction_items.py` for persistence, matching, and serialization
- The refactoring guide is `docs/service_boundary_refactoring_plan.md`.
- Next extraction order: admin operations, recovery case user routes, analysis APIs, shared web dependencies.
# Court Auction Platform 프로젝트 브리프

## 목적
법원 회생/파산 부동산 공고와 첨부 문서를 수집하고, 텍스트 추출/OCR/AI 분석을 통해 사용자와 관리자가 물건을 검토할 수 있는 로컬 우선 웹 플랫폼이다.

## 현재 구조
- `main_app.py`: FastAPI 웹 서버, 사용자/관리자 라우팅
- `backend/database`: SQLAlchemy 모델, CRUD, SQLite 세션
- `backend/crawler`: 법원 게시판 수집
- `backend/parser`: PDF/HWP 텍스트 추출과 PII 옵션 처리
- `backend/ai_engine`: Gemini/ChatGPT 계열 기본 분석
- `backend/jobs`: 상세 분석 job, OCR job, worker heartbeat
- `backend/ocr`: 무료 로컬 OCR 엔진 어댑터
- `frontend/templates`: Jinja2 사용자/관리자 화면
- `storage/raw_quarantine`: 원본 파일 격리 저장소
- `storage/processed`: 파싱/OCR/분석 결과 저장소
- `reports`: 스프린트 결과 리포트

## 핵심 DB 개념
- `RawDocument`: 다운로드/격리된 원본 파일
- `Asset`: 변하지 않는 물건 정보
- `AssetEvent`: 사건/공고 단위 상태, 파싱 텍스트, 날짜
- `AiAnalysis`: 기본/상세 분석 대표 결과
- `AnalysisResult`: 모델별 분석 결과 저장
- `AnalysisJob`: 상세 분석과 OCR 작업 큐
- `AnalysisReview`: 관리자 분석 품질 검수
- `UserEventAction`: 관심/지켜보기/패스
- `UserEventNote`: 사용자별 메모/태그
- `AuditLog`: 운영 감사 로그
- `CrawlRun`: 정기/수동/보정 수집 실행 이력

## 현재 운영 수집 정책
- 정기 수집 실행: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_scheduled_crawl.ps1`
- 안전 검증: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_scheduled_crawl.ps1 -DryRun`
- 기본 범위: 최근 14일, `Limit=50`, `MaxPages=15`
- 보정 수집: `.\run_scheduled_crawl.ps1 -RunType backfill -StartDate 2026-06-15 -Limit 50 -MaxPages 15`
- 실행 이력: `crawl_runs`
- 운영 화면: `/admin/collection`
- 로그 위치: `storage/logs/crawl_runs`
- 중복 실행 방지: `storage/scheduled_crawl.lock`

## 현재 온비드 공매 MVP
- 사용자/관리자 조회 화면: `/auctions`, `/auctions/{auction_item_id}`
- 관리자 샘플 수집 API: `POST /api/admin/auctions/onbid/sync?sample=true`
- 관리자 실제 수집 API: `POST /api/admin/auctions/onbid/sync?sample=false`
- 수동 사건 연결 API: `POST /api/admin/auctions/{auction_item_id}/links`
- 실행 스크립트: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_onbid_sync.ps1 -Sample`
- 실제 API 실행: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_onbid_sync.ps1 -Limit 20`
- DB 테이블: `auction_items`, `auction_item_snapshots`, `auction_notices`, `auction_results`, `case_auction_links`, `auction_alerts`
- 주요 서비스: `backend/services/auction_items.py`
- API 클라이언트 경계: `backend/onbid/client.py`
- 현재 실제 온비드 API 키가 없으면 샘플 데이터로 동작한다.
- 실제 API 설정값: `ONBID_API_KEY`, `ONBID_API_BASE_URL=https://apis.data.go.kr/B010003/OnbidRlstListSrvc2`
- 실제 오퍼레이션: `/getRlstCltrList2`
- 필수 파라미터: `serviceKey`, `pageNo`, `numOfRows`, `resultType=json`, `prptDivCd`, `pvctTrgtYn`
- 2026-07-05 실제 호출 확인 결과: HTTP 401. 공공데이터포털 키 활성화/승인 또는 인코딩 키 형식 확인 필요.

## 현재 OCR 정책
- 무료 기본 엔진: Tesseract OCR
- 실제 OCR 성공 상태: `OCR_PARSED`
- 개발용 mock OCR 상태: `OCR_MOCKED`
- OCR 필요 상태: `OCR_REQUIRED`
- `OCR_PARSED` 문서는 분석 가능 상태로 간주한다.
- OCR 완료 후 AI 분석은 자동 비용 발생을 피하기 위해 관리자/기존 분석 요청 흐름으로 연결한다.
- 실행:
  - 상태 점검: `.\run_ocr_worker.ps1 -Limit 1 -DryRun`
  - 실제 OCR: `.\run_ocr_worker.ps1 -Limit 1 -Enqueue`
  - mock OCR: `.\run_ocr_worker.ps1 -Limit 1 -Enqueue -Mock`

## 현재 로그인
- 기본 관리자: `admin`
- 기본 비밀번호: `admin1234!`
- 운영 전 반드시 관리자 화면 또는 `/account/password`에서 변경 권장

## 개발 시 토큰 절약 규칙
- 전체 파일을 매번 읽지 않는다.
- 기능별 진입점만 읽는다.
  - OCR: `backend/ocr`, `backend/jobs/ocr_service.py`, `run_ocr_worker.ps1`
  - 관리자 UI: `main_app.py`, `frontend/templates/admin/dashboard.html`
  - 사용자 UI: `frontend/templates/user`, `frontend/static/app.js`
  - DB: `backend/database/models.py`, 필요한 CRUD/service 파일
- 변경 전후에는 관련 파일만 문법 검사한다.
