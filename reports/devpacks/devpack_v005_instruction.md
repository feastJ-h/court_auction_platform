# Codex 개발팩 v005 작업 지시서

## Product QA, Fresh ONBID Data, Navigation Repair & Safe Review Pack

- 작성일: 2026-07-06
- 대상 저장소: `C:\Users\xogns\Documents\testAuction\court_auction_platform`
- 원격 저장소: `https://github.com/feastJ-h/court_auction_platform.git`
- 기준 브랜치: `codex/devpack-v004-real-onbid-operations`
- 기준 커밋: `913aece feat: implement real onbid operations v004`
- 권장 작업 브랜치: `codex/devpack-v005-product-qa-fresh-data-navigation`
- 지시서 위치: `reports/devpacks/devpack_v005_instruction.md`
- 최종 결과 bundle 위치: `reports/devpacks/devpack_v005_result_bundle.md`
- 최신 프로젝트 상태 문서: `reports/project-result_current.md`
- 마이그레이션 장부: `docs/migration_ledger.md`

이 개발팩은 단발성 UI 수정이 아니라, v004에서 실제 ONBID API 연결까지 성공한 뒤 발견된 제품성 문제를 상용화 전 단계에서 최대한 정리하기 위한 장시간 통합팩이다.

v004는 실제 ONBID API를 `Limit=20`, `MaxPages=1`로 연결하고, 공개 ONBID 카테고리, 국유일반재산 독립 카테고리, 정보 부족 badge, 같은 공고 다른 물건, 관리자 관찰성, restore/scheduler/log-retention dry-run helper, `/privacy`, `/terms`, `robots.txt`, `sitemap.xml`까지 추가했다. 그러나 v004 이후 실제 화면과 데이터에서 다음 문제가 확인되었다.

```text
1. ONBID API에서 2003년 같은 오래된 데이터가 들어올 수 있다.
2. 2025년 이전 데이터는 현재 서비스 목적상 공개 탐색 가치가 낮다.
3. 부동산/동산/국유일반재산 메뉴와 탭 active 상태가 일부 화면에서 일관되지 않다.
4. 카테고리는 아직 service-derived 중심이고, 대량 데이터/탭 count/성능/정렬에는 저장형 파생 필드가 필요할 수 있다.
5. 상용화 단계로 가기에는 UI polish, QA, 보안, 운영 리허설, 외부 리뷰 구조가 부족하다.
6. ChatGPT나 외부 리뷰어가 `127.0.0.1`을 직접 볼 수 없으므로, 안전한 review mode와 임시 tunnel 구조가 필요하다.
```

따라서 v005의 목표는 “새 외부 연동을 붙이는 것”이 아니라, **공개 베타 직전 제품 QA, 데이터 신뢰도, 탐색 UX, 운영 리허설, 안전한 외부 검토 준비**를 한 번에 크게 끌어올리는 것이다.

---

# 0. 최상위 목표

v005의 최상위 목표는 다음 한 문장으로 정의한다.

```text
ONBID 공개 데이터는 2025-01-01 이후의 유효한 물건만 기본 수집·표시하고,
전체 nav/menu active 상태와 ONBID 카테고리 UX를 URL·데이터·화면·테스트에서 일관되게 고치며,
상용화 전 제품 QA·보안·운영 리허설·외부 리뷰 mode를 안전하게 준비한다.
```

제품 방향:

```text
Fresh ONBID:
  공개 /onbid는 기본적으로 2025-01-01 이후 입찰/공고 데이터만 보여준다.

Navigation consistency:
  홈, 온비드, 회생/파산, 내 온비드, 관리자, 각 카테고리 tab의 active 상태가 모든 주요 route에서 일관된다.

Public review readiness:
  외부 리뷰용 review mode를 제공하되, raw/internal/admin mutation/real sync/API key 노출을 막는다.

Operations rehearsal:
  scheduler, backup/restore, log retention, run history, sitemap, security, legal draft를 상용화 전 점검 가능한 상태로 만든다.

No external integration:
  알림, 이메일, web push, SMS, 실제 AdSense 송출, 결제, 낙찰결과 외부 연동은 구현하지 않는다.
```

---

# 1. v005 범위 요약

## 1.1 v005에 반드시 포함할 것

이번 v005는 아래 항목을 모두 포함한다.

```text
제품/UX:
- 전체 nav/menu active 수리
- 공통 header/nav partial화
- 카테고리 탭 count
- 필터 chip/초기화
- 지역 preset active
- 가격 preset active
- 상세 breadcrumb
- 공개 route visual smoke 테스트
- 모바일/접근성 1차 QA

데이터 신뢰도:
- 2025년 이후 데이터 freshness gate
- stale 데이터 audit/hide
- 기존 2025 이전 row 삭제 금지
- 신규 sync/probe에서 2025 이전 payload accepted_fresh 금지
- ONBID date field mapping 보강
- category 저장 컬럼/인덱스 검토 또는 비파괴 추가
- sitemap fresh public item만 포함

운영/관리자:
- staging/preview tunnel 정식화
- review mode + Cloudflare/ngrok tunnel 준비
- Windows Scheduler 실제 등록 리허설 강화
- 운영 DB backup/restore 리허설 강화
- 관리자 run history 화면
- failed sync alert 후보 설계, 단 실제 알림 발송 구현 금지
- 관리자 readiness dashboard 강화
- API key configured 여부는 값 없이 표시

보안/상용화 전 QA:
- privacy/terms/disclaimer 정식화, 단 법률 검토 완료처럼 쓰지 않기
- rate limit / CSRF / session 보안 점검 및 가능한 범위 구현
- raw payload/internal path/OCR/AI public boundary 재검증
- review URL noindex/noarchive
- tunnel 사용 안전 runbook
- Lighthouse/접근성/모바일 QA 체크리스트 또는 가능한 자동화
```

## 1.2 v005에서 제외할 것

다음은 명시적으로 제외한다.

```text
외부 연동:
- 이메일 발송 구현
- 알림 발송 구현
- web push 구현
- SMS/카카오/슬랙/디스코드 등 외부 메시징 구현
- 실제 AdSense client/slot 운영 연동
- 결제/구독/과금
- 낙찰결과/AuctionResult 본 구현
- 외부 운영 배포 자동화
- Cloudflare/ngrok 설치 자동화
- tunnel을 Codex가 임의로 실행하여 외부 공개하는 행위

데이터:
- 대량 전체 백필
- 기존 DB row 자동 삭제
- storage/raw/processed 원문 삭제
- raw payload 공개
- API key 출력/로그/문서화

Git/DB:
- main 직접 작업
- destructive migration
- `git reset --hard`
- `git clean -fd/-fdx`
- `.env`, DB, storage, logs 커밋
```

## 1.3 외부 연동 관련 특별 원칙

v005에서는 외부 연동을 “설계”할 수는 있으나 “실제 전송”은 구현하지 않는다.

허용:

```text
- failed sync alert 후보 설계서 작성
- 관리자 화면에 “알림 미구현 / 후보 설계 있음” 표시
- 알림 event 후보, trigger 후보, rate limit 후보 정리
- future integration interface 초안 작성, 단 실제 네트워크 전송 없음
```

금지:

```text
- SMTP 설정 추가
- 이메일 발송 코드 추가
- Slack/Discord webhook 호출 코드 추가
- browser push service worker 구현
- 외부 알림 API 호출
- 사용자 알림 수신 동의 저장 구조 본 구현
```

---

# 2. 작업 시작 전 필수 절차

## 2.1 브랜치 생성

사용자가 먼저 PowerShell에서 아래를 실행해 v005 브랜치를 만든다.

```powershell
cd C:\Users\xogns\Documents\testAuction\court_auction_platform

git checkout codex/devpack-v004-real-onbid-operations
git pull --ff-only

git checkout -b codex/devpack-v005-product-qa-fresh-data-navigation

git branch --show-current
git --no-pager log --oneline --decorate -5
git status --short
```

정상 기대:

```text
Branch: codex/devpack-v005-product-qa-fresh-data-navigation
Base includes: 913aece feat: implement real onbid operations v004
status: clean
```

## 2.2 지시서 파일 추가

사용자가 이 문서를 아래 경로에 저장한다.

```text
reports/devpacks/devpack_v005_instruction.md
```

저장 후 지시서 커밋을 먼저 만든다.

```powershell
git add reports/devpacks/devpack_v005_instruction.md
git commit -m "docs: add v005 devpack instructions"
git push -u origin codex/devpack-v005-product-qa-fresh-data-navigation
```

이후 Codex CLI가 구현 작업을 수행한다.

## 2.3 Codex 작업 시작 직후 필수 확인

Codex는 작업 시작 직후 아래 명령을 실행하고 결과를 `devpack_v005_result_bundle.md`에 기록한다.

```powershell
git rev-parse --show-toplevel
git branch --show-current
git status --short
git remote -v
git --no-pager log --oneline --decorate -8
git merge-base --is-ancestor 913aece HEAD
if ($LASTEXITCODE -eq 0) {
    "OK: v004 final commit is included"
} else {
    "ERROR: v004 final commit is NOT included"
}
```

정상 기대값:

```text
Git root: C:/Users/xogns/Documents/testAuction/court_auction_platform
Branch: codex/devpack-v005-product-qa-fresh-data-navigation
Remote: https://github.com/feastJ-h/court_auction_platform.git
v004 final commit included: yes
Work start status: clean
```

다음이면 기능 개발을 중단하고 result bundle에 기록한다.

```text
- Git root가 예상 경로가 아니다.
- 현재 브랜치가 main이다.
- v004 final commit 913aece가 현재 브랜치 조상에 없다.
- git status --short에 사용자 변경분이 있고 지시서에 처리 기준이 없다.
- .env, DB, storage, logs, runtime 파일이 stage되어 있다.
- git init이 필요해 보인다.
```

## 2.4 AGENTS.md 읽기

Codex는 `AGENTS.md`를 먼저 읽고 따른다.

지시서와 AGENTS.md가 충돌하면:

```text
- v005 지시서가 v005 기능 범위에서 우선한다.
- 보안/금지 규칙은 더 엄격한 쪽을 따른다.
- 외부 연동 금지, 민감 파일 금지, raw/public boundary 금지는 절대 완화하지 않는다.
```

