# Devpack v010 Beta Release Candidate Result Bundle

## 1. 작업 메타데이터

- 작업일: 2026-07-10 KST
- 기준 브랜치: `codex/devpack-v009-onbid-data-source-status-quality`
- 작업 브랜치: `codex/devpack-v010-beta-release-candidate-ux`
- 기준 커밋: `cc10db3 docs: finalize v009 result bundle`
- 구현 커밋: `cbf0323 feat: complete v010 beta release candidate ux`
- 목표: 외부 베타 사용자가 홈 → 목록 → 카테고리/필터 → 상세 → 관심/패스/메모 → 내 검토함을 별도 설명 없이 사용할 수 있는 RC 구축

## 2. 시작 Git 상태

```text
Git root: C:/Users/xogns/Documents/testAuction/court_auction_platform
Initial branch: codex/devpack-v009-onbid-data-source-status-quality
Initial status: 사용자 제공 v010 지시서 1개만 untracked
Remote: https://github.com/feastJ-h/court_auction_platform.git
```

v009 원격은 최신 상태였고 `git pull --ff-only` 후 v010 브랜치를 생성했다. `main`에는 작업하지 않았다.

## 3. 백업 정보

- Source DB: `auction_data.db`
- Backup: `storage/backups/auction_data_20260710_110441.db`
- SHA-256: `D0FD97632C840086AD6D983CD69AD8390531CBD09D091DC5F2C870DA03D3731B`
- 백업 시각: 2026-07-10 11:04:41 KST
- Restore: 실행하지 않음. schema/data migration이 없고 원본 DB를 변경하지 않았다.

## 4. v009 carry-forward

v009의 공개 freshness/sample 차단, KST 마감 보정, 원문 URL fallback, 관리자 데이터 품질 화면과 권한 경계를 유지했다. 이번 devpack은 추가 bulk fetch 없이 기존 1,076건으로 제품 흐름을 검증했다.

## 5. 변경 전 라이브 UI audit

지시서와 소스 audit에서 다음을 재확인했다.

- 카테고리 탭이 필터 폼 아래에 있고 category select와 중복됨
- 54개 페이지 번호 전체 렌더링
- 페이지 링크가 일부 필터만 보존
- 목록에서 패스 핵심 액션과 undo 부재
- 오늘 신규가 없으면 최근 20건으로 조용히 대체
- 홈 preview가 같은 유형/공고에 편중 가능
- public에 내부 review mode 기술 문구 노출
- Tailwind CDN 장애 시 스타일 전체 소실

변경 전 인앱 브라우저 캡처는 해당 세션의 브라우저 target 부재로 실행하지 못했다. 이후 검증은 독립 Playwright Chromium과 소스 비교로 수행했다.

## 6. 화면별 변경 요약

- 홈: count query 의미 일치, 최초 수집 기준, 수도권/가격 count 정정, 2+2 category preview, 3단계 첫 방문 안내
- ONBID 목록: 제목 바로 아래 category tabs, quick actions, responsive filter drawer, active chips, 결과 범위, 카드 계층, compact pagination
- 오늘 보기: `first_seen_at` 기준, silent fallback 제거, display-only diversity cap, 로그인/비로그인 summary 분리
- 상세: 공식 온비드 홈페이지와 번호 copy fallback, 모바일 action bar, 개인 정리 우선순위
- 내 검토함: 탭 count, 패스 복구, 관심 해제, 감시 해제, 메모 확인
- 회생·파산: 공통 compact pagination, filter label, overflow 방지
- 전역: beta banner, skip link, 공통 nav/footer/legal links, 로컬 정적 CSS

## 7. Category tabs 전/후

| 항목 | 변경 전 | 변경 후 |
| --- | --- | --- |
| 위치 | filter form 내부 하단 | 제목 바로 아래 sticky 가능 zone |
| 선택 수단 | select + tabs | tabs 1회, hidden state transport만 유지 |
| count | global 가능성 | category 이외 현재 조건을 반영한 faceted count |
| 모바일 | wrap 가능 | 한 줄 내부 가로 스크롤, 44px target |
| 기타 | 항상 노출 | count 1건 이상일 때만 노출 |

