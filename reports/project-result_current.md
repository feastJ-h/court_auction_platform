# Project Current Status

업데이트: 2026-07-06

## 현재 수준

`court_auction_platform`는 v003 Public Beta Readiness Pack 1 기준으로 공개 탐색과 로그인 개인화를 분리했다.

- 비로그인 공개 탐색:
  - `/`
  - `/onbid`
  - `/onbid/{auction_item_id}`
  - `/cases`
  - `/cases/{event_id}`
  - `/about`
  - `/disclaimer`
  - `/privacy-draft`
- 로그인 사용자:
  - `/user` 회생/파산 AI 분석 화면
  - `/my/onbid/favorites`
  - `/my/onbid/passed`
  - `/my/onbid/watching`
  - 온비드 관심/패스/감시/메모 저장
- 관리자:
  - 기존 수집, 분석, OCR, 품질, 사용자 관리 기능 유지
  - 관리자 API 인증 경계 유지

## 주요 라우트

- 온비드 공개: `GET /onbid`, `GET /onbid/{auction_item_id}`
- 온비드 개인화: `POST /onbid/{auction_item_id}/preference`, `POST /api/onbid/{auction_item_id}/preference`
- 회생/파산 공개: `GET /cases`, `GET /cases/{event_id}`
- 회생/파산 로그인: `GET /user`, `GET /user/bookmarks`, `GET /user/watching`, `GET /user/passed`
- 원문 보호: `GET /documents/raw/{raw_doc_id}` 로그인 필요
- SEO/고지: `GET /robots.txt`, `GET /sitemap.xml`, `GET /about`, `GET /disclaimer`, `GET /privacy-draft`

## 주요 DB 모델

- 기존:
  - `AssetEvent`, `RawDocument`, `CollectionEvidence`, `AiAnalysis`, `AnalysisResult`
  - `AuctionItem`, `AuctionNotice`, `AuctionNoticeItemLink`
  - `UserEventAction`, `UserEventNote`
- v003 신규:
  - `UserAuctionPreference`

## 공개/로그인/관리자 경계

- 공개 회생/파산 DTO는 AI 분석, OCR 전문, raw file path, `/documents/raw/{id}`를 포함하지 않는다.
- 공개 온비드 DTO는 raw payload를 포함하지 않는다.
- 온비드 preference POST/API는 로그인 필수다.
- 관리자 API는 기존 인증 요구를 유지한다.
- 광고 슬롯은 `ADSENSE_ENABLED=false` 기본값으로 비활성이다.

## 테스트

검증 완료:

```powershell
$Py = "C:\Users\xogns\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
& $Py -m py_compile main_app.py backend/database/models.py backend/database/session.py backend/web/routers/auctions.py backend/web/routers/cases.py backend/services/auction_items.py backend/services/user_auction_preferences.py tests/public_access_auth_boundary_test.py tests/router_boundary_test.py
& $Py tests/onbid_module_test.py
& $Py tests/page_response_smoke_test.py
& $Py tests/router_boundary_test.py
& $Py tests/isolated_operations_test.py
& $Py tests/public_access_auth_boundary_test.py
powershell -ExecutionPolicy Bypass -File .\run_onbid_scheduled_sync.ps1 -Sample -ApiKind notice -Limit 20 -MaxPages 1 -IncludeNoticeDetails -IncludeNoticeItems
```

참고: 이 도구 세션에서는 background uvicorn 프로세스가 유지되지 않아 `http://127.0.0.1:8000/onbid` 로컬 서버 확인은 실패했다. 라우트와 페이지 검증은 FastAPI `TestClient`로 완료했다.

## 남은 리스크

- 개인정보 처리방침은 초안이며 베타 공개 전 정식화 필요.
- 실제 AdSense client/slot은 연결하지 않음.
- 실제 온비드 API probe는 API 키/네트워크 전제가 있어 보류.
- sitemap은 정적 공개 URL만 포함한다.
- 같은 공고에 묶인 다른 온비드 물건 UX는 v004에서 보강 권장.

## v004 우선순위

1. 온비드 데이터 품질과 필터/검색 UX 고도화.
2. 실제 API 샘플 기반 normalizer 보강.
3. 같은 공고의 다른 물건 상세 UX 추가.
4. 동적 sitemap 정책 수립.
5. 백업/복원 리허설과 운영 스케줄러 점검.