---

# 3. 절대 금지 사항

Codex는 아래를 절대 수행하지 않는다.

```text
Git:
- git init
- main 직접 개발
- git reset --hard
- git clean -fd
- git clean -fdx
- .git 삭제
- 사용자가 명시하기 전 commit/push
- 기존 브랜치 강제 덮어쓰기

민감 파일:
- .env 출력/수정/커밋
- API key 출력/로그/문서화
- *.db, *.sqlite, *.sqlite3 커밋
- storage/ 커밋
- logs/ 커밋
- runtime_settings.json 커밋
- raw payload dump를 reports/docs에 기록

DB:
- 기존 row 자동 삭제
- destructive migration
- 컬럼/테이블 삭제
- storage/raw 또는 processed 문서 삭제
- restore 실제 적용을 confirm 없이 수행

보안:
- 회생/파산 AI 분석 비로그인 공개
- OCR full text 비로그인 공개
- 내부 raw file path 공개
- /documents/raw 비로그인 공개
- admin API public 공개
- review mode에서 admin mutation 허용

외부 연동:
- 이메일 발송 구현
- web push 구현
- SMS/카카오/Slack/Discord webhook 구현
- 실제 AdSense 연동
- 결제/구독 구현
- 낙찰결과/AuctionResult 본 구현
- 외부 production deployment 자동 수행

운영:
- Windows Scheduler 실제 등록을 Codex가 자동 수행
- Cloudflare/ngrok tunnel을 Codex가 자동 실행하여 외부 공개
- real API 대량 백필
- Limit > 20, MaxPages > 1 실제 API 호출
```

---

# 4. 작업 방식

v005는 Core, Extended, Stretch의 순서로 진행하되, 사용자는 “많은 부분을 최대한 진행”하기를 원한다. 따라서 Codex는 Core 완료 후 멈추지 말고 Extended와 Stretch를 가능한 범위까지 진행한다.

```text
Core Scope:
  반드시 완료해야 하는 제품 QA/데이터 신뢰도/메뉴 수리/리뷰 모드.

Extended Scope:
  상용화 전 운영 리허설, 보안, 관리자, sitemap, visual QA.

Stretch Scope:
  모바일/접근성 polish, Lighthouse/manual QA, 추가 route inventory, AGENTS 보강.
```

중간 결과 문서는 만들지 않는다.

최종 결과는 반드시 하나로 통합한다.

```text
reports/devpacks/devpack_v005_result_bundle.md
```

다음 파일도 필요에 따라 갱신한다.

```text
reports/project-result_current.md
docs/migration_ledger.md
AGENTS.md
```

---

# Core Scope

---

# 5. Core 1: 전체 구조 inventory 작성

## 5.1 목표

현재 앱의 route, template, nav, auth boundary를 먼저 inventory로 파악한다. 메뉴 active 문제는 부분 수정으로 접근하면 계속 새는 경향이 있으므로, v005에서는 전체 구조를 표로 먼저 고정한다.

## 5.2 Codex 작업

다음 항목을 조사하고 result bundle에 기록한다.

```text
Route Inventory:
- public routes
- login-required routes
- admin routes
- raw/internal routes
- API routes
- POST/mutation routes

Template Inventory:
- public templates
- auctions templates
- cases templates
- my/user templates
- admin templates
- shared partials
- legal/SEO templates

Navigation Matrix:
- URL
- login state
- expected active_section
- expected active_subsection
- expected active_category
- current result
- fixed result

Security Boundary Matrix:
- anonymous allowed?
- login required?
- admin required?
- raw/AI/OCR/internal field exposure risk?
```

## 5.3 결과 bundle 기록 형식

`devpack_v005_result_bundle.md`에 아래 섹션을 둔다.

```markdown
## Route / Template / Navigation Inventory

| URL | Method | Auth | Template/API | Expected active | Result |
| --- | --- | --- | --- | --- | --- |
| / | GET | public | public/home | home | pass/fixed |
| /onbid | GET | public | auctions/index | onbid + all | pass/fixed |
| /onbid?category=real_estate | GET | public | auctions/index | onbid + real_estate | pass/fixed |
| /onbid?category=movable | GET | public | auctions/index | onbid + movable | pass/fixed |
| /onbid?category=national_property | GET | public | auctions/index | onbid + national_property | pass/fixed |
| /cases | GET | public | cases/index | cases | pass/fixed |
| /my/onbid/favorites | GET | login | auctions/my_list | my + favorites | pass/fixed |
| /admin/collection | GET | admin | admin/collection | admin + collection | pass/fixed |
```

## 5.4 산출물

가능하면 아래 artifact를 생성하되 Git에는 꼭 커밋하지 않아도 된다. 커밋 대상이 아니라면 `storage/review/` 아래에 둔다.

```text
storage/review/v005_route_inventory.json
storage/review/v005_navigation_matrix.json
```

최종 bundle에는 요약만 통합한다.

---

# 6. Core 2: 공통 nav/header partial화

## 6.1 목표

각 템플릿마다 header/nav를 복사해 둔 상태를 줄이고, active state를 공통 로직으로 통제한다.

## 6.2 신규/수정 partial 후보

가능한 범위에서 다음 shared partial을 만든다.

```text
frontend/templates/shared/base_head.html
frontend/templates/shared/public_nav.html
frontend/templates/shared/onbid_category_tabs.html
frontend/templates/shared/filter_chips.html
frontend/templates/shared/admin_nav.html
frontend/templates/shared/my_nav.html
frontend/templates/shared/review_banner.html
frontend/templates/shared/breadcrumbs.html
frontend/templates/shared/empty_state.html
frontend/templates/shared/ad_slot.html
```

기존 `shared/ad_slot.html`은 유지한다.

## 6.3 라우터 context 표준

각 route는 template에 아래 context를 명시적으로 넘긴다.

```python
{
    "active_section": "onbid",
    "active_subsection": "",
    "active_category": "real_estate",
    "page_title": "...",
    "breadcrumbs": [...],
    "review_mode": settings.review_mode,
}
```

권장 active_section 값:

```text
home
onbid
cases
my
admin
legal
auth
```

권장 active_category 값:

```text
all
real_estate
movable
national_property
other
```

권장 active_subsection 값:

```text
favorites
passed
watching
notes
collection
operations_readiness
run_history
users
```

## 6.4 금지

```text
- URL 문자열을 템플릿마다 제각각 비교하지 않는다.
- 결과 count가 0이라는 이유로 active category를 all로 되돌리지 않는다.
- 로그인/관리자 메뉴를 public partial에서 권한 체크 없이 표시하지 않는다.
- admin 페이지에 광고 partial을 include하지 않는다.
```

---

# 7. Core 3: nav/menu active state 전면 수정

## 7.1 목표

모든 주요 route에서 메뉴 active 상태가 정확해야 한다.

## 7.2 필수 검증 URL

아래 URL은 테스트로 고정한다.

```text
GET /
GET /onbid
GET /onbid?category=real_estate
GET /onbid?category=movable
GET /onbid?category=national_property
GET /onbid?category=other
GET /onbid?region=서울&category=real_estate
GET /onbid?price_max=100000000&category=movable
GET /onbid/{auction_item_id}
GET /cases
GET /cases/{event_id}
GET /about
GET /privacy
GET /terms
GET /disclaimer
GET /my
GET /my/onbid/favorites
GET /my/onbid/passed
GET /my/onbid/watching
GET /admin
GET /admin/collection
GET /admin/operations-readiness 또는 해당 섹션
GET /admin/onbid-runs 또는 해당 run history route
```

## 7.3 필수 규칙

```text
/ -> home active
/onbid -> onbid active, category all active
/onbid?category=real_estate -> onbid active, 부동산 tab active
/onbid?category=movable -> onbid active, 동산 tab active
/onbid?category=national_property -> onbid active, 국유일반재산 tab active
/onbid?category=other -> onbid active, 기타 tab active
/onbid/{id} -> onbid active, breadcrumb 표시
/cases -> cases active
/cases/{id} -> cases active, breadcrumb 표시
/my/onbid/favorites -> my active, favorites active
/my/onbid/passed -> my active, passed active
/my/onbid/watching -> my active, watching active
/admin/collection -> admin active, collection active
/admin/operations-readiness -> admin active, operations_readiness active
/admin/onbid-runs -> admin active, run_history active
```

결과가 0건이어도 active state는 URL/query 기준으로 유지한다.

## 7.4 테스트

신규 테스트 후보:

```text
tests/navigation_active_state_test.py
tests/onbid_public_filter_state_test.py
```

테스트는 가능하면 HTML에 안정적인 test marker를 넣고 검사한다.

권장 marker:

```html
data-active-section="onbid"
data-active-category="movable"
data-active-subsection="favorites"
aria-current="page"
```

필수 assertion:

```text
- /onbid?category=movable 결과가 0건이어도 data-active-category="movable"
- /onbid/{id}에서 data-active-section="onbid"
- /cases/{id}에서 data-active-section="cases"
- /admin/collection에서 data-active-section="admin"
```

---

# 8. Core 4: ONBID 2025 freshness policy

## 8.1 정책

v005부터 공개 ONBID 기본 목록은 2025년 이후 데이터만 표시한다.

```text
ONBID_MIN_PUBLIC_DATE = 2025-01-01
```

의미:

```text
2025-01-01 포함
2024-12-31 이전 제외
날짜 판단 불가 item은 public 기본 목록 제외
기존 DB row는 삭제하지 않고 stale/audit/hide
신규 real sync/upsert에서는 2025 이전 payload를 accepted_fresh로 처리하지 않음
```

설정 후보:

```text
ONBID_MIN_PUBLIC_DATE=2025-01-01
ONBID_PUBLIC_HIDE_STALE=true
ONBID_PUBLIC_HIDE_UNKNOWN_DATE=true
```

## 8.2 날짜 판단 우선순위

물건의 최신성은 수집일이 아니라 공매 자체 날짜로 판단한다.

우선순위:

```text
1. bid_end_at / cltrBidEndDt / 입찰마감일
2. bid_start_at / cltrBidBgngDt / 입찰시작일
3. notice_date / pbancDt / 공고일
4. open_bid_at / opengDt / 개찰일
5. 기타 API별 실제 날짜 필드
```

금지:

```text
updated_at만으로 fresh 판단 금지
created_at만으로 fresh 판단 금지
수집 시각만으로 fresh 판단 금지
```

이유:

```text
2003년 물건을 2026년에 수집하면 updated_at은 최신처럼 보일 수 있다.
공개 탐색 기준은 공매 데이터의 입찰/공고 날짜여야 한다.
```

## 8.3 서비스 함수 후보

```python
ONBID_MIN_PUBLIC_DATE = date(2025, 1, 1)

def extract_onbid_relevant_date(item_or_payload) -> tuple[date | None, str]:
    ...

def is_onbid_fresh(item_or_payload, cutoff: date = ONBID_MIN_PUBLIC_DATE) -> tuple[bool, str]:
    ...

def build_onbid_freshness_badge(item_or_payload) -> dict:
    ...
```

반환 예:

```python
{
    "public_date": "2025-03-14",
    "date_source": "bid_end_at",
    "is_fresh": True,
    "is_stale": False,
    "is_unknown_date": False,
    "reason": "fresh"
}
```

## 8.4 public query 적용

`/onbid` 기본 query는 다음 조건을 적용한다.

```text
source = ONBID
onbid_public_date >= 2025-01-01
exclude stale
exclude unknown date
category = query category or all
region/price filters preserved
sort = closing_soon 또는 newest_public_date
```

단, admin/debug route에서는 stale/unknown도 확인 가능해야 한다.

## 8.5 UI 안내

`/onbid` 상단 또는 filter area에 문구를 추가한다.

```text
공개 목록은 2025-01-01 이후 입찰/공고 데이터만 기본 표시합니다.
오래된 데이터와 날짜 확인 불가 데이터는 관리자 audit에서 확인할 수 있습니다.
```

## 8.6 테스트

신규 테스트:

```text
tests/onbid_freshness_policy_test.py
```

필수 assertion:

```text
- 2003-xx-xx payload는 stale
- 2024-12-31 payload는 stale
- 2025-01-01 payload는 fresh
- 2026-xx-xx payload는 fresh
- 날짜 확인 불가 payload는 unknown_date
- public /onbid 기본 목록에 stale item 미노출
- public /onbid 기본 목록에 unknown date item 미노출
- admin metrics에는 stale/unknown count 노출
```

---

# 9. Core 5: ONBID fresh API probe

## 9.1 목표

ONBID API가 날짜 파라미터를 지원하는지 확인하고, 지원하지 않거나 무시하면 local freshness gate로 방어한다.

## 9.2 신규 스크립트 후보

```text
run_onbid_fresh_probe.ps1
```

명령 예:

```powershell
powershell -ExecutionPolicy Bypass -File .\run_onbid_fresh_probe.ps1 -ApiKind real_estate -Limit 20 -MaxPages 1 -MinDate 2025-01-01
powershell -ExecutionPolicy Bypass -File .\run_onbid_fresh_probe.ps1 -ApiKind movable -Limit 20 -MaxPages 1 -MinDate 2025-01-01
powershell -ExecutionPolicy Bypass -File .\run_onbid_fresh_probe.ps1 -ApiKind notice -Limit 20 -MaxPages 1 -MinDate 2025-01-01
powershell -ExecutionPolicy Bypass -File .\run_onbid_fresh_probe.ps1 -ApiKind national_property -Limit 20 -MaxPages 1 -MinDate 2025-01-01
```

## 9.3 제한

```text
Limit 기본 20
MaxPages 기본 1
API key 값 출력 금지
raw payload 전체 출력 금지
응답 field key 후보만 요약
```

## 9.4 기록할 통계

```text
api_kind
min_date
requested_date_params
server_date_filter_supported
server_date_filter_reliable
fetched
accepted_fresh
dropped_stale_before_min_date
dropped_missing_relevant_date
inserted
updated
duplicates
failed
date_source_distribution
oldest_relevant_date
newest_relevant_date
api_key_value_printed=false
```

## 9.5 실패 처리

```text
API가 실패해도 v005 전체를 중단하지 않는다.
key 값 없이 status/code/error class 중심으로 result bundle에 기록한다.
sample/fixture/local freshness tests는 계속 진행한다.
```

---

# 10. Core 6: sync/upsert freshness gate

## 10.1 목표

앞으로 신규 sync에서 2025 이전 데이터가 기본 공개 DB row로 늘어나지 않게 한다.

## 10.2 worker/script 변경

대상 후보:

```text
backend/workers/onbid_sync.py
backend/onbid/client.py
backend/services/auction_items.py
run_onbid_scheduled_sync.ps1
run_onbid_probe.ps1
run_onbid_fresh_probe.ps1
```

옵션 추가:

```text
-MinDate 2025-01-01
--min-date 2025-01-01
--include-stale-for-audit  기본 false
```

기본값:

```text
MinDate = 2025-01-01
```

## 10.3 저장 정책

```text
신규 real sync:
  2025 이전 payload는 기본적으로 AuctionItem upsert하지 않는다.
  날짜 확인 불가 payload도 기본적으로 public AuctionItem upsert하지 않는다.
  단, stats에는 dropped_*로 기록한다.

sample/test:
  stale fixture는 테스트를 위해 isolated DB에 넣을 수 있다.

기존 DB:
  삭제하지 않는다.
  public query에서 숨긴다.
  admin audit에 집계한다.
```

## 10.4 통계 추가

sync result에 아래 값을 추가한다.

```text
fetched
accepted_fresh
dropped_stale_before_min_date
dropped_missing_relevant_date
inserted
updated
duplicates
failed
oldest_relevant_date
newest_relevant_date
```

## 10.5 result bundle 기록

실제 API 호출 결과는 아래 표로 기록한다.

```markdown
| API kind | Limit | MaxPages | MinDate | Fetched | Accepted fresh | Dropped stale | Dropped unknown date | Inserted | Updated | Duplicates | Notes |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
```

---

# 11. Core 7: 기존 DB stale audit/hide/repair

## 11.1 목표

v004 실제 API 호출로 들어온 2003년 등 오래된 row가 공개 목록에 나오지 않게 하고, 기존 DB 상태를 audit한다.

## 11.2 신규 스크립트 후보

```text
audit_onbid_freshness.ps1
repair_onbid_derived_fields.ps1
```

기본 dry-run:

```powershell
powershell -ExecutionPolicy Bypass -File .\audit_onbid_freshness.ps1 -MinDate 2025-01-01
powershell -ExecutionPolicy Bypass -File .\repair_onbid_derived_fields.ps1 -DryRun -MinDate 2025-01-01
```

실제 repair는 DB 백업 후에만 가능하다.

```powershell
powershell -ExecutionPolicy Bypass -File .\backup_database.ps1
powershell -ExecutionPolicy Bypass -File .\repair_onbid_derived_fields.ps1 -Apply -MinDate 2025-01-01
```

Codex는 `-Apply`를 임의 실행하지 않는다. 필요하면 result bundle에 사용자 실행 명령으로 제시한다.

## 11.3 audit 항목

```text
total_onbid_items
fresh_count
stale_before_min_date_count
unknown_date_count
oldest_relevant_date
newest_relevant_date
category별 fresh/stale/unknown
api_kind/source_api별 fresh/stale/unknown
stale 대표 item id/cltr_mng_no/date_source/public_date, 단 raw payload 미출력
```

## 11.4 repair 항목

비파괴 컬럼을 추가한 경우에만 repair가 의미 있다.

```text
onbid_category
onbid_public_date
onbid_date_source
onbid_is_stale
```

삭제 금지:

```text
DELETE FROM auction_items 금지
storage 삭제 금지
raw payload 삭제 금지
```

---

# 12. Core 8: category 저장 컬럼/인덱스 검토 또는 추가

## 12.1 배경

v004에서는 `national_property`가 service-derived였고 신규 컬럼/인덱스는 없었다. v005에서는 public category tab, count, freshness filter, sitemap, admin metrics가 중심 기능이 되므로 저장형 파생 필드가 필요할 가능성이 높다.

## 12.2 우선 판단 기준

Codex는 먼저 현재 schema와 query 성능을 확인한다.

```text
- category filter가 raw_payload LIKE에 과도하게 의존하는가?
- 2025 freshness filter가 raw_payload/date parsing 반복에 의존하는가?
- category tab count 계산이 전체 row scan인가?
- sitemap fresh item 조회가 느려질 가능성이 높은가?
```

컬럼 없이 안정적이고 빠르게 구현 가능하면 service-derived 유지 가능하다.

하지만 다음이면 비파괴 컬럼/인덱스 추가를 권장한다.

```text
- public query에서 stale hide가 불안정함
- category count가 매번 raw_payload scan
- large synthetic test에서 느림
- admin freshness/category metrics가 전체 스캔
```

## 12.3 권장 신규 컬럼

추가 시 비파괴 방식으로 추가한다.

```text
auction_items.onbid_category TEXT NOT NULL DEFAULT ''
auction_items.onbid_public_date TEXT NOT NULL DEFAULT ''
auction_items.onbid_date_source TEXT NOT NULL DEFAULT ''
auction_items.onbid_is_stale BOOLEAN NOT NULL DEFAULT 0
```

대체 이름을 쓰면 result bundle에 이유를 기록한다.

## 12.4 권장 인덱스

```text
idx_auction_items_source_onbid_category
idx_auction_items_source_onbid_public_date
idx_auction_items_source_category_public_date_price
idx_auction_items_source_onbid_is_stale
```

SQLite에서 이미 존재하면 재생성하지 않는다.

## 12.5 migration ledger

신규 컬럼/인덱스가 하나라도 추가되면 `docs/migration_ledger.md`에 v005 항목을 추가한다.

반드시 포함:

```text
- 변경 목적
- 신규 컬럼
- 신규 인덱스
- 비파괴 여부
- 기존 데이터 영향
- repair/backfill 방식
- rollback 방법
- 검증 명령
```

---