실데이터 count: 전체 1,076 / 부동산 516 / 동산 560 / 국유일반재산 0. 0건 탭은 stale row를 노출하지 않고 명시적 empty state를 표시한다.

## 8. Pagination 전/후

- 공통 helper: `backend/web/pagination.py`
- 공통 partial: `frontend/templates/shared/pagination.html`
- ONBID와 `/cases`에 적용
- Desktop: 첫/마지막 + 현재 앞뒤 2 + ellipsis + 이전/다음
- Mobile: `이전 · 현재 / 전체 · 다음`
- 1/54, 2/54, 27/54, 53/54, 54/54, 1/1, 4/7, 음수/초과를 unit test로 검증
- 실데이터 54페이지에서 전체 번호 렌더링이 사라졌음을 Playwright로 확인

## 9. Filter/query state 검증

`region`, `category`, `data_quality`, `price_min`, `price_max`, `closing_within_days`, `sort`, `q`, `status`, `agency`, `usage`, `has_notice`, `has_detail`을 공통 query builder가 보존한다. category/filter/sort 변경 시 page는 링크에서 제거되어 1로 초기화된다. 13개 query key는 parameterized pytest로 각각 검증했다.

## 10. Card UX 변경

- 유형/상태/D-day → 제목 → 위치/기관/관리번호 → 가격 → 마감 → 자료 상태 → 액션 순으로 재배치
- `자료 일부 확인 필요` 1개 summary badge만 사용
- 원문 URL이 없을 때 큰 disabled box를 제거하고 상세 fallback 한 줄만 표시
- 비로그인 카드마다 반복되던 큰 로그인 CTA를 목록 상단 안내 1회로 축약
- 로그인 카드는 관심/패스/상세를 직접 제공

## 11. Pass/undo 검증

- 패스는 `UserAuctionPreference.is_passed`만 갱신하며 item delete를 수행하지 않는다.
- 성공 즉시 카드 제거, `기본 목록에서 숨겼습니다` toast, 5초 undo 제공
- undo 성공 시 원래 DOM 위치 복원
- 요청 실패 시 카드 복원과 안전 오류 안내
- JS 비활성화 시 기존 POST/303 fallback 유지
- 연속 패스 시 최신 toast만 undo 대상으로 유지하며 이전 패스 상태는 서버에 유지
- 패스함 복구 E2E PASS

## 12. Today queue 기준 및 diversity

- 기준: DB 최초 insert `created_at`을 KST `first_seen_date`로 직렬화
- `freshness_date`를 오늘 신규로 오인하지 않음
- 오늘 0건이면 최근 자료를 오늘 자료로 대체하지 않고 별도 `최근 수집 항목 보기` 링크 제공
- queue 최대 20건, 같은 공고 최대 3, 같은 기관 최대 8
- 완료는 실제 queue 전부가 관심/패스로 분류된 경우만 표시
- 현재 실데이터 오늘 최초 수집 955건, diversity를 반영한 우선 20건 표시

## 13. Home count/preview 검증

- 오늘 처음 수집 955
- 7일 이내 마감 429
- 서울·경기·인천 현재 공개 340
- 최저입찰가 확인 및 1억 이하 728
- preview는 데이터가 존재할 때 부동산 2 + 동산 2를 우선하고 같은 공고 최대 1건으로 제한
- 추천/투자 평가 표현은 사용하지 않음

## 14. 내 검토함 E2E

임시 test DB와 실행 시 난수 계정을 사용했다. 계정/비밀번호는 코드, 로그, 결과서에 남기지 않았다.

```text
login → 관심 저장 → 패스 → 카드 제거 → undo → 재패스
→ 패스함 확인 → 복구 → 메모 작성 → 메모 탭 확인
```

전체 흐름 PASS. private memo는 공유 summary payload에 포함되지 않는 기존 경계를 유지했다.

## 15. Beta/review mode 분리

- Beta banner: 자료 지연/누락 가능성과 원문 최종 확인만 안내
- Review mode 내부 기술 문구는 관리자에게만 표시
- beta mode에서도 개인화 저장 허용
- beta/review noindex 정책은 설정값으로 중앙화

## 16. Header/footer/legal 업데이트

