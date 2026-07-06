# 자산 분석 플랫폼 프로젝트 결과 정리 v001

작성일: 2026-07-06  
프로젝트 경로: `C:\Users\xogns\Documents\testAuction\court_auction_platform`

## 1. 프로젝트 한 줄 요약

이 프로젝트는 회생·파산 공고와 온비드 공매 데이터를 수집하고, 회생·파산 영역에는 AI 분석을 적용하며, 온비드 영역에는 물건 목록·상세 수집과 공매 탐색을 집중시키는 로컬 기반 자산 분석 플랫폼이다.

현재 상태는 내부 MVP에 가까운 수준이다. 로그인, 사용자 화면, 관리자 화면, 회생·파산 수집, OCR, AI 분석 작업 큐, 온비드 공매 수집, 온비드 목록·상세 화면, 수집 스케줄 운영 문서, 주요 스모크 테스트가 갖춰져 있다.

## 2. 핵심 서비스 방향

서비스는 두 개의 큰 카테고리로 구분한다.

1. 회생·파산
   - 법원 공고와 첨부 문서를 수집한다.
   - 문서 파싱, OCR, AI 분석, 관리자 검토, 사용자 관심/패스/메모 기능을 제공한다.
   - AI 분석은 당분간 이 영역에만 집중한다.

2. 온비드 공매
   - 온비드 API를 통해 공매 물건을 수집한다.
   - 부동산, 동산, 공고, 공고 물건, 국유재산 입찰대상 등으로 확장 가능한 기반이 있다.
   - 회생·파산 사건과 억지로 연결하기보다 공매 물건 정보의 수집·정리·조회에 집중한다.

법원경매와 지도탐색은 현재 사용자 UI에서 숨기는 방향으로 정리했다. 실제 서비스 첫 화면은 회생·파산과 온비드 공매 중심으로 이해되도록 개선했다.

## 3. 이번 정리에서 추가로 완료한 작업

### 3.1 수집 스케줄 정책 리팩토링

회생·파산과 온비드의 수집 주기를 서로 다르게 설계했다.

회생·파산 권장 스케줄:

```text
평일 08:10, 15:10
주말 09:10
```

온비드 권장 스케줄:

```text
매일 06:30, 08:30, 10:30, 12:30, 14:30, 16:30, 18:30, 20:30, 22:30
```

이 정책은 `backend/services/crawl_runs.py`에서 한 곳에 모아 계산한다. 관리자 수집 화면은 이 값을 그대로 표시한다.

### 3.2 온비드 동산 상세 수집 연결

기존에는 부동산 상세 수집 흐름이 더 먼저 연결되어 있었고, 동산 상세 API는 클라이언트 함수만 준비된 상태에 가까웠다. 이번 정리에서 `include_details` 옵션이 동산 목록 수집에도 전달되도록 연결했다.

변경된 흐름:

```text
run_onbid_sync(... include_details=True)
-> collect_movable_pages(...)
-> OnbidClient.fetch_movable_items(... include_details=True)
-> fetch_movable_detail(...)
-> merge_onbid_detail(...)
-> upsert_auction_item(...)
```

이제 온비드 상세 수집 옵션은 부동산과 동산 모두에 적용 가능하다.

### 3.3 관리자 수집 화면 정리

`frontend/templates/admin/collection.html`을 다시 정리했다.

주요 개선:

- 회생·파산 수집과 온비드 수집을 같은 화면에서 명확히 분리
- 각각 마지막 상태, 마지막 성공, 다음 예정 시각, 운영 시간 표시
- 온비드 수집 버튼 유지
- 수집 이력 표를 Jinja 매크로로 정리해 중복 감소
- 깨져 보이던 문구를 한국어 기준으로 재작성

### 3.4 운영 스크립트 기본값 조정

회생·파산 수집은 더 가볍게, 온비드는 더 자주 넓게 수집하는 기본값으로 조정했다.

