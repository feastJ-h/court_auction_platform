# PROJECT_CONTEXT.md

## 1. 프로젝트 목표

법원 회생/파산 공고와 온비드 공매 데이터를 수집하고, 로컬 저장소/SQLite DB/AI 분석/관리자 검수/사용자 UI를 연결해 상용 서비스 수준의 자산 분석 플랫폼으로 발전시키는 것이 목표다.

핵심 방향:
- 회생/파산 사건과 공매 물건을 각각 독립 도메인으로 관리한다.
- 법원 원문 파일과 추출 텍스트는 로컬에 안전하게 보관한다.
- Gemini, ChatGPT/Codex 계열 분석을 선택적으로 사용할 수 있는 구조를 유지한다.
- 외부 데이터는 오염 가능성이 있다고 보고, 파일 경로/PII/가짜 다운로드/API 실패를 우선 방어한다.
- `main_app.py`를 점점 얇게 만들고, 기능별 라우터/서비스 경계를 명확히 나눈다.

## 2. 현재까지 완료된 작업

### 기본 플랫폼
- FastAPI + Jinja2 + SQLite 기반 웹 앱 구축.
- 사용자/관리자 로그인, 역할 기반 메뉴, 사용자 대시보드 구성.
- 법원 공고 수집/파싱/OCR/AI 분석/관리자 검수 흐름 구축.
- Tesseract OCR 연동 기반 마련.
- Gemini/ChatGPT/Codex 계열 분석 모드 선택 구조 마련.

### 온비드 공매
- 온비드 부동산 물건목록 조회 API 연동.
- 실제 API 키 활성화 확인 완료.
- 실제 API 5건 호출 성공:
  - `fetched=5`
  - 첫 호출 `inserted=5`
  - 재호출 `inserted=0`, `duplicates=5`
  - `used_sample=False`
- 온비드 전체 응답 건수 예시: `62045`.
- 같은 물건의 여러 입찰 회차 구분을 위해 `onbid_cltr_no`, `pbct_no`, `pbct_nsq` 추가.
- 온비드 목록/상세 UI에 PBCT/회차 식별 정보 표시.

### 라우터 분리
`main_app.py`에서 기능별 라우터로 분리 완료:
- 공매/온비드: `backend/web/routers/auctions.py`
- 관리자 사용자 관리: `backend/web/routers/admin_users.py`
- 관리자 운영 화면: `backend/web/routers/admin_operations.py`
- 회생/파산 사용자 화면 및 사용자 액션: `backend/web/routers/cases.py`
- 분석 API 및 분석 job API: `backend/web/routers/analysis.py`
- OCR 운영 API: `backend/web/routers/ocr_operations.py`
- 원문 문서 제공: `backend/web/routers/documents.py`
- 공통 웹 의존성/타입/헬퍼: `backend/web/dependencies.py`

### 테스트/검증
- 라우터 누락/중복 등록 방지 테스트 추가: `tests/router_boundary_test.py`
- 주요 페이지 응답 스모크 테스트 추가: `tests/page_response_smoke_test.py`
- 기존 회귀 테스트 유지:
  - `tests/onbid_module_test.py`
  - `tests/isolated_operations_test.py`
- 최근 확인된 통과 항목:
  - 문법 검사 통과
  - 라우터 경계 테스트 통과
  - 페이지 응답 스모크 테스트 통과
  - 온비드 샘플/공매 연결 테스트 통과
  - 사용자 액션/OCR/basic analysis guard 테스트 통과
- 로컬 서버 실행 확인:
  - `http://127.0.0.1:8000`
  - `/login` 200
  - `/user`, `/admin`, `/auctions`는 비로그인 시 303 로그인 리다이렉트
  - `/api/local-analysis/status` 200

### 문서/리포트
최근 주요 리포트:
- `reports/sprint_real_onbid_quality_report.md`
- `reports/sprint_admin_operations_router_report.md`
- `reports/sprint_case_router_report.md`
- `reports/sprint_analysis_router_report.md`
- `reports/sprint_shared_web_dependencies_report.md`
- `reports/sprint_ocr_documents_page_smoke_report.md`

서비스 경계 문서:
- `docs/service_boundary_refactoring_plan.md`

## 3. 변경된 파일 목록

핵심 변경 파일:
- `main_app.py`
- `backend/database/models.py`
- `backend/database/session.py`
- `backend/onbid/client.py`
- `backend/services/auction_items.py`
- `backend/web/dependencies.py`
- `backend/web/routers/admin_operations.py`
- `backend/web/routers/admin_users.py`
- `backend/web/routers/analysis.py`
- `backend/web/routers/auctions.py`
- `backend/web/routers/cases.py`
- `backend/web/routers/documents.py`
- `backend/web/routers/ocr_operations.py`
- `frontend/templates/auctions/index.html`
- `frontend/templates/auctions/detail.html`
- `tests/router_boundary_test.py`
- `tests/page_response_smoke_test.py`
- `docs/service_boundary_refactoring_plan.md`
- `PROJECT_CONTEXT.md`