- 제품명은 `settings.product_name`으로 중앙화
- skip link, active nav, 모바일 내부 가로 스크롤 적용
- footer: 소개/약관/개인정보/면책/데이터 출처/오류 제보/기준일
- 약관·개인정보·면책 기준일을 2026-07-10으로 갱신
- 운영자 연락처는 임의 생성하지 않고 `준비 중`으로 표시

## 17. Security 점검

- Session: HttpOnly, SameSite=Lax, HTTPS Secure, 12시간 expiry, login마다 난수 sid, logout sid revoke
- CSRF: SameSite cookie + unsafe method의 Origin/Sec-Fetch-Site 동일 출처 검사. cross-site preference POST 403 검증
- Rate limit: login, 오류 제보/공유, original redirect, admin sync에 프로세스 내 sliding window 적용
- Headers: CSP, X-Content-Type-Options, X-Frame-Options/frame-ancestors, Referrer-Policy, Permissions-Policy, X-Robots-Tag
- 403/404/429/500: 한국어 안전 응답, stack/path/secret 비노출
- 한계: rate limit/session revoke store는 단일 프로세스 메모리 기반이므로 다중 인스턴스 전 Redis 등 공유 저장소로 교체 필요

## 18. Data sync/original fallback 점검

- 추가 bulk fetch 없음
- 공식 온비드 도메인 `https://www.onbid.co.kr/`을 확인하고 homepage fallback으로 사용
- 검증되지 않은 exact detail URL 조합 없음
- 온비드 번호/공매 번호/물건명 copy 제공
- API key/query secret은 URL, analytics, 결과서에 없음
- scheduler script와 기존 public data는 변경하지 않음

현재 데이터 audit:

```text
public visible: 1076
active/upcoming: 1015
real_estate: 516
movable: 560
national_property: 0
duplicate groups: 0
sample public: 0
stale/unknown public: 0
public status conflict: 0
last updated: 2026-07-10 07:46 KST
```

v009의 1,016 active count보다 1건 적은 것은 검증 시각 경과로 한 deadline이 마감된 결과다.

## 19. 접근성 결과

- axe-core WCAG 2 A/AA 자동 검사
- 홈, ONBID 전체/category, 오늘 보기, 상세, 로그인, 내 검토함, 회생·파산, 약관, 개인정보
- critical: 0
- serious: 0
- 수정한 항목: 보조문구 contrast, cases select label, breadcrumb link 비색상 구분

## 20. Responsive viewport 결과

검증 viewport: 360×800, 390×844, 768×1024, 1024×768, 1440×900.

- body horizontal overflow: 전 route 0
- category tabs 내부 overflow만 허용
- 768/1024에서는 filter drawer, 1440에서는 inline compact filter
- mobile pagination 한 줄 유지
- QA screenshot 24개와 로그인 screenshot 1개를 `storage/qa/v010`에 생성했으며 커밋하지 않음

## 21. Lighthouse/성능 결과

Lighthouse 점수는 실행하지 않았다. 대신 동일 Chromium의 로컬 navigation timing과 asset audit를 수행했다.

```text
home navigation: 952.0 ms
onbid navigation: 388.2 ms
today navigation: 227.0 ms
compiled app.css: 28,204 bytes
Tailwind CDN reference: 0
```

로컬 CSS 빌드로 CDN 장애 시 무스타일 화면이 되는 문제를 제거했다. `caniuse-lite` 업데이트 경고는 남지만 빌드/실행에는 영향이 없다.

## 22. Pytest 수집 수와 결과

```text
python -m pytest -m "not integration and not external and not visual"
60 collected / 2 deselected / 58 selected
58 passed
```

legacy executable 파일은 import 시 DB 환경을 변경하므로 `tests/conftest.py`가 pytest function 없는 파일을 collect-ignore하고 beta runner가 별도 프로세스로 실행한다.

## 23. Script/legacy test 결과

`run_beta_qa.ps1` 포함 기본 4종 PASS:

- `onbid_module_test.py`
- `page_response_smoke_test.py`
- `router_boundary_test.py`
- `isolated_operations_test.py`

추가로 auth/review/security header/copy/mojibake/legal/navigation/home/today/analytics/share 계열 13개 script를 실행했고, 변경된 홈 label에 맞춰 stale expectation 1건을 갱신한 뒤 모두 PASS했다.

## 24. Playwright E2E 결과