회생·파산:

```text
Limit=40
MaxPages=8
DaysBack=7
```

온비드:

```text
Limit=100
MaxPages=8
ApiKind=all
IncludeDetails=기본 꺼짐
```

### 3.5 운영 문서 최신화

다음 문서를 새 정책에 맞게 다시 작성했다.

- `docs/production_crawling_schedule_runbook.md`
- `docs/onbid_scheduled_sync_runbook.md`

두 문서 모두 수동 실행, Windows 작업 스케줄러 등록 예시, 로그 확인 경로, 운영 주의사항을 포함한다.

### 3.6 PowerShell 로그 인코딩 정리

수집 스크립트에서 Python 출력이 PowerShell 로그에 섞일 때 NUL 문자가 포함되어 보이는 문제가 있었다. `*>>` 직접 append 대신 Python 출력값을 받아 UTF-8로 `Out-File -Append` 처리하도록 변경했다.

대상 스크립트:

- `run_scheduled_crawl.ps1`
- `run_onbid_sync.ps1`
- `run_onbid_scheduled_sync.ps1`

검증 결과, 새 로그는 UTF-8 텍스트로 정상 출력된다.

## 4. 현재 주요 파일 구조

```text
court_auction_platform/
  main_app.py
  orchestrator.py
  backend/
    ai_engine/
    analysis/
    analysis_worker/
    config.py
    crawler/
    database/
    document_pipeline/
    jobs/
    ocr/
    onbid/
    parser/
    services/
    web/
      routers/
  frontend/
    static/
    templates/
  docs/
  reports/
  storage/
  tests/
  *.ps1
```

## 5. 백엔드 구성

### 5.1 FastAPI 앱

진입점은 `main_app.py`다.

현재 역할:

- FastAPI 앱 생성
- Jinja2 템플릿 연결
- 정적 파일 연결
- 로그인/로그아웃
- 세션 쿠키 인코딩·검증
- 공통 사용자/관리자 인증 함수
- 공통 이벤트 표시 메타데이터 구성
- 각 도메인 라우터 등록

아직 `main_app.py`에는 계정/비밀번호/사용자 설정/관리자 메타데이터 보정 같은 일부 레거시 라우트가 남아 있다. 기능상 동작하지만, 장기적으로는 `backend/web/routers/account.py` 또는 별도 auth/account 라우터로 분리하는 것이 좋다.

### 5.2 라우터 분리 상태

분리 완료된 주요 라우터:

- `backend/web/routers/auctions.py`
  - 온비드 공매 목록
  - 온비드 공매 상세
  - 관리자 온비드 수집 API
  - 사건-공매 연결 후보 API는 아직 남아 있으나 UI에서는 핵심 흐름에서 내려둔 상태

- `backend/web/routers/admin_operations.py`
  - 관리자 대시보드
  - 관리자 물건 화면
  - 관리자 분석 화면
  - 관리자 수집 관리 화면
  - 분석 리뷰 화면
  - 수집 품질 API

- `backend/web/routers/admin_users.py`
  - 관리자 사용자 생성
  - 사용자 활성/비활성
  - 권한 변경

- `backend/web/routers/cases.py`
  - 사용자 회생·파산 화면
  - 관심/패스/감시/메모 기능
  - 사용자 액션 기반 목록

- `backend/web/routers/analysis.py`
  - 기본 분석 API
  - 상세 분석 job 생성
  - job 상태/취소/재시도/이벤트 조회
  - 분석 리뷰 등록
  - 로컬 분석 상태 API

- `backend/web/routers/ocr_operations.py`
  - OCR job enqueue
  - OCR 상태 확인

- `backend/web/routers/documents.py`
  - 원문 문서 제공
  - 로그인 사용자만 접근 가능

## 6. 데이터베이스 모델

주요 테이블:

### 6.1 회생·파산 영역

- `RawDocument`
  - 수집된 원문 파일
  - 파일 경로, 원본 URL, 파일 해시

