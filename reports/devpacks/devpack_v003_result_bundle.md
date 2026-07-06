# Codex 개발 결과 Bundle v003

## 1. 작업 메타데이터

- Git root: `C:/Users/xogns/Documents/testAuction/court_auction_platform`
- Branch: `codex/devpack-v003-public-first-personalization`
- Base commit: `e392e30 docs: add v003 devpack instructions` (`baseline-v002-20260706` 이후)
- Final commit(s): 커밋하지 않음. 사용자 승인 전 push/commit 미수행.
- Remote: `https://github.com/feastJ-h/court_auction_platform.git`
- 작업 시작 status: `git status --short` 출력 없음
- 작업 종료 status: 변경 파일은 working tree에 있으며 커밋/스테이징하지 않음. 민감 파일 stage 검사 출력 없음.

작업 시작 확인 명령 결과:

```text
git rev-parse --show-toplevel
=> C:/Users/xogns/Documents/testAuction/court_auction_platform

git branch --show-current
=> codex/devpack-v003-public-first-personalization

git status --short
=> 출력 없음

git remote -v
=> origin https://github.com/feastJ-h/court_auction_platform.git (fetch)
=> origin https://github.com/feastJ-h/court_auction_platform.git (push)

git --no-pager log --oneline --decorate -5
=> e392e30 (HEAD -> codex/devpack-v003-public-first-personalization, origin/codex/devpack-v003-public-first-personalization) docs: add v003 devpack instructions
=> 48f47c7 (tag: baseline-v002-20260706, origin/main, main) baseline after devpack v002
```

## 2. 수준 결과 요약

v003 Core Scope를 구현했다. 비로그인 사용자는 `/onbid`, `/onbid/{id}`, `/cases`, `/cases/{id}`를 볼 수 있고, 로그인 사용자는 온비드 관심/패스/감시/메모를 저장할 수 있다. 회생/파산 공개 화면은 별도 public DTO와 템플릿을 사용해 AI 분석, OCR 전문, 내부 raw file 경로, `/documents/raw/{id}` 링크를 생성하지 않는다.

Extended Scope 일부도 완료했다. 온비드 기본/빠른 필터, 공고 연결 표시, 공개 홈, 광고 슬롯 feature flag, SEO 기본 route, about/disclaimer/privacy-draft 초안을 추가했다.

## 3. Core Scope 결과

### 3.1 공개 온비드 목록/상세

- `GET /onbid`, `GET /onbid/{auction_item_id}` 추가.
- 기존 `GET /auctions`, `GET /auctions/{auction_item_id}`도 로그인 없이 접근 가능하게 유지.
- 목록에 물건명, 분류, 소재지, 기관, 감정가, 최저가, 저감률, 입찰마감 D-day, 공고 연결 여부, 상세 여부를 표시.

### 3.2 공개 온비드 상세/공고/원문 링크

- 상세 화면에 가격, 일정, 물건정보, 입찰조건, 유의사항, 연결 공고 목록을 표시.
- 온비드 공고 외부 URL은 `target="_blank" rel="noopener noreferrer"`로 표시.
- 내부 storage 경로와 raw payload는 공개 템플릿에 전달하지 않음.

### 3.3 공개 회생/파산 목록/기본 상세

- `GET /cases`, `GET /cases/{event_id}` 추가.
- 공개 DTO는 사건번호, 제목, 상태, 공고일, 마감일, 분류, 소재지, 외부 원문 URL만 포함.
- AI 분석 본문, OCR 전문, 내부 원문 파일 URL, raw file path는 생성하지 않음.

### 3.4 로그인 온비드 개인화

- 신규 모델/테이블: `UserAuctionPreference`.
- 신규 서비스: `backend/services/user_auction_preferences.py`.
- POST:
  - `POST /onbid/{auction_item_id}/preference`
  - `POST /api/onbid/{auction_item_id}/preference`