관련 실행 스크립트:
- `run_onbid_sync.ps1`
- `start_fastapi_background.ps1`
- `stop_fastapi.ps1`
- `run_ocr_worker.ps1`
- `run_scheduled_crawl.ps1`

## 4. 아직 남은 작업

우선순위 높은 다음 작업:
1. 계정/비밀번호/사용자 설정 라우터 분리
   - `/account/password`
   - `/user/settings`
   - 필요 시 로그인/로그아웃 라우트까지 `auth.py` 또는 `account.py`로 분리

2. 관리자 메타데이터 보정 라우터 분리
   - `/admin/events/{event_id}/metadata`
   - 관리자 운영 또는 case moderation 라우터로 이동

3. DB 마이그레이션 관리 체계 정리
   - 현재는 SQLite용 수동 `ALTER TABLE` 보정이 `backend/database/session.py`에 있음
   - 추후 Alembic 또는 `docs/migration_ledger.md` 필요

4. 페이지/폼 단위 스모크 테스트 확장
   - 관리자 사용자 생성/권한 변경
   - 관리자 메타데이터 수정
   - OCR enqueue
   - 공매 실제 API 버튼/샘플 버튼

5. 한글 인코딩 깨짐 정리
   - 일부 기존 샘플 텍스트/템플릿/테스트 문자열이 깨져 있음
   - 기능에는 큰 영향은 없지만 UI 품질 개선 필요

6. 온비드 실제 API 확장 수집
   - 현재 5건 검증 완료
   - 다음에는 페이지 단위 수집, 날짜/상태 필터, 중복/회차 정책 고도화 필요

## 5. 현재 발생 중인 오류/이슈

현재 치명적인 런타임 오류는 없음.

알려진 이슈:
- FastAPI TestClient 실행 시 Starlette `httpx` deprecation warning 발생.
  - 테스트 실패는 아니며 현재 기능에는 영향 없음.
- 일부 한글 문자열이 깨져 보이는 파일이 있음.
  - 특히 오래된 템플릿/샘플 데이터/테스트 문자열.
  - 대규모 치환 전에 기능 테스트를 먼저 유지해야 함.
- 실제 외부 API 호출은 네트워크 권한 승인이 필요할 수 있음.
  - 샌드박스에서는 온비드 호출이 차단될 수 있으며, 승인 후 정상 동작 확인됨.
- `main_app.py`에 아직 남은 라우트가 있음.
  - 인증/계정/사용자 설정
  - 관리자 메타데이터 보정
  - 루트/로그인/원문 URL 생성 helper 등

## 6. 절대 바꾸면 안 되는 부분

주의해서 유지해야 할 부분:
- API 키, 개인 키, 세션 키를 로그/리포트/화면에 노출하지 말 것.
- 기존 `.env` 값 자체를 임의로 삭제하거나 공개하지 말 것.
- `auction_data.db`를 사용자 승인 없이 삭제하지 말 것.
- `storage/raw_quarantine`, `storage/processed`, `storage/logs`의 기존 자료를 임의 삭제하지 말 것.
- `RawDocument.file_path` 원문 파일 경로 보안 검사를 약화하지 말 것.
- `/documents/raw/{raw_doc_id}`는 로그인 없이 열리면 안 됨.
- 온비드 중복 기준을 단순히 `cltr_mng_no` 하나로 되돌리지 말 것.
  - 현재 `cltr_mng_no`, `pbct_cdtn_no`, 그리고 보조 식별값 `onbid_cltr_no`, `pbct_no`, `pbct_nsq`가 중요함.
- 기존 테스트를 삭제하지 말 것.
  - 실패하면 고쳐야 하며, 임의로 테스트 기대값을 낮추면 안 됨.
- `main_app.py`를 다시 거대 라우트 파일로 되돌리지 말 것.
- 사용자가 만든 변경사항을 git reset/checkout 등으로 되돌리지 말 것.

## 7. 다음 Codex 대화에서 바로 실행할 첫 번째 작업 지시문

다음 대화에서 아래 지시문으로 바로 시작하면 된다:

> `court_auction_platform/PROJECT_CONTEXT.md`와 `docs/service_boundary_refactoring_plan.md`를 먼저 읽고, 이어서 계정/비밀번호/사용자 설정 라우터 분리를 진행해줘. `/account/password`, `/user/settings`, 가능하면 로그인/로그아웃 라우트까지 `backend/web/routers/account.py` 또는 `auth.py`로 분리하고, `tests/router_boundary_test.py`와 `tests/page_response_smoke_test.py`를 확장한 뒤 전체 회귀 테스트를 실행해줘. 완료 후 `reports/`에 스프린트 리포트를 작성해줘.