- `CollectionEvidence`
  - 수집 근거
  - 공고 제목, 첨부명, 공고일, 마감일, 상세 페이지 텍스트

- `Asset`
  - 자산 카테고리, 세부 카테고리, 주소

- `AssetEvent`
  - 사건/공고 단위 데이터
  - 사건번호, 상태, 제목, 공고 URL, 공고일, 마감일, 파싱 상태, 추출 텍스트

- `AiAnalysis`
  - 기본 AI 분석 결과

- `AnalysisResult`
  - 모델별 분석 결과 저장
  - Gemini, ChatGPT, Codex 계열 결과 비교를 고려한 구조

- `AnalysisJob`
  - 상세 분석/OCR 등 비동기 작업
  - 상태, 시도 횟수, 결과 파일 경로, 진행률, 취소 요청 여부

- `AnalysisJobEvent`
  - 분석 작업 이벤트 로그

- `AnalysisReview`
  - 관리자 분석 품질 평가

### 6.2 사용자 영역

- `User`
  - 사용자 계정, 비밀번호 해시, 표시명, 역할, 활성 상태

- `UserEventAction`
  - 관심, 패스, 감시 등 사용자별 사건 액션

- `UserEventNote`
  - 사용자별 사건 메모와 태그

### 6.3 온비드 영역

- `AuctionItem`
  - 온비드 물건 기본 정보
  - `cltr_mng_no`, `pbct_cdtn_no`, `onbid_cltr_no`, `pbct_no`, `pbct_nsq` 등 온비드 식별자 포함
  - 감정가, 최저입찰가, 보증금, 입찰 시작/마감/개찰일
  - 소재지, 기관명, 용도, 상세 설명, 유의사항, 원문 payload

- `AuctionItemSnapshot`
  - 수집 시점별 가격/상태 스냅샷

- `AuctionNotice`
  - 공고 단위 데이터

- `AuctionResult`
  - 낙찰/결과 데이터 확장용

- `CaseAuctionLink`
  - 회생·파산 사건과 온비드 물건 연결용
  - 현재 서비스 방향상 핵심 UI에서는 후순위

- `AuctionAlert`
  - 알림 확장용

### 6.4 운영 영역

- `CrawlRun`
  - 회생·파산 수집과 온비드 수집 모두의 실행 이력
  - `run_type`으로 구분
  - 온비드 실행 유형은 `onbid_scheduled`, `onbid_manual`, `onbid_backfill`, `onbid_sample` 사용

- `AuditLog`
  - 관리자/사용자 중요 행위 기록

## 7. 온비드 API 연동 상태

온비드 클라이언트는 `backend/onbid/client.py`에 있다.

현재 준비된 API 범위:

1. 부동산 물건 목록
   - Endpoint: `OnbidRlstListSrvc2`
   - Operation: `getRlstCltrList2`

2. 부동산 물건 상세
   - Endpoint: `OnbidRlstDtlSrvc2`
   - Operation: `getRlstDtlInf2`

3. 동산 물건 목록
   - Endpoint: `OnbidMvastListSrvc2`
   - Operation: `getMvastCltrList2`

4. 동산 물건 상세
   - Endpoint: `OnbidMvastDtlSrvc2`
   - Operation: `getMvastDtlInf2`

5. 공고 목록
   - Endpoint: `OnbidPbancListSrvc2`
   - Operation: `getPbancList2`

6. 공고 상세
   - Endpoint: `OnbidPbancDtlnfSrvc2`
   - Operation: `getPbancDtlInf2`

7. 공고 상세 물건정보
   - Endpoint: `OnbidPbancCltrDtlSrvc2`
   - Operation: `getPbancCltrInf2`

8. 국유일반재산 입찰대상물건
   - Endpoint: `kamcoRlcBidTrgtCltr`
   - Operation: `cltrLst`