- 내 온비드:
  - `GET /my`
  - `GET /my/onbid/favorites`
  - `GET /my/onbid/passed`
  - `GET /my/onbid/watching`
- 상태 규칙:
  - 관심 ON 시 패스 해제
  - 패스 ON 시 관심/감시 해제
  - 감시 ON 시 패스 해제

### 3.5 회생/파산 AI 노출 경계

- 공개 `/cases` 계열은 로그인 화면의 `build_event_payload`를 사용하지 않는다.
- `tests/public_access_auth_boundary_test.py`에서 `SECRET AI`, `SECRET OCR`, `documents/raw`, raw 파일명이 공개 상세에 없는 것을 검증.
- `/documents/raw/{raw_doc_id}`는 기존처럼 비로그인 401 유지.

### 3.6 권한 경계 테스트

- `tests/public_access_auth_boundary_test.py` 신규 추가.
- `tests/router_boundary_test.py`에 v003 공개/개인화 route 등록 기대값 추가.

## 4. Extended Scope 결과

### 4.1 온비드 필터/정렬

- 지원 필터: `q/keyword`, `region`, `asset_type`, `usage`, `agency`, `price_min`, `price_max`, `closing_within_days`, `min_discount_rate`, `has_notice`, `has_detail`, `sort`.
- 빠른 필터: 7일 내 마감, 신규 등록, 저감률 30%+, 부동산, 동산, 공고 연결 있음, 상세정보 있음.

### 4.2 온비드 공고 요약/같은 공고 물건

- 상세 화면에 연결 공고 요약을 표시.
- 같은 공고의 다른 물건 탐색은 이번 변경에서 보류. 링크 데이터는 `AuctionNoticeItemLink`로 유지됨.

### 4.3 공개 랜딩 페이지

- `/`를 공개 탐색 허브로 변경.
- `/onbid`, `/cases`, `/disclaimer`로 바로 이동할 수 있게 구성.

### 4.4 광고 슬롯 feature flag

- 설정 추가:
  - `ADSENSE_ENABLED=false`
  - `ADSENSE_CLIENT_ID=`
  - `ADSENSE_FOOTER_SLOT_ID=`
- partial: `frontend/templates/shared/ad_slot.html`
- 공개 온비드/회생·파산 하단에만 include. 관리자 페이지에는 include하지 않음.

### 4.5 SEO/robots/sitemap

- `GET /robots.txt`
- `GET /sitemap.xml`
- 공개 홈에 기본 description/Open Graph meta 추가.

### 4.6 고지/AI 책임 안내

- `GET /about`
- `GET /disclaimer`
- `GET /privacy-draft`
- 개인정보 문서는 초안 상태를 명시.

### 4.7 UTF-8 정리

- 신규 공개 템플릿과 결과 문서는 UTF-8 한국어로 작성.
- 기존 devpack 지시서의 콘솔 출력 깨짐은 수정하지 않음.

## 5. Stretch Scope 결과

### 5.1 관리자 관찰성 2차

보류. v003 Core/Extended 권한 경계와 공개 전환을 우선 처리했다.

### 5.2 실제 API probe 준비

보류. 실제 API 키가 필요한 작업은 수행하지 않았다.

### 5.3 백업/복원 문서

보류. 본 bundle에 운영 전 `backup_database.ps1` 권장을 기록했다.

### 5.4 AGENTS.md 보강

보류. 이번 작업 중 repo-level 규칙 변경 필요성은 확인되지 않았다.

## 6. 변경 파일 목록