# 13. Core 9: category mapping 보강

## 13.1 공개 카테고리

```text
all
real_estate
movable
national_property
other
```

## 13.2 분류 우선순위

```text
1. source_api/api_kind가 national_property이면 무조건 national_property
2. 명시 onbid_category/category가 있으면 우선 사용
3. ONBID API kind hint 사용
4. asset_type/usage/raw_payload token 보조 판정
5. 불확실하면 other
```

## 13.3 national_property 규칙

```text
national_property는 독립 카테고리다.
국유일반재산 payload에 토지/건물/주거 token이 있어도 real_estate로 재분류하지 않는다.
국유일반재산 payload에 차량/기계 token이 있어도 movable로 재분류하지 않는다.
```

## 13.4 부동산 token 후보

```text
부동산
토지
건물
상가
주거
아파트
주택
오피스텔
대지
임야
전
답
공장
창고
근린생활시설
real estate
land
building
apartment
house
office
```

## 13.5 동산 token 후보

```text
동산
차량
자동차
승용
화물
운송
선박
기계
장비
비품
재고
movable
vehicle
car
ship
machine
equipment
```

## 13.6 테스트

```text
tests/onbid_category_mapping_test.py
```

필수 assertion:

```text
- 토지/건물/상가/주거 -> real_estate
- 차량/운송/기계/장비 -> movable
- national_property source_api + 토지 token -> national_property
- national_property source_api + 차량 token -> national_property
- unknown sparse payload -> other
- 저장형 onbid_category가 있으면 helper가 일관되게 사용
```

---

# 14. Core 10: /onbid 공개 필터 UX polish

## 14.1 목표

상용화 전 공개 탐색 화면의 기본 사용성을 끌어올린다.

## 14.2 필수 UI 요소

```text
- category tabs: 전체/부동산/동산/국유일반재산/기타
- category별 count
- 지역 preset
- 가격 preset
- 직접 가격 입력
- 현재 적용 필터 chip
- 필터 초기화 버튼
- active preset 표시
- 2025 이후 데이터 표시 안내
- no-result empty state 개선
- 모바일에서 필터가 깨지지 않게 구성
```

## 14.3 지역 preset

```text
전체
서울
경기
인천
부산
대구
대전
광주
울산
세종
강원
충북
충남
전북
전남
경북
경남
제주
```

## 14.4 가격 preset

```text
가격 전체
1억 이하
1억~3억
3억~5억
5억 이상
직접 입력
```

## 14.5 필터 chip 예

```text
지역: 서울
카테고리: 부동산
가격: 1억~3억
2025년 이후
```

각 chip은 가능하면 해당 필터 제거 링크를 제공한다.

## 14.6 query 유지 원칙

필터 링크를 만들 때 다른 기존 필터가 사라지지 않아야 한다.

예:

```text
category를 바꿔도 region/price는 유지
region을 바꿔도 category/price는 유지
price preset을 바꿔도 category/region은 유지
reset은 명확히 전체 초기화
```

## 14.7 테스트

```text
tests/onbid_public_filter_state_test.py
```

필수 assertion:

```text
- /onbid?region=서울&category=real_estate&price_max=100000000에서 chip 표시
- reset link가 /onbid로 연결
- category link가 기존 region/price를 유지
- price preset active 표시
- region preset active 표시
- category count가 표시됨
```

---

# 15. Core 11: 상세 페이지 polish

## 15.1 목표

`/onbid/{id}`가 “데이터 덩어리”가 아니라 검토 가능한 상세 페이지가 되도록 정리한다.

## 15.2 필수 요소

```text
- breadcrumb: 홈 > 온비드 > 카테고리 > 물건
- 상단 온비드 active
- 카테고리 badge
- 2025 이후/freshness badge
- 정보 부족 panel
- 핵심 요약 카드: 최저가, 감정가, 입찰마감, 소재지, 기관
- 외부 원문 링크, 단 내부 raw path 금지
- 같은 공고 다른 물건
- 내 관심/패스/감시/메모 panel
- 입찰 전 원문 확인 고정 안내
```

## 15.3 회생/파산 상세

`/cases/{id}`도 최소 breadcrumb와 active state를 정리한다.

금지 유지:

```text
비로그인 AI 분석 노출 금지
OCR full text 노출 금지
raw file path 노출 금지
/documents/raw link 노출 금지
```

---

# 16. Core 12: review mode 설계 및 구현

## 16.1 목표

외부 리뷰어 또는 ChatGPT가 공개 페이지를 검토할 수 있도록 안전한 review mode를 만든다. review mode는 운영 배포가 아니라 임시 검토 상태다.

## 16.2 설정 후보

`backend/config.py` 또는 기존 settings에 추가한다.

```text
REVIEW_MODE=false
REVIEW_PUBLIC_ONLY=true
REVIEW_DISABLE_ADMIN_MUTATIONS=true
REVIEW_DISABLE_REAL_SYNC=true
REVIEW_HIDE_RAW_LINKS=true
REVIEW_NO_INDEX=true
REVIEW_BANNER_ENABLED=true
REVIEW_ALLOWED_HOSTS=
REVIEW_READONLY_DB_RECOMMENDED=true
```

기본값은 모두 안전한 방향으로 둔다.

## 16.3 review mode 동작

REVIEW_MODE=true일 때:

```text
- 모든 public 페이지 상단에 review banner 표시
- robots/meta에 noindex, noarchive 권장
- admin mutation 버튼 비활성화
- real API sync 버튼 비활성화
- 실제 DB restore/apply/retention apply UI 비활성화
- raw/internal link 숨김
- API key configured 여부도 public에는 표시하지 않음
- admin route는 기본적으로 로그인+admin 유지
- review public URL로는 admin credential 공유 금지
```

## 16.4 review mode banner 문구

```text
리뷰 모드입니다. 이 URL은 임시 검토용이며, 입찰/투자 판단에 사용할 수 없습니다.
관리자 기능, 원문 raw, 실제 수집 실행은 비활성화되어 있습니다.
```

## 16.5 review DB 권장

실제 운영 DB를 그대로 tunnel에 노출하지 않는다.

가능하면 아래 helper를 만든다.

```text
prepare_review_database.ps1
```

기능 후보:

```text
- auction_data.db를 storage/review/auction_data_review.db로 복사
- 복사 전/후 SHA256 출력
- 원본 DB 수정 없음
- optional: 사용자 메모/세션/민감 row를 비우는 sanitize 옵션 검토
```

명령 후보:

```powershell
powershell -ExecutionPolicy Bypass -File .\prepare_review_database.ps1 -Source .\auction_data.db -Target .\storage\review\auction_data_review.db -DryRun
powershell -ExecutionPolicy Bypass -File .\prepare_review_database.ps1 -Source .\auction_data.db -Target .\storage\review\auction_data_review.db -Apply
```

Codex는 `-Apply`를 임의 실행하지 않는다. 가능하면 dry-run만 수행하고 result bundle에 사용자 실행 명령으로 기록한다.

## 16.6 review server 실행 스크립트

가능하면 아래 helper를 만든다.

```text
run_review_server.ps1
```

동작 후보:

```text
- REVIEW_MODE=true
- REVIEW_PUBLIC_ONLY=true
- REVIEW_DISABLE_REAL_SYNC=true
- REVIEW_DISABLE_ADMIN_MUTATIONS=true
- REVIEW_NO_INDEX=true
- DB_URL을 review DB로 지정 가능
- host는 기본 127.0.0.1
- port는 기본 8000
```

명령 후보:

```powershell
powershell -ExecutionPolicy Bypass -File .\run_review_server.ps1 -Port 8000
```

주의:

```text
- 기본 bind는 127.0.0.1
- tunnel 도구가 localhost를 외부로 연결한다
- uvicorn을 0.0.0.0으로 직접 열지 않는다
```

---

# 17. Core 13: Cloudflare/ngrok tunnel review runbook

## 17.1 목표

포트포워딩 대신 안전한 임시 tunnel 방식으로 외부 검토를 할 수 있게 한다.

## 17.2 원칙

```text
- Codex는 tunnel을 자동 실행하지 않는다.
- 사용자가 명시적으로 실행한다.
- review mode를 켠 상태에서만 tunnel을 공유한다.
- admin credential은 공유하지 않는다.
- 실제 운영 DB 대신 review DB 또는 sample DB를 사용한다.
- 테스트 후 tunnel을 종료한다.
```

## 17.3 Cloudflare quick tunnel 명령

Cloudflare Tunnel이 설치되어 있다면 사용자는 별도 공유기 포트포워딩 없이 localhost를 임시 URL로 노출할 수 있다.

권장 순서:

```powershell
cd C:\Users\xogns\Documents\testAuction\court_auction_platform

powershell -ExecutionPolicy Bypass -File .\run_review_server.ps1 -Port 8000

cloudflared tunnel --url http://127.0.0.1:8000
```

Cloudflare quick tunnel은 테스트/개발용으로만 사용한다. 운영 배포로 간주하지 않는다.

## 17.4 ngrok 명령

ngrok이 설치되어 있다면:

```powershell
cd C:\Users\xogns\Documents\testAuction\court_auction_platform

powershell -ExecutionPolicy Bypass -File .\run_review_server.ps1 -Port 8000

ngrok http 127.0.0.1:8000
```

가능하면 ngrok 인증/접근 제한 기능을 사용한다.

## 17.5 tunnel 공유 전 체크리스트

```text
[ ] REVIEW_MODE=true banner가 보인다.
[ ] /robots.txt 또는 meta가 noindex/noarchive 기준을 반영한다.
[ ] /documents/raw/{id}가 비로그인 차단된다.
[ ] /api/admin/onbid-quality가 비로그인 차단된다.
[ ] /admin/collection은 admin login 없이는 접근되지 않는다.
[ ] public /onbid에 2025 이전 데이터가 보이지 않는다.
[ ] public /onbid에 raw payload/internal path가 보이지 않는다.
[ ] API key 값이 화면/로그에 보이지 않는다.
[ ] admin mutation/real sync 버튼이 review mode에서 disabled 또는 hidden이다.
[ ] tunnel URL은 필요한 사람에게만 공유한다.
```