현재 실제 저장 흐름에 직접 연결된 것은 부동산 목록/상세, 동산 목록/상세다. 공고 목록·공고 상세·공고 물건정보·입찰대상물건은 클라이언트 함수와 분석 문서 기반이 준비되어 있으며, 다음 단계에서 저장 모델과 화면 연결을 확장하면 된다.

## 8. 온비드 수집 흐름

실행 스크립트:

- 단발/기존 수집: `run_onbid_sync.ps1`
- 스케줄 수집: `run_onbid_scheduled_sync.ps1`

워커:

- `backend/workers/onbid_sync.py`

흐름:

```text
PowerShell script
-> python -m backend.workers.onbid_sync
-> OnbidClient
-> normalize_onbid_api_item
-> upsert_auction_item
-> AuctionItem / AuctionItemSnapshot / AuctionNotice
-> CrawlRun 기록
```

지원 옵션:

- `--api-kind real_estate`
- `--api-kind movable`
- `--api-kind all`
- `--include-details`
- `--sample`
- `--limit`
- `--page-no`
- `--max-pages`
- `--run-type`

스케줄 스크립트 특징:

- `storage/onbid_scheduled_sync.lock`으로 중복 실행 방지
- `storage/logs/onbid/`에 실행 로그 저장
- sample/manual/scheduled/backfill 실행 유형 분리

## 9. 회생·파산 수집 흐름

실행 스크립트:

- `run_scheduled_crawl.ps1`

워커:

- `backend/workers/scheduled_crawl.py`

오케스트레이션:

- `orchestrator.py`

흐름:

```text
PowerShell script
-> python -m backend.workers.scheduled_crawl
-> orchestrator.run_pipeline
-> crawler.crawl_court_notices
-> parser.extract_document
-> ai_engine.analyze_asset_text
-> RawDocument / CollectionEvidence / Asset / AssetEvent / AiAnalysis
-> CrawlRun 기록
```

특징:

- DryRun 지원
- 최근 N일 기준 수집
- 특정 시작일/종료일 보정 수집
- 파일 해시 기반 중복 방지
- 실패 시에도 가능한 범위의 원문/증거 데이터 보존

## 10. AI 분석 구조

AI 분석은 회생·파산 중심으로 둔다.

분석 구성:

- 기본 분석: `backend/ai_engine/analyzer.py`
- 상세 분석 prompt: `backend/analysis_worker/prompt_builder.py`
- 상세 분석 worker:
  - `backend/analysis_worker/cli_worker.py`
  - `backend/analysis_worker/app_server_worker.py`
- 분석 결과 파서: `backend/analysis_worker/result_parser.py`
- 분석 job API: `backend/web/routers/analysis.py`

지원 Provider 구조:

- Gemini
- OpenAI/ChatGPT 계열
- Codex CLI
- Codex App Server

운영 방향:

- 자동으로 모든 온비드 물건에 AI 분석을 붙이지 않는다.
- 회생·파산 사건의 문서 분석, 환가 가능성, 위험 요소 정리에 우선 적용한다.
- 온비드는 당분간 데이터 수집, 정규화, 검색, 가격·상태 추적 중심으로 발전시키는 것이 좋다.

## 11. OCR 구조

OCR 관련 구성:

- `backend/ocr/tesseract_engine.py`
- `backend/workers/ocr_worker.py`
- `run_ocr_worker.ps1`
- `docs/tesseract_ocr_setup.md`

OCR 상태:

- `OCR_REQUIRED`
- `OCR_PARSED`
- `OCR_MOCKED`
- `PARSE_FAILED`

운영 포인트:

- Tesseract와 Poppler가 로컬 환경에 준비되어야 한다.
- OCR은 비용보다 처리 시간이 주요 병목이다.
- OCR 완료 후 AI 분석 job으로 이어지는 구조를 점진적으로 자동화할 수 있다.

## 12. UI/UX 현황

### 12.1 사용자 화면

주요 템플릿:

- `frontend/templates/user/index.html`
- `frontend/templates/user/action_list.html`
- `frontend/templates/user/passed.html`
- `frontend/templates/user/settings.html`

현재 사용자 화면 방향:

- 회생·파산 업무를 기본 작업 공간으로 제공
- 관심/감시/패스/메모 같은 개인 작업 흐름 제공
- 온비드 공매는 별도 큰 카테고리로 진입
- 법원경매/지도탐색은 현재 노출하지 않음

### 12.2 온비드 화면

주요 템플릿:

- `frontend/templates/auctions/index.html`
- `frontend/templates/auctions/detail.html`

현재 방향:

- 온비드 공매 물건 목록 조회
- 물건 상세 확인
- 입찰가, 감정가, 할인율, 일정, 기관, 식별자 확인
- 사건 연결보다 수집 정보 표시와 검토 포인트 중심

### 12.3 관리자 화면

주요 템플릿:

- `frontend/templates/admin/dashboard.html`
- `frontend/templates/admin/assets.html`
- `frontend/templates/admin/analysis.html`
- `frontend/templates/admin/collection.html`
- `frontend/templates/admin/reviews.html`
- `frontend/templates/admin/users.html`

현재 관리자 화면 방향:

- 회생·파산 분석 상태 관리
- 수집 품질 점검
- OCR/AI 작업 상태 확인
- 분석 리뷰
- 온비드 수집 상태 분리 확인
- 사용자 관리

## 13. 운영 스크립트 목록

주요 스크립트:

- `run_fastapi.ps1`
  - FastAPI 서버 실행

- `start_fastapi_background.ps1`
  - 백그라운드 서버 실행

- `stop_fastapi.ps1`
  - 서버 종료

- `run_scheduled_crawl.ps1`
  - 회생·파산 정기/수동/보정 수집

- `run_onbid_sync.ps1`
  - 온비드 수동 수집

- `run_onbid_scheduled_sync.ps1`
  - 온비드 스케줄 수집

- `run_ocr_worker.ps1`
  - OCR 작업 실행

- `enqueue_deep_analysis_jobs.ps1`
  - 상세 분석 job 등록

- `run_cli_analysis_worker.ps1`
  - CLI 기반 분석 worker 실행

- `run_codex_app_server_worker.ps1`
  - Codex App Server 기반 분석 worker 실행

- `backup_database.ps1`
  - DB 백업

- `ingest_local_quarantine.ps1`
  - 로컬 격리 폴더 문서 수집

## 14. 운영 문서

현재 `docs/`에 있는 핵심 문서:

- `production_crawling_schedule_runbook.md`
  - 회생·파산 수집 스케줄 가이드

- `onbid_scheduled_sync_runbook.md`
  - 온비드 수집 스케줄 가이드

- `service_boundary_refactoring_plan.md`
  - 라우터/서비스 경계 정리 계획

- `tesseract_ocr_setup.md`
  - OCR 설치/설정 안내

- `sprint_execution_protocol.md`
  - 스프린트 진행 방식

## 15. 테스트 현황

현재 주요 테스트:

- `tests/onbid_module_test.py`
  - 온비드 샘플 수집
  - 부동산 상세 중복 처리
  - 동산 수집
  - 온비드 페이지 응답
  - 관리자 주요 페이지 응답

- `tests/page_response_smoke_test.py`
  - 로그인
  - 주요 보호 페이지 응답
  - 원문 문서 접근 권한
  - 주요 API 응답

- `tests/router_boundary_test.py`
  - 라우터 등록 경계와 중복 등록 방지

- `tests/isolated_operations_test.py`
  - 격리된 운영 흐름 테스트

이번 정리 후 확인한 검증:

```text
py_compile 통과
tests/onbid_module_test.py 통과
tests/page_response_smoke_test.py 통과
tests/router_boundary_test.py 통과
tests/isolated_operations_test.py 통과
run_scheduled_crawl.ps1 -DryRun 통과
run_onbid_scheduled_sync.ps1 -Sample 통과
run_onbid_sync.ps1 -Sample 통과
```