| 파일 | 변경 요약 | 위험도 | 비고 |
| --- | --- | --- | --- |
| `backend/config.py` | 광고 슬롯 feature flag 설정 추가 | 낮음 | 기본 disabled |
| `backend/database/models.py` | `UserAuctionPreference` 모델 추가 | 중간 | 신규 테이블 |
| `backend/services/auction_items.py` | 공개 필터/정렬, 공고 요약 직렬화 | 중간 | 기존 unique 기준 유지 |
| `backend/services/user_auction_preferences.py` | 온비드 개인화 service 추가 | 중간 | 로그인 사용자 전용 |
| `backend/web/routers/auctions.py` | `/onbid`, preference POST/API, `/my/onbid/*` | 중간 | POST는 로그인 필수 |
| `backend/web/routers/cases.py` | `/cases` 공개 목록/상세 public DTO | 높음 | AI/raw 노출 경계 |
| `main_app.py` | 공개 홈, about/disclaimer/privacy, robots/sitemap | 낮음 | root 공개 전환 |
| `frontend/templates/auctions/*` | 공개 온비드 목록/상세와 내 목록 | 중간 | 광고 슬롯 하단 |
| `frontend/templates/cases/*` | 공개 회생/파산 목록/상세 | 높음 | 민감 필드 미사용 |
| `frontend/templates/public/*` | 공개 홈/고지 페이지 | 낮음 | 초안 문구 |
| `frontend/templates/shared/ad_slot.html` | 광고 partial | 낮음 | disabled 기본 |
| `tests/public_access_auth_boundary_test.py` | 공개/권한 경계 테스트 | 높음 | 민감 문자열 검증 |
| `tests/router_boundary_test.py` | 신규 route 등록 검증 | 낮음 | 기대 목록 확장 |
| `docs/migration_ledger.md` | v003 schema ledger 추가 | 중간 | 비파괴 신규 테이블 |
| `reports/devpacks/devpack_v003_result_bundle.md` | 본 결과 bundle | 낮음 | 신규 |
| `reports/project-result_current.md` | 최신 프로젝트 상태 | 낮음 | 신규 |

## 7. DB/마이그레이션 변경

- 신규 테이블: `user_auction_preferences`
- 신규 컬럼: 없음
- 비파괴 여부: 기존 테이블/컬럼/데이터 삭제 없음
- migration ledger 업데이트 여부: 완료, `docs/migration_ledger.md`
- rollback 방법: 코드 롤백으로 기존 조회 기능 유지. preference 데이터 삭제가 필요하면 DB 백업 복구 또는 별도 명시 절차 필요.

## 8. 권한 경계 표

| 사용자 상태 | 접근 가능 | 접근 불가 | 검증 방법 |
| --- | --- | --- | --- |
| 비로그인 | `/`, `/onbid`, `/onbid/{id}`, `/cases`, `/cases/{id}`, `/about`, `/disclaimer` | `/documents/raw/{id}`, `/api/admin/onbid-quality`, 온비드 preference POST 저장 | `tests/public_access_auth_boundary_test.py` |
| 로그인 | 온비드 preference 저장, `/my/onbid/*`, 기존 `/user` 회생/파산 분석 화면 | 타 사용자 preference 직접 접근 route 없음 | `tests/public_access_auth_boundary_test.py`, 기존 smoke |
| 관리자 | 기존 관리자 화면/API | 광고 노출 없음 | `tests/page_response_smoke_test.py`, `tests/onbid_module_test.py` |

## 9. 테스트 결과

| 명령 | 결과 | 비고 |
| --- | --- | --- |
| `& $Py -m py_compile main_app.py backend/database/models.py backend/database/session.py backend/web/routers/auctions.py backend/web/routers/cases.py backend/services/auction_items.py backend/services/user_auction_preferences.py tests/public_access_auth_boundary_test.py tests/router_boundary_test.py` | PASS | 문법 검증 |
| `& $Py tests/onbid_module_test.py` | PASS | ONBID item/notice/link |
| `& $Py tests/page_response_smoke_test.py` | PASS | page smoke |
| `& $Py tests/router_boundary_test.py` | PASS | route registration |
| `& $Py tests/isolated_operations_test.py` | PASS | 기존 role/action/OCR guard |
| `& $Py tests/public_access_auth_boundary_test.py` | PASS | v003 public/auth boundary |
| `.\run_onbid_scheduled_sync.ps1 -Sample -ApiKind notice -Limit 20 -MaxPages 1 -IncludeNoticeDetails -IncludeNoticeItems` | FAIL | PowerShell execution policy |
| `powershell -ExecutionPolicy Bypass -File .\run_onbid_scheduled_sync.ps1 -Sample -ApiKind notice -Limit 20 -MaxPages 1 -IncludeNoticeDetails -IncludeNoticeItems` | PASS | `status=SUCCEEDED`, sample notice 2, notice items 3, links updated 3 |
| local uvicorn start attempts | FAIL | `Start-Process`, `Start-Job`, Process API, `cmd start /B` 모두 이 도구 세션에서 서버 프로세스가 유지되지 않아 `http://127.0.0.1:8000/onbid` HTTP 확인 실패 |