## 17.6 result bundle 기록

```text
- review mode 구현 여부
- review server command
- Cloudflare/ngrok command guide
- 실제 tunnel 실행 여부: Codex는 실행하지 않음
- public review URL: 사용자가 별도로 공유 시에만 기록, 기본은 기록하지 않음
- review safety checklist 결과
```

---

# 18. Core 14: public route visual smoke / screenshot review

## 18.1 목표

ChatGPT나 외부 리뷰어가 직접 localhost를 볼 수 없어도 화면 구조를 검토할 수 있게 캡처/HTML snapshot을 생성한다.

## 18.2 접근 방식

새 heavy dependency를 무리하게 추가하지 않는다.

우선순위:

```text
1. Playwright가 이미 설치되어 있으면 screenshot capture 사용
2. 설치되어 있지 않으면 TestClient HTML snapshot 생성
3. 둘 다 어려우면 route별 status/text marker smoke test 작성
```

## 18.3 스크립트 후보

```text
scripts/capture_ui_review.py
capture_ui_review.ps1
```

출력 위치:

```text
storage/review/screenshots/
storage/review/html/
storage/review/review_manifest.json
```

이 경로는 커밋하지 않는다.

## 18.4 캡처 대상

```text
/
 /onbid
/onbid?category=real_estate
/onbid?category=movable
/onbid?category=national_property
/onbid?region=서울&category=real_estate
/onbid?price_max=100000000&category=movable
/onbid/{sample_item_id}
/cases
/cases/{sample_event_id}
/privacy
/terms
/disclaimer
/admin/collection after admin login, 가능하면 screenshot 대신 HTML marker test
/admin/operations-readiness after admin login
/admin/onbid-runs after admin login
```

## 18.5 모바일 viewport

가능하면 다음 viewport를 모두 캡처한다.

```text
desktop: 1440x1000
tablet: 768x1024
mobile: 390x844
```

## 18.6 테스트

신규 테스트 후보:

```text
tests/public_route_visual_smoke_test.py
tests/template_render_smoke_test.py
```

필수 assertion:

```text
- 주요 public route가 200
- active marker 존재
- review mode banner가 REVIEW_MODE=true일 때 표시
- 주요 필터 chip/탭/초기화 UI가 렌더링
- raw/internal 문자열이 public HTML에 없음
```

---

# Extended Scope

---

# 19. Extended 1: 관리자 freshness/category/readiness dashboard

## 19.1 목표

관리자가 “현재 데이터가 믿을 만한가?”를 한 화면에서 볼 수 있게 한다.

## 19.2 대상 route

기존 `/admin/collection`을 강화하거나 신규 route를 추가한다.

권장 신규 route:

```text
/admin/operations-readiness
```

기존 화면도 유지한다.

## 19.3 지표

```text
Freshness:
- min_public_date
- fresh_public_count
- stale_before_min_date_count
- missing_relevant_date_count
- oldest_public_date
- newest_public_date
- stale ratio
- unknown date ratio

Category:
- real_estate_count
- movable_count
- national_property_count
- other_count
- category별 fresh/stale/unknown
- category별 missing price/location/schedule

API:
- last real_estate run
- last movable run
- last notice run
- last national_property run/probe
- last success
- last failure
- latest failure message summary
- duplicates/stale/unknown dropped counts

Operations:
- backup latest timestamp
- restore dry-run available
- scheduler tasks expected/missing
- log retention dry-run status
- API key configured 여부, 값은 노출 금지
- review mode status
- legal pages status
- robots/sitemap status
```

## 19.4 UI 문구

```text
공개 기준: 2025-01-01 이후 입찰/공고 데이터만 기본 표시합니다.
2025 이전 데이터는 삭제하지 않고 공개 목록에서 제외하며, 관리자 audit에서 확인합니다.
```

## 19.5 테스트

```text
tests/admin_readiness_dashboard_test.py
tests/admin_observability_test.py
```

필수 assertion:

```text
- 비로그인 /admin/operations-readiness 접근 불가
- admin 접근 200
- freshness metrics 존재
- category metrics 존재
- backup/scheduler/log readiness section 존재
- API key 값 자체는 HTML/JSON에 없음
```

---

# 20. Extended 2: 관리자 run history 화면

## 20.1 목표

수집/backup/restore/scheduler/log-retention 실행 결과를 운영자가 추적할 수 있게 한다.

## 20.2 구현 후보

기존 `CrawlRun` 또는 현재 run 기록 모델을 재사용한다. 신규 테이블은 가능하면 피한다.

신규 route 후보:

```text
/admin/onbid-runs
/api/admin/onbid-runs
```

## 20.3 표시 항목

```text
- run id
- run type
- api kind
- status
- started_at
- finished_at
- duration
- fetched
- inserted
- updated
- duplicates
- accepted_fresh
- dropped_stale_before_min_date
- dropped_missing_relevant_date
- error summary, key/raw payload 없음
- log file path는 내부 경로를 직접 public에 노출하지 말고 admin 내부에서도 필요 최소 표시
```

## 20.4 필터

```text
- api_kind
- status
- run_type
- days
```

## 20.5 failed sync alert 후보 설계

실제 알림은 보내지 않는다.

run history 화면 또는 result bundle에 설계만 기록한다.

```text
Trigger candidates:
- last run failed
- 24시간 이상 successful run 없음
- stale drop rate가 과도함
- unknown date rate가 과도함
- API auth error
- API total_count 갑작스러운 0

Future channels:
- email
- Slack/Discord webhook
- browser push
- admin dashboard banner

v005 implementation:
- admin dashboard warning only
- no outbound notification
```

---

# 21. Extended 3: Windows Scheduler 실제 등록 리허설 강화

## 21.1 목표

실제 Windows Task Scheduler 등록 전, 명령/권한/경로/로그/환경을 점검할 수 있게 한다.

## 21.2 원칙

Codex는 실제 등록을 자동 수행하지 않는다.

허용:

```text
- check_scheduled_tasks.ps1 강화
- register_scheduled_tasks.ps1 생성, 기본 DryRun
- 권장 등록 명령 출력
- task XML 또는 command preview 생성
```

금지:

```text
- Codex가 -Register/-Apply로 실제 task 등록
- 사용자 승인 없는 schtasks /Create 실행
```

## 21.3 권장 작업 종류

```text
CourtAuction-Onbid-RealEstate-Fresh
CourtAuction-Onbid-Notice-Fresh
CourtAuction-Onbid-NationalProperty-Fresh
CourtAuction-Case-Crawl
CourtAuction-Backup-Daily
CourtAuction-LogRetention-Weekly
```

## 21.4 권장 명령 후보

```powershell
powershell -ExecutionPolicy Bypass -File .\run_onbid_scheduled_sync.ps1 -RunType scheduled -ApiKind real_estate -Limit 20 -MaxPages 1 -MinDate 2025-01-01 -IncludeDetails

powershell -ExecutionPolicy Bypass -File .\run_onbid_scheduled_sync.ps1 -RunType scheduled -ApiKind notice -Limit 20 -MaxPages 1 -MinDate 2025-01-01 -IncludeNoticeDetails -IncludeNoticeItems

powershell -ExecutionPolicy Bypass -File .\run_onbid_probe.ps1 -ApiKind national_property -Limit 20 -MaxPages 1 -MinDate 2025-01-01
```

## 21.5 스크립트 후보

```text
check_scheduled_tasks.ps1
register_scheduled_tasks.ps1
```

`register_scheduled_tasks.ps1` 기본 동작:

```text
-DryRun 기본 true
-Apply 또는 -Register 없으면 실제 등록하지 않음
명령 preview 출력
작업명/트리거/working directory/log path 검증
```

## 21.6 테스트

```text
tests/scheduler_scripts_test.py
```

검증:

```text
- DryRun 출력이 등록 명령을 포함
- 실제 등록은 하지 않음
- MinDate 2025-01-01 포함
- Limit 20, MaxPages 1 포함
```

---

# 22. Extended 4: 운영 DB backup/restore 리허설 강화

## 22.1 목표

실제 운영 DB를 망가뜨리지 않고 backup/restore 절차를 리허설한다.

## 22.2 backup 개선

`backup_database.ps1`를 점검한다.

권장 출력:

```json
{
  "source": "...",
  "backup": "...",
  "sha256": "...",
  "bytes": 12345,
  "created_at": "...",
  "status": "BACKUP_CREATED"
}
```

## 22.3 restore dry-run 개선

기존 `restore_database.ps1`를 강화한다.

요구:

```text
- BackupPath 필수
- DryRun 기본
- ConfirmRestore 없으면 실제 restore 금지
- target DB hash 출력
- backup hash 출력
- restore 전 target backup 추천
```

## 22.4 temp restore rehearsal

운영 DB에 덮어쓰지 않고 임시 DB로 복원 테스트를 수행한다.

스크립트 후보:

```text
test_restore_rehearsal.ps1
```

명령 후보:

```powershell
powershell -ExecutionPolicy Bypass -File .\test_restore_rehearsal.ps1 -BackupPath storage\backups\auction_data_YYYYMMDD_HHMMSS.db
```

동작:

```text
- storage/test/restore_rehearsal_*.db로 복사
- SQLite 연결 확인
- 주요 테이블 존재 확인
- row count 요약
- 테스트 DB 삭제 여부는 옵션으로
```

실제 운영 DB restore는 하지 않는다.

## 22.5 result bundle 기록

```text
- latest backup path
- restore dry-run result
- temp restore rehearsal result
- rollback runbook
```

---

# 23. Extended 5: log retention 강화

## 23.1 목표

로그와 백업 보관 정책을 dry-run 중심으로 정리한다.

## 23.2 정책 후보

```text
storage/logs/onbid/: 30일
루트 *.log: 14~30일
storage/backups/: 30일 또는 최근 N개
storage/review/: review 종료 후 수동 삭제
storage/raw/: 삭제 금지
storage/processed/: 삭제 금지
```

## 23.3 run_log_retention.ps1 개선

요구:

```text
- 기본 DryRun
- Apply 없으면 삭제 없음
- raw/processed 삭제 금지
- 삭제 후보 JSON 출력
- LogsOnly 옵션 유지
- BackupsOnly 옵션 후보
- KeepLatestBackups 후보
```