```text
python -m pytest -m visual
2 passed
```

- Public: 10개 route × 5 viewport, status/overflow/tabs/pagination/axe 검증
- Login: 관심, 패스, undo, 패스함 복구, 메모 저장 검증
- 실제 Chromium headless 사용

## 25. Cloudflare 외부 URL QA

사용한 임시 URL:

```text
https://nine-respect-archived-subsidiary.trycloudflare.com
```

동일 실행 내 uvicorn + tunnel 검증 결과:

- `/`, `/onbid`, 3 category, `/onbid/today`, `/cases`, `/terms`, `/privacy`, `/disclaimer`: 200
- `/admin/onbid-data-quality`: 303 login redirect
- 모든 응답: `X-Robots-Tag: noindex, noarchive`
- 최초 502는 셸 종료 시 uvicorn이 정리된 실행환경 문제였고 동일 실행 검증으로 해소
- cloudflared/uvicorn 종료 확인: 0 process, port 8000 listener 0
- named tunnel 자격증명/DNS는 없으므로 만들지 않음. 고정 beta URL은 사전 생성 named tunnel + DNS 권한을 준비한 뒤 동일 uvicorn origin으로 연결해야 함

## 26. 개인정보/secret/raw exposure 점검

- `.env`, DB, backup, storage, log, runtime settings staged 0
- screenshot/browser profile/session file commit 0
- raw payload/internal path/OCR 전문 public serializer 노출 0
- analytics는 event/item/category/page/sort/boolean만 허용하고 note, memo, URL, raw payload를 제거
- npm audit: vulnerability 0

## 27. 변경 파일 목록

주요 구현:

- `backend/web/pagination.py`
- `backend/services/onbid_review.py`
- `backend/web/routers/auctions.py`
- `backend/web/routers/cases.py`
- `backend/services/auction_items.py`
- `backend/services/product_engagement.py`
- `main_app.py`
- `frontend/static/app.css`, `beta.js`, `tailwind.input.css`
- `frontend/templates/shared/{pagination,toast,public_nav,legal_footer_links,onbid_category_tabs}.html`
- ONBID/home/cases/legal 핵심 templates
- 전체 template의 Tailwind CDN을 `/static/app.css`로 교체
- `package.json`, `package-lock.json`, `tailwind.config.js`
- `pytest.ini`, `tests/conftest.py`, v010 unit/contract/Playwright tests
- `run_beta_qa.ps1`

DB schema 변경이 없어 `docs/migration_ledger.md`는 변경하지 않았다.

## 28. 남은 리스크

- direct official item URL coverage 0%; homepage + copy fallback만 제공
- 국유일반재산 fresh public row 0
- 고정 beta URL/DNS 미구성
- 분산 rate limit/session revoke store 미구성
- Lighthouse 정량 점수 미측정
- FastAPI `on_event`와 TestClient compatibility deprecation warning
- Tailwind browserslist data update warning

## 29. 베타 판정

**조건부 베타 오픈 가능**

근거: 핵심 탐색/소거/복구/저장 흐름, public/auth/admin 경계, 58 unit/contract, 2 Playwright, 외부 route, axe/overflow가 모두 통과했다. 조건은 고정 staging URL, beta 운영 계정 정책, 공유 rate limit store 또는 단일 인스턴스 유지, 장애 모니터링 준비다.

## 30. 다음 devpack 추천

1. Named Cloudflare staging URL과 운영 health/alert
2. Redis 기반 session revoke/rate limit
3. 공식 ONBID 검색 deep-link 소량 검증
4. 국유일반재산 날짜 normalization
5. Lighthouse CI와 FastAPI lifespan/TestClient deprecation 정리

## 31. 종료 Git 상태

- 구현과 문서 커밋 완료 후 clean worktree 확인
- 최종 sensitive staged-file scan과 `git diff --check` PASS
- storage QA/DB/log는 ignored 상태 유지

## 32. Commit/push 결과

- 구현 commit: `cbf0323 feat: complete v010 beta release candidate ux`
- 문서 commit: `21a17a1 docs: add v010 beta rc result bundle`
- Push: `origin/codex/devpack-v010-beta-release-candidate-ux` 생성 및 upstream 설정 성공
- `main` merge/push: 수행하지 않음