알려진 경고:

```text
Starlette TestClient의 httpx 관련 deprecation warning
```

현재 기능 실패는 아니며, 추후 FastAPI/Starlette/httpx 버전 조정 때 정리하면 된다.

## 16. 현재 완성도 평가

### 16.1 내부 MVP 기준

완성도: 높음

가능한 것:

- 로그인
- 회생·파산 공고 수집
- 문서 저장
- OCR 준비
- AI 분석 job 관리
- 사용자별 관심/패스/메모
- 관리자 대시보드
- 관리자 수집 품질 점검
- 온비드 API 기반 물건 수집
- 온비드 목록/상세 조회
- 회생·파산/온비드 수집 스케줄 분리
- 운영 문서 기반 작업 스케줄러 등록

### 16.2 실제 서비스 기준

아직 필요한 것:

- 인증/권한 보안 강화
- 운영 DB 마이그레이션 체계
- 배포 환경 구성
- 장애 알림
- 외부 API 호출량 정책
- 개인정보 마스킹 기본 활성화 검토
- 실사용 UI 문구 전체 정리
- 온비드 공고/결과/입찰대상 API 저장 구조 확장
- 데이터 품질 대시보드 고도화

## 17. 중요한 주의사항

### 17.1 API 키

온비드 API 키와 AI API 키는 `.env`에 둔다. 문서나 화면에 직접 노출하지 않는다.

### 17.2 원문 문서 보안

`/documents/raw/{raw_doc_id}`는 로그인 사용자에게만 제공된다. 이 경계는 유지해야 한다.

### 17.3 DB 삭제 금지

`auction_data.db`, `storage/raw_quarantine`, `storage/processed`, `storage/logs`는 임의 삭제하지 않는다.

### 17.4 온비드 중복 기준

온비드는 단순 `cltr_mng_no` 하나만으로 중복 판단하면 안 된다. 현재는 `source + cltr_mng_no + pbct_cdtn_no`를 핵심 unique 기준으로 둔다. 입찰 회차 구분을 위해 `onbid_cltr_no`, `pbct_no`, `pbct_nsq`도 보조 식별자로 유지한다.

### 17.5 인코딩 이슈

일부 오래된 파일과 테스트 샘플에는 깨져 보이는 한글 문자열이 남아 있다. 기능 테스트는 통과하지만, 실제 서비스 polish 단계에서는 템플릿과 샘플 데이터의 UTF-8 문자열을 점진적으로 정리하는 것이 좋다.

## 18. 다음 개발 우선순위

### 18.1 최우선

1. Windows 작업 스케줄러 실제 등록
   - 회생·파산: 평일 08:10, 15:10 / 주말 09:10
   - 온비드: 매일 06:30~22:30 2시간 간격
   - 온비드 상세: 매일 23:10 별도 실행 권장

2. 관리자 수집 화면 실제 데이터로 관찰
   - 성공률
   - 중복률
   - 실패 메시지
   - API 호출량

3. 온비드 공고 API 저장 구조 확장
   - `AuctionNotice`를 공고 목록/상세 API와 직접 연결
   - 공고 물건정보 API를 `AuctionItem`과 매핑
   - 국유일반재산 입찰대상 API 결과 저장 모델 검토

### 18.2 서비스 품질

4. UI 문구 전체 UTF-8 정리
   - 관리자 화면
   - 사용자 화면
   - 샘플 데이터
   - 테스트 기대 문구

5. 데이터 품질 대시보드 강화
   - 온비드 수집 건수 추세
   - API별 실패율
   - 중복률
   - 상세 수집 누락률
   - 입찰 마감 D-day 분포

6. 온비드 검색/필터 개선
   - 소재지
   - 용도
   - 기관
   - 가격대
   - 입찰 마감일
   - 할인율
   - 부동산/동산 세부 구분