## 23.4 테스트

```text
tests/log_retention_scripts_test.py
```

검증:

```text
- DryRun은 삭제하지 않음
- raw/processed 대상 제외
- Apply 없이 삭제 없음
```

---

# 24. Extended 6: privacy/terms/disclaimer 정식화

## 24.1 목표

베타 공개에 가까운 문구로 정리하되, 법률 검토 완료처럼 단정하지 않는다.

## 24.2 route

```text
/privacy
/terms
/disclaimer
/about
```

`/privacy-draft`는 `/privacy`로 redirect 유지 가능.

## 24.3 포함할 내용

개인정보:

```text
- 수집 항목: 계정 정보, 표시명, 세션, 관심/패스/감시/메모, 접속/운영 로그
- 수집하지 않는 항목: 결제 정보, 알림 수신 정보, 광고 개인화 정보
- 이용 목적: 개인화 목록, 보안, 운영, 장애 대응
- 보관 기간: 베타 운영 정책 기준, 추후 정식화
- 제3자 제공 없음
- 외부 원문 링크 이동 시 외부 사이트 정책 적용
- 문의처 placeholder
```

약관:

```text
- 서비스 성격: 공공데이터 탐색/개인 검토 보조 도구
- 원문 확인 책임
- 데이터 지연/오류 가능성
- AI 분석은 법률/투자/입찰 자문 아님
- 금지 행위
- 서비스 변경/중단 가능성
- 베타 운영 고지
```

고지:

```text
- 입찰/투자 판단 전 원문 확인
- 회생/파산 AI 분석은 로그인 사용자 참고자료
- ONBID AI 자동 분석 미제공
- 낙찰결과/알림/결제/광고 실제 연동 미제공
```

## 24.4 UI

공통 public nav와 footer에 연결한다.

```text
개인정보
이용약관
고지
문의 준비 중
```

## 24.5 테스트

```text
tests/legal_pages_test.py
```

검증:

```text
- /privacy, /terms, /disclaimer 200
- /privacy-draft redirect
- 핵심 문구 포함
- raw/internal path 없음
```

---

# 25. Extended 7: sitemap/robots fresh public item만 포함

## 25.1 목표

sitemap이 오래된 2003년 ONBID item을 포함하지 않게 한다.

## 25.2 robots

유지/강화:

```text
Disallow: /admin
Disallow: /api/admin
Disallow: /user
Disallow: /my
Disallow: /documents/raw
Disallow: /storage
```

review mode일 때:

```text
User-agent: *
Disallow: /
```

또는 public page meta noindex를 강화한다. 운영 모드와 review mode의 동작을 result bundle에 명확히 기록한다.

## 25.3 sitemap

포함:

```text
/
/onbid
/cases
/about
/disclaimer
/privacy
/terms
fresh /onbid/{id} limited
safe public /cases/{id} limited
```

제외:

```text
admin
api/admin
user
my
documents/raw
storage
stale onbid item
unknown-date onbid item
raw/internal
```

## 25.4 제한

```text
동적 /onbid/{id}는 최대 100개 또는 설정값
fresh_public only
item_name 있고 public_date >= 2025-01-01
```

## 25.5 테스트

```text
tests/sitemap_fresh_public_routes_test.py
```

검증:

```text
- stale /onbid/{id} 미포함
- fresh /onbid/{id} 포함
- protected path 미포함
- review mode에서 noindex/disallow 동작
```

---

# 26. Extended 8: rate limit / CSRF / session 보안 점검

## 26.1 목표

상용화 전 기본 보안 리스크를 점검하고 가능한 범위에서 구현한다.

## 26.2 rate limit

외부 Redis 없이 local app에서 가능한 가벼운 in-memory rate limit를 구현하거나, 최소한 설계와 테스트를 남긴다.

대상 후보:

```text
POST /login
POST /onbid/{id}/preference
POST /api/onbid/{id}/preference
POST /api/admin/auctions/onbid/sync
admin mutation routes
```

기본 정책 후보:

```text
login: IP+username 기준 5회/분
preference: user 기준 60회/분
admin sync: admin user 기준 5회/10분
```

주의:

```text
in-memory limiter는 단일 프로세스 local/beta용이다.
운영 분산 환경에서는 Redis 등 외부 저장소가 필요하지만 v005에서는 구현하지 않는다.
```

## 26.3 CSRF

폼 POST에 CSRF token을 도입할 수 있으면 도입한다.

대상:

```text
로그인
로그아웃
온비드 preference
메모 저장
admin mutation
```

설계:

```text
session cookie 기반 CSRF token
hidden input csrf_token
POST에서 검증
API JSON route는 header X-CSRF-Token 또는 same-origin 검토
```

어려우면 result bundle에 보류 사유와 위험을 기록한다.

## 26.4 session cookie

점검 항목:

```text
HttpOnly
SameSite=Lax 또는 Strict
Secure flag는 HTTPS/review tunnel 상황 고려
세션 secret 고정/출력 금지
로그아웃 시 cookie 정리
```

설정 후보:

```text
SESSION_COOKIE_SECURE=false local default
SESSION_COOKIE_SAMESITE=lax
SESSION_COOKIE_HTTPONLY=true
```

## 26.5 security headers

가능하면 middleware를 추가한다.

```text
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
```

CSP는 Tailwind CDN을 사용 중이면 조심스럽게 설계만 하거나 보류한다.

## 26.6 테스트

```text
tests/security_headers_test.py
tests/csrf_rate_limit_test.py
```

검증:

```text
- public route에 보안 header 존재
- 민감 POST에 CSRF 요구 또는 명확한 대안
- login rate limit smoke
- session cookie attributes 확인
```

---

# 27. Extended 9: Lighthouse / 접근성 / 모바일 QA

## 27.1 목표

완전한 프론트엔드 QA 도구 체인은 아니더라도, 상용화 전 눈에 띄는 UX/accessibility 문제를 잡는다.

## 27.2 자동화 가능 범위

가능하면 다음 중 가능한 것을 수행한다.

```text
- Playwright screenshot
- HTML landmark/heading/label 검사
- aria-current active 검사
- form label/placeholder 검사
- mobile viewport render smoke
```

Lighthouse CLI 또는 Chrome이 없으면 설치하지 않는다. 대신 result bundle에 “실행 불가 사유”와 수동 체크리스트를 기록한다.

## 27.3 수동 체크리스트

```text
Desktop:
- nav active
- filters usable
- category count
- stale 안내
- detail breadcrumb
- no-result state

Mobile:
- header wrapping
- filters scroll/collapse
- table overflow
- CTA touch target
- breadcrumb wrapping

Accessibility:
- 페이지당 h1 하나
- form label 또는 aria-label
- active nav aria-current
- link text meaningful
- color만으로 상태 구분하지 않음
- keyboard focus 확인
```

## 27.4 result bundle 기록

```text
- 자동 screenshot/HTML snapshot 경로
- 수동 확인 대상 URL
- 통과/미확인/보류 항목
- v006로 넘길 polish
```

---

# 28. Extended 10: staging/preview tunnel 정식화

## 28.1 목표

v006에서 진짜 staging을 가기 전에, v005에서 preview tunnel 운영 규칙을 문서화하고 script 수준으로 준비한다.

## 28.2 preview 방식 비교

result bundle에 다음 비교를 포함한다.

```text
1. local screenshots only
2. Cloudflare quick tunnel
3. ngrok
4. GitHub Codespaces forwarded port
5. 공유기 포트포워딩
```

권장 순서:

```text
1순위: screenshot/HTML snapshot
2순위: review mode + Cloudflare quick tunnel
3순위: review mode + ngrok
4순위: Codespaces preview with sample DB
5순위: 포트포워딩, 가능하면 피함
```

## 28.3 포트포워딩 관련 결론

문서에 명확히 기록한다.

```text
공유기 포트포워딩은 현재 단계에서 권장하지 않는다.
이유:
- 개발 서버 직접 노출
- 방화벽/공인 IP 노출
- HTTPS/reverse proxy/rate limit/session hardening 미흡
- admin/raw boundary 실수 시 위험
```

---

# 29. Stretch Scope

Core와 Extended가 안정적으로 끝나면 아래도 가능한 범위에서 진행한다.

## 29.1 AGENTS.md 보강

추가 후보:

```text
- v005 이후 ONBID public cutoff 2025-01-01
- stale row 삭제 금지
- review mode/tunnel 안전 규칙
- active nav test requirement
- real API Limit=20 MaxPages=1 유지
- external integration 금지
- scheduler/register Apply 금지
```

## 29.2 local review runbook section

새 markdown을 만들기보다 result bundle에 통합한다. 단, script help는 가능하다.

## 29.3 UI text cleanup

깨진 UTF-8 또는 어색한 문구가 public-facing template에 있으면 정리한다.

제외:

```text
과거 reports 대량 수정
대량 포맷팅
무관한 관리자 문구 전체 리라이트
```

## 29.4 performance smoke

가능하면 isolated DB에 synthetic data를 생성해 category/freshness query 성능을 점검한다.

```text
5,000~20,000 synthetic AuctionItem
category/freshness/price/region query
same-notice lookup
admin metrics
```

운영 DB는 오염시키지 않는다.

---

# 30. 필수 테스트 명령

Codex runtime Python을 우선 사용한다.

```powershell
$Py = "C:\Users\xogns\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
```

## 30.1 compile

```powershell
& $Py -m py_compile main_app.py backend/database/models.py backend/database/session.py backend/web/routers/auctions.py backend/web/routers/cases.py backend/web/routers/admin_operations.py backend/services/auction_items.py backend/services/onbid_observability.py backend/onbid/client.py backend/workers/onbid_sync.py
```

신규 backend/service/script-facing Python 파일이 있으면 추가한다.

## 30.2 v005 신규 테스트

실제 파일명은 구현에 맞춰 조정하되 result bundle에 정확히 기록한다.