최종 Git 확인:

```text
git status --short
=> M backend/config.py
=> M backend/database/models.py
=> M backend/services/auction_items.py
=> M backend/web/routers/auctions.py
=> M backend/web/routers/cases.py
=> M docs/migration_ledger.md
=> M frontend/templates/auctions/detail.html
=> M frontend/templates/auctions/index.html
=> M main_app.py
=> M tests/router_boundary_test.py
=> ?? backend/services/user_auction_preferences.py
=> ?? frontend/templates/auctions/my_list.html
=> ?? frontend/templates/cases/
=> ?? frontend/templates/public/
=> ?? frontend/templates/shared/
=> ?? reports/devpacks/devpack_v003_result_bundle.md
=> ?? reports/project-result_current.md
=> ?? tests/public_access_auth_boundary_test.py

git --no-pager log --oneline --decorate -5
=> e392e30 (HEAD -> codex/devpack-v003-public-first-personalization, origin/codex/devpack-v003-public-first-personalization) docs: add v003 devpack instructions
=> 48f47c7 (tag: baseline-v002-20260706, origin/main, main) baseline after devpack v002

git diff --cached --name-only | Select-String -Pattern ...
=> 출력 없음
```

## 10. 미완료/보류/리스크

| 항목 | 상태 | 이유 | 다음 조치 |
| --- | --- | --- | --- |
| 같은 공고의 다른 온비드 물건 표시 | 부분 보류 | 공고 요약은 구현, 같은 공고 물건 UX는 Core 안정화 후가 적절 | v004 필터/상세 고도화에서 처리 |
| 실제 AdSense 연동 | 보류 | 실제 client/slot id 없음 | v006에서 실제 설정 검증 |
| 실제 API probe | 보류 | 실제 API 키와 네트워크 호출 필요 | v004/v005에서 별도 probe |
| 동적 sitemap | 보류 | 공개 URL 정책과 데이터량 고려 필요 | v004 이후 |
| 정식 개인정보 처리방침 | 보류 | 운영 주체/문의처/보유기간 확정 필요 | 베타 전 법무/운영 검토 |

## 11. v004 추천 작업

- 온비드 같은 공고의 다른 물건 표시와 상세 필터 UX 보강.
- 실제 API 샘플 기반 normalizer 필드 품질 보강.
- 회생/파산 공개 검색 성능 개선.
- sitemap 동적 URL 정책 수립.
- 운영 DB 백업/복원 리허설.

## 12. Codex CLI 운영 메모

- 사용한 `/goal`: 없음
- approval 관련 특이사항: network/API 키 작업 없음. PowerShell script execution policy 때문에 `powershell -ExecutionPolicy Bypass -File ...`로 sample 스케줄러를 실행.
- 사용한 Python: `C:\Users\xogns\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`
- 긴 로그 위치: `storage/logs/onbid/onbid_scheduled_20260706_211303.log` (전체 로그는 bundle에 첨부하지 않음)
- 로컬 dev server: 이 도구 세션에서는 background uvicorn 프로세스가 유지되지 않아 URL 제공 불가. 기능 검증은 FastAPI `TestClient`로 완료.