### 18.3 운영 안정화

7. Alembic 도입 또는 migration ledger 작성
   - 현재 SQLite 자동 보정 방식이 섞여 있다.
   - 서비스 운영 전에는 명시적 마이그레이션 체계가 필요하다.

8. 백업/복구 절차 정식화
   - DB 백업
   - 원문 문서 백업
   - 로그 보관 정책

9. 실패 알림
   - 작업 스케줄러 실패
   - 온비드 API 실패
   - OCR 실패
   - AI worker 장기 RUNNING 상태

### 18.4 사업화/서비스화

10. 사용자 권한 모델 구체화
    - 관리자
    - 내부 검토자
    - 일반 사용자
    - 읽기 전용 사용자

11. 결제/구독 전 서비스 범위 정의
    - 회생·파산 분석은 고부가 기능
    - 온비드 공매 탐색은 데이터 탐색 기능
    - 리포트 다운로드, 알림, 관심 물건 추적을 유료 기능 후보로 검토

12. 법적 고지와 책임 범위 정리
    - AI 분석은 참고자료
    - 입찰/투자 판단 책임
    - 공공 API 데이터 지연/오류 가능성
    - 개인정보 처리 방침

## 19. ChatGPT에 이어서 물어보기 좋은 질문

아래 질문을 그대로 ChatGPT에 넣으면 다음 사업/개발 계획을 잡기 좋다.

```text
아래 프로젝트 결과 문서를 바탕으로, 이 서비스를 실제 베타 서비스로 출시하기 위한 4주 개발 로드맵을 만들어줘.
각 주차별 목표, 개발 작업, 운영 준비, 리스크, 검증 방법을 분리해서 제안해줘.
```

```text
회생·파산 AI 분석과 온비드 공매 수집을 가진 자산 분석 플랫폼의 MVP 기능 범위를 재정의해줘.
무료 기능, 내부 관리자 기능, 유료 후보 기능으로 나눠서 정리해줘.
```

```text
온비드 API를 더 확장하려고 한다.
부동산/동산 목록·상세, 공고 목록·상세, 공고 물건정보, 국유재산 입찰대상 API를 어떤 DB 모델과 화면 구조로 확장하면 좋을지 설계해줘.
```

```text
현재 로컬 FastAPI + SQLite 기반 프로젝트를 실제 서비스 환경으로 옮기려면 어떤 인프라 구성이 적절한지 제안해줘.
개인 개발자가 운영 가능한 저비용 구성과, 이후 확장 가능한 구성을 각각 제시해줘.
```

## 20. 다음 작업을 시작할 때 추천 문장

다음 Codex 또는 ChatGPT 작업을 시작할 때는 아래 문장으로 시작하면 좋다.

```text
court_auction_platform/project-result_v001.md를 읽고, 현재 프로젝트를 베타 출시 가능한 수준으로 만들기 위한 다음 스프린트를 진행해줘.
우선순위는 온비드 공고 API 저장 구조 확장, UI 문구 UTF-8 정리, 스케줄러 실제 운영 점검, 데이터 품질 대시보드 강화야.
```

## 21. 결론

프로젝트는 이제 단순 실험 단계에서 벗어나, 내부 MVP와 운영 준비 단계 사이에 있다. 회생·파산은 AI 분석 중심, 온비드는 대량 공매 데이터 수집 중심이라는 큰 방향이 잡혔고, 이 방향에 맞게 UI와 스케줄러도 분리되었다.

다음 단계의 핵심은 기능을 더 많이 붙이는 것보다, 실제 운영에서 매일 데이터가 안정적으로 쌓이고 관리자가 실패를 빨리 발견할 수 있게 만드는 것이다. 그 다음에 온비드 공고/결과 API 확장과 사용자 알림/리포트 기능을 붙이면 서비스 형태가 더 선명해질 것이다.