```powershell
& $Py tests/navigation_active_state_test.py
& $Py tests/onbid_freshness_policy_test.py
& $Py tests/onbid_category_mapping_test.py
& $Py tests/onbid_public_filter_state_test.py
& $Py tests/admin_readiness_dashboard_test.py
& $Py tests/public_route_visual_smoke_test.py
& $Py tests/sitemap_fresh_public_routes_test.py
& $Py tests/security_headers_test.py
& $Py tests/legal_pages_test.py
```

선택/가능 시:

```powershell
& $Py tests/csrf_rate_limit_test.py
& $Py tests/scheduler_scripts_test.py
& $Py tests/log_retention_scripts_test.py
& $Py tests/template_render_smoke_test.py
```

## 30.3 기존 핵심 테스트

```powershell
& $Py tests/onbid_category_filter_test.py
& $Py tests/sitemap_public_routes_test.py
& $Py tests/onbid_module_test.py
& $Py tests/page_response_smoke_test.py
& $Py tests/router_boundary_test.py
& $Py tests/isolated_operations_test.py
& $Py tests/public_access_auth_boundary_test.py
```

## 30.4 sample/dry-run scripts

```powershell
powershell -ExecutionPolicy Bypass -File .\run_onbid_scheduled_sync.ps1 -Sample -ApiKind notice -Limit 20 -MaxPages 1 -IncludeNoticeDetails -IncludeNoticeItems

powershell -ExecutionPolicy Bypass -File .\audit_onbid_freshness.ps1 -MinDate 2025-01-01

powershell -ExecutionPolicy Bypass -File .\repair_onbid_derived_fields.ps1 -DryRun -MinDate 2025-01-01

powershell -ExecutionPolicy Bypass -File .\check_scheduled_tasks.ps1

powershell -ExecutionPolicy Bypass -File .\run_log_retention.ps1 -DryRun
```

## 30.5 real API fresh probe

실제 API는 key가 configured일 때만 실행한다. key 값은 출력하지 않는다.

```powershell
powershell -ExecutionPolicy Bypass -File .\run_onbid_fresh_probe.ps1 -ApiKind real_estate -Limit 20 -MaxPages 1 -MinDate 2025-01-01

powershell -ExecutionPolicy Bypass -File .\run_onbid_fresh_probe.ps1 -ApiKind movable -Limit 20 -MaxPages 1 -MinDate 2025-01-01

powershell -ExecutionPolicy Bypass -File .\run_onbid_fresh_probe.ps1 -ApiKind notice -Limit 20 -MaxPages 1 -MinDate 2025-01-01

powershell -ExecutionPolicy Bypass -File .\run_onbid_fresh_probe.ps1 -ApiKind national_property -Limit 20 -MaxPages 1 -MinDate 2025-01-01
```

실제 저장형 sync를 수행해야 한다면 DB 백업 후 제한 조건을 지킨다.

```powershell
powershell -ExecutionPolicy Bypass -File .\backup_database.ps1

powershell -ExecutionPolicy Bypass -File .\run_onbid_scheduled_sync.ps1 -RunType manual -ApiKind real_estate -Limit 20 -MaxPages 1 -MinDate 2025-01-01 -IncludeDetails
```

Codex는 real 저장형 sync를 실행하기 전 반드시 backup이 성공했는지 확인한다.

---

# 31. 민감 파일 검사

작업 종료 전 반드시 실행한다.

```powershell
git status --short

$trackedSensitive = git ls-files | Select-String -Pattern '(^|[\\/])\.env($|[\\/])|(^|[\\/])storage[\\/]|(^|[\\/])logs[\\/]|(^|[\\/])runtime_settings\.json$|\.(db|sqlite|sqlite3)$|(^|[\\/])\.git\.bad-init'
if ($trackedSensitive) {
    $trackedSensitive
    throw "민감 파일이 tracked 상태입니다. 확인 필요."
} else {
    "OK: no tracked sensitive runtime files"
}

git diff --cached --name-only | Select-String -Pattern '(^|/|\\)(\.env|storage|logs)(/|\\|$)|\.(db|sqlite|sqlite3)$|runtime_settings\.json|\.git\.bad-init'
```

마지막 명령 출력이 있으면 커밋하지 않는다.

---

# 32. 결과 bundle 요구사항

최종 결과 파일:

```text
reports/devpacks/devpack_v005_result_bundle.md
```

반드시 다음 목차를 포함한다.

```markdown
# Codex Development Result Bundle v005

## 1. Work Metadata
- Git root:
- Branch:
- Base commit:
- Final commit(s): not committed, not pushed
- Remote:
- Work start status:
- Work end status:

## 2. High-Level Result

## 3. Route / Template / Navigation Inventory

## 4. Navigation/Menu Active State Result

## 5. Fresh ONBID Data Policy Result

## 6. ONBID Fresh API Probe Result
| API kind | Limit | MaxPages | MinDate | Fetched | Accepted fresh | Dropped stale | Dropped unknown date | Inserted/Updated/Duplicate | Notes |

## 7. Existing DB Stale Audit Result

## 8. Category Mapping and Stored Field Result

## 9. Public ONBID UX Polish Result
- Category tabs/counts:
- Filter chips/reset:
- Region preset active:
- Price preset active:
- Empty state:
- Detail breadcrumb:

## 10. Review Mode and Tunnel Readiness
- Review mode settings:
- Disabled mutations:
- Review server command:
- Cloudflare/ngrok commands:
- Safety checklist:

## 11. Visual/HTML Review Artifacts
- Screenshots:
- HTML snapshots:
- Manifest:
- Not generated reason, if any:

## 12. Admin Readiness / Run History Result

## 13. Scheduler Rehearsal Result

## 14. Backup/Restore Rehearsal Result

## 15. Log Retention Result

## 16. Legal Pages Result

## 17. Sitemap/Robots Fresh Public Result

## 18. Security Hardening Result
- Rate limit:
- CSRF:
- Session cookie:
- Security headers:
- Deferred risks:

## 19. Lighthouse / Accessibility / Mobile QA Result

## 20. DB/Migration Changes
- New tables:
- New columns:
- New indexes:
- Non-destructive:
- Migration ledger updated:
- Rollback:

## 21. Changed Files
| File | Summary | Risk | Notes |

## 22. Public/Login/Admin Boundaries
| Area | Anonymous | Login | Admin | Notes |

## 23. Test Results
| Command | Result | Notes |

## 24. Manual Local Review Guide

## 25. Incomplete / Deferred / Risks

## 26. v006 Recommended Work
Focus on external integrations only after v005 review:
- notification/email design implementation
- production staging/deployment hardening
- real AdSense if desired
- auction results if desired
- formal legal review
- larger backfill strategy

## 27. Codex CLI Operations Memo
- Goal used:
- Approval prompts:
- API key printed?: no
- Real API commands:
- Tunnel actually run?: no, unless user explicitly did outside Codex
```

---

# 33. project-result_current.md 갱신 요구사항

`reports/project-result_current.md`를 v005 기준으로 업데이트한다.

반드시 포함:

```text
- v005 완료 기능
- 2025 freshness policy
- stale data handling
- category/navigation 상태
- review mode/tunnel 준비 상태
- admin readiness/run history 상태
- scheduler/backup/restore/log retention 리허설 상태
- 보안 점검 상태
- 테스트 결과
- 아직 상용화 전 남은 리스크
- v006 이후 외부 연동 준비 방향
```

---

# 34. migration ledger 갱신 요구사항

다음 중 하나라도 있으면 `docs/migration_ledger.md`에 v005 항목을 추가한다.

```text
- 신규 컬럼
- 신규 인덱스
- 신규 테이블
- ensure_schema_migrations 변경
- stored category/freshness 필드 추가
- run history 저장 구조 변경
```

v005 ledger에는 반드시 아래를 쓴다.

```text
- change date
- purpose
- schema changes
- data handling
- stale row policy
- migration method
- rollback method
- verification
```

---

# 35. AGENTS.md 보강 후보

필요하면 아래 규칙을 추가한다.

```text
v005 이후 ONBID 공개 데이터 freshness:
- public /onbid는 기본적으로 2025-01-01 이후 데이터만 표시한다.
- 2025 이전 row는 삭제하지 않고 stale/audit 처리한다.
- 신규 real sync는 2025 이전 payload를 accepted_fresh로 처리하지 않는다.

Navigation:
- nav/menu active state는 route context와 tests로 검증한다.
- 결과가 0건이어도 query category tab active는 유지한다.

Review mode:
- review mode에서는 admin mutation, real sync, raw link를 비활성화한다.
- tunnel은 사용자가 명시적으로 실행한다.
- API key/raw payload/internal path를 공개하지 않는다.

External integrations:
- email/push/Slack/AdSense/payment/auction-result integrations are separate future devpacks.
```

---

# 36. 완료 기준

v005는 아래 조건을 만족하면 완료로 본다.

```text
1. /onbid 기본 공개 목록에서 2025-01-01 이전 item이 보이지 않는다.
2. 날짜 확인 불가 item은 public 기본 목록에서 숨겨진다.
3. 2003년 fixture가 stale로 판정된다.
4. 신규 real API fresh probe가 Limit=20, MaxPages=1, MinDate=2025-01-01로 실행 또는 실패 사유 기록된다.
5. 기존 DB stale audit 결과가 result bundle에 기록된다.
6. 기존 DB row는 삭제하지 않는다.
7. 부동산/동산/국유일반재산/기타 category mapping이 테스트된다.
8. national_property는 독립 카테고리로 유지된다.
9. /onbid category tab active state가 결과 0건이어도 정확하다.
10. 홈/온비드/회생파산/내온비드/관리자 nav active state가 주요 route에서 정확하다.
11. 공통 nav/header partial이 도입되거나 도입 불가 사유가 기록된다.
12. filter chip/reset/region preset/price preset active가 구현된다.
13. 상세 breadcrumb가 구현된다.
14. category count가 표시된다.
15. review mode가 구현되고 안전 checklist가 통과한다.
16. Cloudflare/ngrok tunnel runbook이 result bundle에 포함된다.
17. Codex는 tunnel을 자동 실행하지 않는다.
18. visual smoke 또는 HTML snapshot review artifact가 생성되거나 불가 사유가 기록된다.
19. admin readiness/run history 화면 또는 섹션이 구현된다.
20. failed sync alert는 후보 설계만 남기고 실제 발송은 구현하지 않는다.
21. scheduler registration rehearsal은 dry-run/preview 중심으로 구현된다.
22. backup/restore rehearsal이 운영 DB를 덮지 않는 방식으로 검증된다.
23. log retention은 dry-run 기본이며 raw/processed 삭제 대상이 아니다.
24. privacy/terms/disclaimer가 베타 공개 전 수준으로 정리된다.
25. sitemap은 fresh public item만 포함한다.
26. rate limit/CSRF/session/security headers가 구현 또는 보류 사유와 함께 점검된다.
27. Lighthouse/accessibility/mobile QA가 실행 또는 체크리스트로 기록된다.
28. public/auth/admin/raw boundary 테스트가 계속 통과한다.
29. API key, DB, storage, logs, raw payload가 Git에 커밋되지 않는다.
30. devpack_v005_result_bundle.md, project-result_current.md, migration_ledger.md가 갱신된다.
31. commit/push는 하지 않는다.
```

---

# 37. Codex CLI 실행용 /goal 문구

Codex CLI에서 아래 goal을 사용한다.

```text
/goal Implement reports/devpacks/devpack_v005_instruction.md on branch codex/devpack-v005-product-qa-fresh-data-navigation. Complete Core Scope first, then Extended Scope, then Stretch Scope as far as safely possible. This v005 pack must repair product QA, navigation/menu active states, ONBID 2025-01-01 freshness policy, stale data audit/hide, category mapping/counts, public filter polish, admin readiness/run history, scheduler and backup/restore rehearsals, legal pages, fresh sitemap, review mode, and Cloudflare/ngrok tunnel readiness. Do not implement external integrations such as email, push notifications, Slack/Discord webhooks, real AdSense, payment, or auction results. Enforce that pre-2025 and unknown-date ONBID items do not appear in public /onbid by default. Do not delete existing DB rows; audit or hide stale rows instead. Keep national_property independent. Use real ONBID API calls only with Limit=20 MaxPages=1 MinDate=2025-01-01 when configured, without printing secrets. Build route/template/navigation inventory and add tests for active states, freshness, category mapping, public filters, review mode, security boundaries, sitemap, and admin readiness. Prepare review mode and tunnel runbook but do not run or expose a public tunnel automatically. Produce one consolidated result bundle at reports/devpacks/devpack_v005_result_bundle.md and update reports/project-result_current.md and docs/migration_ledger.md as needed. Do not commit or push.
```

---

# 38. Codex가 /goal 후 바로 작업하지 않을 때 넣을 메시지

```markdown
현재 repo는 `C:\Users\xogns\Documents\testAuction\court_auction_platform`입니다.
현재 작업 브랜치는 `codex/devpack-v005-product-qa-fresh-data-navigation`입니다.

먼저 아래를 실행해 Git 상태를 확인하고 결과를 최종 bundle에 기록하세요.

```powershell
git rev-parse --show-toplevel
git branch --show-current
git status --short
git remote -v
git --no-pager log --oneline --decorate -8
git merge-base --is-ancestor 913aece HEAD
if ($LASTEXITCODE -eq 0) {
    "OK: v004 final commit is included"
} else {
    "ERROR: v004 final commit is NOT included"
}
```

그 다음 `AGENTS.md`와 `reports/devpacks/devpack_v005_instruction.md`를 읽고 v005를 진행하세요.

핵심은 다음입니다.

- ONBID 공개 데이터는 기본적으로 `2025-01-01` 이후만 표시하세요.
- 2025 이전 payload와 날짜 확인 불가 payload는 public 기본 목록에 나오면 안 됩니다.
- 기존 DB의 2025 이전 row는 삭제하지 말고 audit/hide/repair 대상으로 처리하세요.
- `/onbid?category=real_estate`, `/onbid?category=movable`, `/onbid?category=national_property`, `/onbid?category=other`의 tab active 상태를 고치고 테스트하세요.
- 결과가 0건이어도 선택한 category tab은 active여야 합니다.
- 홈/온비드/회생파산/내온비드/관리자 메뉴 active도 전체적으로 검토하고 테스트하세요.
- `national_property`는 독립 카테고리로 유지하고 부동산/동산으로 재분류하지 마세요.
- filter chip, reset, region preset active, price preset active, category count, detail breadcrumb를 구현하세요.
- review mode를 구현하고 Cloudflare/ngrok tunnel runbook을 작성하세요.
- Codex가 tunnel을 자동 실행하거나 외부 공개하지는 마세요.
- 실제 API 호출은 `Limit=20`, `MaxPages=1`, `MinDate=2025-01-01`만 사용하고 API key 값은 절대 출력/로그/문서화하지 마세요.
- 알림, 이메일, web push, Slack/Discord webhook, 실제 AdSense, 결제, 낙찰결과, 대량 백필, destructive migration은 하지 마세요.
- scheduler/register/restore/apply/tunnel 같은 위험 작업은 dry-run 또는 runbook 중심으로 처리하세요.
- commit/push는 하지 마세요.

최종 결과는 `reports/devpacks/devpack_v005_result_bundle.md` 하나에 통합하고,
`reports/project-result_current.md`, `docs/migration_ledger.md`도 필요한 만큼 갱신하세요.
```

---

# 39. Codex 승인창 기준

## 39.1 승인 가능

다음 조건이면 보통 `y` 승인 가능하다.

```text
- tests 실행
- py_compile
- run_onbid_fresh_probe.ps1
- audit_onbid_freshness.ps1
- repair_onbid_derived_fields.ps1 -DryRun
- check_scheduled_tasks.ps1
- run_log_retention.ps1 -DryRun
- restore_database.ps1 -DryRun
- test_restore_rehearsal.ps1
- Limit=20
- MaxPages=1
- MinDate=2025-01-01
- API key 값 출력 없음
```

## 39.2 신중 승인

다음은 반드시 내용을 확인한다.

```text
- backup_database.ps1
- prepare_review_database.ps1 -Apply
- repair_onbid_derived_fields.ps1 -Apply
- register_scheduled_tasks.ps1 -Apply 또는 -Register
- restore_database.ps1 -ConfirmRestore
- run_log_retention.ps1 -Apply
- cloudflared tunnel ...
- ngrok http ...
```

Codex가 자동으로 실행하려 하면 거절한다. 사용자가 명시적으로 실행할 때만 진행한다.

## 39.3 거절

다음은 거절한다.

```text
git reset --hard
git clean -fd
git clean -fdx
git push
git commit
Limit > 20
MaxPages > 1
DB row 삭제
storage/raw 삭제
storage/processed 삭제
API key 출력
.env 출력
email/webhook/push/AdSense/payment/auction result external integration
production deployment
```

---

# 40. 사용자 실행 요약

v005 지시서 저장과 브랜치 준비:

```powershell
cd C:\Users\xogns\Documents\testAuction\court_auction_platform

git checkout codex/devpack-v004-real-onbid-operations
git pull --ff-only

git checkout -b codex/devpack-v005-product-qa-fresh-data-navigation

notepad reports\devpacks\devpack_v005_instruction.md

git add reports/devpacks/devpack_v005_instruction.md
git commit -m "docs: add v005 devpack instructions"
git push -u origin codex/devpack-v005-product-qa-fresh-data-navigation
```

Codex CLI 시작:

```powershell
cd C:\Users\xogns\Documents\testAuction\court_auction_platform

codex -C "C:\Users\xogns\Documents\testAuction\court_auction_platform" --ask-for-approval on-request
```

Codex 내부:

```text
/clear
```

그 다음:

```text
/goal Implement reports/devpacks/devpack_v005_instruction.md on branch codex/devpack-v005-product-qa-fresh-data-navigation. Complete Core Scope first, then Extended Scope, then Stretch Scope as far as safely possible. This v005 pack must repair product QA, navigation/menu active states, ONBID 2025-01-01 freshness policy, stale data audit/hide, category mapping/counts, public filter polish, admin readiness/run history, scheduler and backup/restore rehearsals, legal pages, fresh sitemap, review mode, and Cloudflare/ngrok tunnel readiness. Do not implement external integrations such as email, push notifications, Slack/Discord webhooks, real AdSense, payment, or auction results. Enforce that pre-2025 and unknown-date ONBID items do not appear in public /onbid by default. Do not delete existing DB rows; audit or hide stale rows instead. Keep national_property independent. Use real ONBID API calls only with Limit=20 MaxPages=1 MinDate=2025-01-01 when configured, without printing secrets. Build route/template/navigation inventory and add tests for active states, freshness, category mapping, public filters, review mode, security boundaries, sitemap, and admin readiness. Prepare review mode and tunnel runbook but do not run or expose a public tunnel automatically. Produce one consolidated result bundle at reports/devpacks/devpack_v005_result_bundle.md and update reports/project-result_current.md and docs/migration_ledger.md as needed. Do not commit or push.
```

리뷰 모드 수동 실행 예시는 Codex 결과 후 사용자가 실행한다.

```powershell
powershell -ExecutionPolicy Bypass -File .\run_review_server.ps1 -Port 8000
```

Cloudflare tunnel:

```powershell
cloudflared tunnel --url http://127.0.0.1:8000
```

ngrok tunnel:

```powershell
ngrok http 127.0.0.1:8000
```

tunnel URL 공유 전에는 반드시 review safety checklist를 확인한다.

---

# 41. v006 이후 방향

v005가 끝난 뒤 v006은 “외부 연동 준비/구현 전 단계”로 잡는다.

v006 후보:

```text
- 외부 알림/email/webhook 구현 전 설계 확정
- 알림 동의/수신거부/개인정보 처리 구조
- production-grade staging
- formal legal review
- 배포 인프라
- rate limit 외부 저장소
- scheduler 실제 운영 등록
- 더 큰 ONBID 백필 전략
- monitoring/alert implementation, 단 v005에서는 구현하지 않음
```

v005의 목표는 v006에서 외부 연동을 시작해도 되는지 판단할 수 있을 만큼 제품과 데이터, 메뉴, 보안, 운영 리허설을 정리하는 것이다.
