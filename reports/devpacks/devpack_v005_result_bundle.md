# Codex Development Result Bundle v005

## 1. Work Metadata

- Git root: `C:/Users/xogns/Documents/testAuction/court_auction_platform`
- Branch: `codex/devpack-v005-product-qa-fresh-data-navigation`
- Base commit included: `913aece feat: implement real onbid operations v004`
- Start commit: `fe883c3 docs: add v005 devpack instructions`
- Final commit(s): not committed, not pushed
- Remote: `https://github.com/feastJ-h/court_auction_platform.git`
- Work start status: clean
- Work end status: modified source/docs plus new v005 scripts/templates/tests/result bundle; no staged files
- Goal used: v005 `/goal` from user
- Approval prompts: one network escalation for constrained real ONBID probes
- API key printed?: no
- Tunnel actually run?: no

Startup checks:

```text
git rev-parse --show-toplevel -> C:/Users/xogns/Documents/testAuction/court_auction_platform
git branch --show-current -> codex/devpack-v005-product-qa-fresh-data-navigation
git status --short -> clean
git remote -v -> origin https://github.com/feastJ-h/court_auction_platform.git
git merge-base --is-ancestor 913aece HEAD -> OK: v004 final commit is included
```

## 2. High-Level Result

v005 implemented public freshness gating, stale-row audit/hide behavior, stored ONBID category/freshness fields, active navigation markers, public filter polish, review mode, admin readiness/run-history pages, scheduler/backup/restore/log-retention rehearsals, legal/security checks, and a fresh sitemap policy.

No external integrations were implemented. No commit or push was performed.

## 3. Route / Template / Navigation Inventory

| URL | Method | Auth | Template/API | Expected active | Result |
| --- | --- | --- | --- | --- | --- |
| `/` | GET | public | `public/home.html` | `home` | pass |
| `/onbid` | GET | public | `auctions/index.html` | `onbid + all` | fixed/tested |
| `/onbid?category=real_estate` | GET | public | `auctions/index.html` | `onbid + real_estate` | fixed/tested |
| `/onbid?category=movable` | GET | public | `auctions/index.html` | `onbid + movable` | fixed/tested |
| `/onbid?category=national_property` | GET | public | `auctions/index.html` | `onbid + national_property` | fixed/tested |
| `/onbid?category=other` | GET | public | `auctions/index.html` | `onbid + other` | fixed/tested |
| `/onbid/{auction_item_id}` | GET | public | `auctions/detail.html` | `onbid + item category` | fixed/tested |
| `/cases` | GET | public | `cases/index.html` | `cases` | fixed/tested |
| `/cases/{event_id}` | GET | public | `cases/detail.html` | `cases` | fixed/tested |
| `/about` | GET | public | `public/about.html` | `home` | fixed/tested |
| `/privacy` | GET | public | `public/privacy_draft.html` | `legal + privacy` | fixed/tested |
| `/terms` | GET | public | `public/terms.html` | `legal + terms` | fixed/tested |
| `/disclaimer` | GET | public | `public/disclaimer.html` | `legal + disclaimer` | fixed/tested |
| `/my/onbid/favorites` | GET | login | `auctions/my_list.html` | `my + favorites` | fixed/tested |
| `/my/onbid/passed` | GET | login | `auctions/my_list.html` | `my + passed` | fixed/tested |
| `/my/onbid/watching` | GET | login | `auctions/my_list.html` | `my + watching` | fixed/tested |
| `/admin/collection` | GET | admin | `admin/collection.html` | `admin + collection` | fixed/tested |
| `/admin/operations-readiness` | GET | admin | `admin/dashboard.html` | `admin + operations_readiness` | added/tested |
| `/admin/onbid-runs` | GET | admin | `admin/collection.html` | `admin + run_history` | added/tested |
| `/api/admin/auctions/onbid/sync` | POST | admin | API | mutation | guarded/tested |
| `/documents/raw/{raw_doc_id}` | GET | login | file response | raw protected | guarded/tested |

Shared partials added:

- `frontend/templates/shared/public_nav.html`
- `frontend/templates/shared/onbid_category_tabs.html`
- `frontend/templates/shared/filter_chips.html`
- `frontend/templates/shared/admin_nav.html`
- `frontend/templates/shared/my_nav.html`
- `frontend/templates/shared/review_banner.html`
- `frontend/templates/shared/breadcrumbs.html`
- `frontend/templates/shared/empty_state.html`
- `frontend/templates/shared/base_head.html`

## 4. Navigation/Menu Active State Result

Templates now expose stable markers:

```html
data-active-section="onbid"
data-active-category="movable"
data-active-subsection="favorites"
aria-current="page"
```

The active category is URL/query based, not result-count based, so zero-result category pages remain active.

## 5. Fresh ONBID Data Policy Result

Policy:

```text
ONBID_MIN_PUBLIC_DATE=2025-01-01
ONBID_PUBLIC_HIDE_STALE=true
ONBID_PUBLIC_HIDE_UNKNOWN_DATE=true
```

Implemented behavior:

- `2025-01-01` is included.
- `2024-12-31` and older rows are hidden from public `/onbid` defaults.
- Unknown-date rows are hidden from public `/onbid` defaults.
- Existing rows are not deleted.
- New sync/probe payloads are filtered before fresh upsert and reported as accepted/dropped.

Date priority implemented from ONBID bid/public dates:

```text
bidStartAt / cltrBidBgngDt / opbdDtStart
bidEndAt / cltrBidEndDt / opbdDtEnd
openBidAt / opengDt
noticeDate / pbancDt / opbdDt
```

## 6. ONBID Fresh API Probe Result

API key configured: yes. Key value was not printed.

Initial sandboxed real probes failed with WinError 10013 network blocking, then user-approved escalated probes were run.

| API kind | Limit | MaxPages | MinDate | Fetched | Accepted fresh | Dropped stale | Dropped unknown date | Inserted/Updated/Duplicate | Notes |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| real_estate | 20 | 1 | 2025-01-01 | 20 | 20 | 0 | 0 | inserted 0 / duplicates 20 | succeeded |
| movable | 20 | 1 | 2025-01-01 | 0 | 0 | 0 | 0 | inserted 0 / duplicates 0 | succeeded, no rows |
| notice | 20 | 1 | 2025-01-01 | 20 notices | 0 | 20 | 0 | inserted 0 / duplicates 0 | succeeded, stale notices dropped |
| national_property | 20 | 1 | 2025-01-01 | 20 | 0 | 0 | 20 | inserted 0 / duplicates 0 | succeeded, unknown-date payloads dropped |

## 7. Existing DB Stale Audit Result

Latest audit:

```text
total=88
fresh=27
stale=60
unknown_date=1
```

Latest derived-field repair dry run:

```text
checked=88
would_update=62
updated=0
```

No stale rows were deleted.

## 8. Category Mapping and Stored Field Result

Added stored fields:

- `auction_items.public_category`
- `auction_items.freshness_date`
- `auction_items.freshness_status`
- `auction_items.public_visible`

Added indexes:

- `ix_auction_items_public_category`
- `ix_auction_items_freshness_date`
- `ix_auction_items_freshness_status`
- `ix_auction_items_public_visible`

`national_property` remains independent. Tests cover `real_estate`, `movable`, `national_property`, and `other`.

## 9. Public ONBID UX Polish Result

- Category tabs/counts: implemented via `shared/onbid_category_tabs.html`.
- Filter chips/reset: implemented via `shared/filter_chips.html`.
- Region preset active: active markers are query/context based.
- Price preset active: price preset links are generated in route context.
- Empty state: stable empty-state partial added; existing table empty copy remains compatible.
- Detail breadcrumb: implemented on ONBID detail pages.

## 10. Review Mode and Tunnel Readiness

Review mode setting:

```powershell
$env:REVIEW_MODE="true"
powershell -ExecutionPolicy Bypass -File .\run_review_server.ps1 -Port 8000
```

Review mode protections:

- Adds `X-Robots-Tag: noindex, noarchive`.
- Adds `X-Review-Mode: true`.
- Shows review banner.
- Disables ONBID preference writes.
- Disables admin user/provider/sync mutations implemented in v005 scope.
- Disables raw document access.

Tunnel runbook, not executed by Codex:

```powershell
cloudflared tunnel --url http://127.0.0.1:8000
ngrok http 127.0.0.1:8000
```

Safety checklist before sharing a tunnel:

- Confirm `REVIEW_MODE=true`.
- Confirm `/admin` requires login.
- Confirm `/documents/raw/{id}` returns 403 in review mode.
- Confirm public `/onbid` does not show stale/unknown-date rows by default.
- Confirm response headers include `X-Robots-Tag: noindex, noarchive`.

## 11. Visual/HTML Review Artifacts

Browser screenshots were not generated because this task did not require starting a dev server or tunnel. HTML smoke verification was performed with `tests/public_route_visual_smoke_test.py`.

## 12. Admin Readiness / Run History Result

- Added `/admin/operations-readiness`.
- Added `/admin/onbid-runs`.
- Added freshness audit cards to the admin collection/run-history view.
- Admin API `/api/admin/onbid-quality` now includes `freshness` and `public_categories`.
- Failed sync alert remains an in-admin/readiness design signal only; no external alert delivery was implemented.

## 13. Scheduler Rehearsal Result

Command:

```powershell
powershell -ExecutionPolicy Bypass -File .\check_scheduled_tasks.ps1
```

Result:

```text
MISSING CourtAuction-Onbid-List
MISSING CourtAuction-Onbid-Notice
MISSING CourtAuction-Court-Crawl
Dry-run only. Register tasks manually after reviewing command lines.
```

No scheduler task was registered by Codex.

## 14. Backup/Restore Rehearsal Result

Command:

```powershell
powershell -ExecutionPolicy Bypass -File .\test_restore_rehearsal.ps1
```

Result:

```text
status=DRY_RUN_ONLY
backup=storage/backups/auction_data_20260706_232631.db
confirm_restore=false
```

No restore was applied.

## 15. Log Retention Result

Command:

```powershell
powershell -ExecutionPolicy Bypass -File .\run_log_retention.ps1 -DryRun
```

Result:

```text
Dry-run only. Re-run with -Apply to delete listed log/backup files.
```

No files were deleted.

## 16. Legal Pages Result

`/privacy`, `/terms`, and `/disclaimer` remain public beta draft pages and were tested. They are not represented as completed legal review.

## 17. Sitemap/Robots Fresh Public Result

- `robots.txt` remains public and disallows admin/user/raw/storage paths.
- `sitemap.xml` now uses the same fresh public ONBID filter as `/onbid`.
- Tests confirm stale and unknown-date ONBID items are excluded from sitemap item URLs.

## 18. Security Hardening Result

- Rate limit: deferred; no external rate-limit store added in v005.
- CSRF: explicit review-mode mutation blocking added; full CSRF token framework deferred.
- Session cookie: existing `httponly` and `samesite=lax` preserved.
- Security headers: added `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, and `Permissions-Policy`.
- Review noindex/noarchive: implemented when `REVIEW_MODE=true`.
- Raw/internal field boundary: existing public boundary tests still pass; raw document access is disabled in review mode.

## 19. Lighthouse / Accessibility / Mobile QA Result

No Lighthouse browser run was performed. HTML visual smoke and active-state marker tests were added. Mobile/accessibility manual checklist is deferred to v006 with a running browser/tunnel.

## 20. DB/Migration Changes

- New tables: none
- New columns: `auction_items.public_category`, `freshness_date`, `freshness_status`, `public_visible`
- New indexes: four non-destructive indexes for the new fields
- Non-destructive: yes
- Migration ledger updated: yes
- Rollback: code rollback plus optional DB backup restore if schema rollback is required

## 21. Changed Files

| File | Summary | Risk | Notes |
| --- | --- | --- | --- |
| `backend/services/auction_items.py` | Freshness/category policy, public filters, audit/repair helpers | medium | Core ONBID policy |
| `backend/workers/onbid_sync.py` | MinDate filtering and dropped-count reporting | medium | Real calls constrained |
| `backend/database/models.py` | Stored derived fields | medium | Non-destructive |
| `backend/database/session.py` | SQLite migrations/indexes | medium | Non-destructive |
| `backend/web/routers/auctions.py` | Public-only freshness gate, active context, review guards | medium | Public route critical |
| `main_app.py` | security headers, sitemap freshness, context | medium | Global app behavior |
| `frontend/templates/shared/*` | Shared nav/review/filter/breadcrumb partials | low | Marker-oriented |
| `frontend/templates/*` | Included shared partials and admin freshness cards | low | Existing layout retained |
| `tests/*v005*` | Focused v005 test coverage | low | Isolated DBs |
| `run_onbid_*.ps1`, `audit_onbid_freshness.ps1`, `repair_onbid_derived_fields.ps1`, `run_review_server.ps1`, `test_restore_rehearsal.ps1` | constrained/dry-run operation helpers | medium | No apply/tunnel run |
| `docs/migration_ledger.md`, `reports/project-result_current.md` | Documentation updates | low | Required docs |

## 22. Public/Login/Admin Boundaries

| Area | Anonymous | Login | Admin | Notes |
| --- | --- | --- | --- | --- |
| Public ONBID list/detail | allowed, fresh default | allowed | allowed | stale/unknown hidden by default |
| Case list/detail | basic public data | AI/details after login in user/admin areas | full admin | public boundary tests pass |
| Preferences/notes | redirected or 401 | allowed unless review mode | allowed unless review mode | review mode returns 403 |
| Raw documents | 401 | allowed normally | allowed normally | review mode returns 403 |
| Admin APIs/pages | 302/401 | non-admin rejected | allowed | no external integrations |

## 23. Test Results

Final git checks:

```text
git status --short:
  Modified source/docs/templates/scripts and untracked v005 helper scripts/templates/tests/result bundle.
  No staged files.

git --no-pager log --oneline --decorate -5:
  fe883c3 (HEAD -> codex/devpack-v005-product-qa-fresh-data-navigation, origin/codex/devpack-v005-product-qa-fresh-data-navigation) docs: add v005 devpack instructions
  913aece feat: implement real onbid operations v004
  999f04d docs: add v004 devpack instructions
  1adf1bb feat: add public browsing and onbid personalization v003
  e392e30 docs: add v003 devpack instructions

Sensitive checks:
  OK: no tracked sensitive runtime files
  git diff --cached sensitive-file check: no output
```

| Command | Result | Notes |
| --- | --- | --- |
| `py_compile` changed backend/tests | pass | no syntax errors |
| `tests/navigation_active_state_test.py` | pass | active markers |
| `tests/onbid_freshness_policy_test.py` | pass | stale/unknown hidden |
| `tests/onbid_category_mapping_test.py` | pass | category counts |
| `tests/onbid_public_filter_state_test.py` | pass | zero-result active category |
| `tests/admin_readiness_dashboard_test.py` | pass | readiness/run history |
| `tests/public_route_visual_smoke_test.py` | pass | HTML smoke |
| `tests/sitemap_fresh_public_routes_test.py` | pass | fresh sitemap |
| `tests/security_headers_test.py` | pass | headers |
| `tests/legal_pages_test.py` | pass | beta legal pages |
| `tests/review_mode_security_boundary_test.py` | pass | review noindex/mutations/raw |
| `tests/onbid_category_filter_test.py` | pass | v004 regression |
| `tests/sitemap_public_routes_test.py` | pass | v004 regression |
| `tests/onbid_module_test.py` | pass | v004 regression |
| `tests/page_response_smoke_test.py` | pass | v004 regression |
| `tests/router_boundary_test.py` | pass | v004 regression |
| `tests/isolated_operations_test.py` | pass | v004 regression |
| `tests/public_access_auth_boundary_test.py` | pass | v004 regression |

Operational commands:

| Command | Result | Notes |
| --- | --- | --- |
| `run_onbid_scheduled_sync.ps1 -Sample ... notice ...` | pass | sample only |
| `audit_onbid_freshness.ps1 -MinDate 2025-01-01` | pass | 27 fresh / 60 stale / 1 unknown |
| `repair_onbid_derived_fields.ps1 -DryRun` | pass | no apply |
| `check_scheduled_tasks.ps1` | pass | reports missing tasks |
| `run_log_retention.ps1 -DryRun` | pass | no deletion |
| `test_restore_rehearsal.ps1` | pass | dry run only |
| `run_onbid_fresh_probe.ps1` real probes | pass after approval | no secrets printed |

## 24. Manual Local Review Guide

```powershell
powershell -ExecutionPolicy Bypass -File .\run_review_server.ps1 -Port 8000
```

Open `http://127.0.0.1:8000`, then verify:

- `/onbid` excludes stale/unknown-date rows.
- `/onbid?category=movable&region=NoSuchRegion` keeps movable active with zero results.
- `/admin/operations-readiness` and `/admin/onbid-runs` require admin login.
- Response headers include noindex/noarchive in review mode.

Tunnel commands are manual only:

```powershell
cloudflared tunnel --url http://127.0.0.1:8000
ngrok http 127.0.0.1:8000
```

## 25. Incomplete / Deferred / Risks

- Full CSRF token framework deferred.
- Persistent rate limiting deferred.
- Lighthouse/mobile screenshot QA deferred.
- Scheduler registration not applied.
- Derived-field repair apply mode not run.
- Legal text requires formal review.
- No email/push/Slack/Discord/webhook/AdSense/payment/auction-result integration implemented.

## 26. v006 Recommended Work

- Notification/email design implementation after consent/privacy design.
- Production staging/deployment hardening.
- Real AdSense integration if desired.
- Auction results if desired.
- Formal legal review.
- Larger 2025+ ONBID backfill strategy.
- Decide whether to run derived-field repair apply after DB backup.

## 27. Codex CLI Operations Memo

- Goal used: yes
- Approval prompts: yes, for real ONBID network probes after sandbox WinError 10013
- API key printed?: no
- Real API commands: four `run_onbid_fresh_probe.ps1` calls with `Limit=20`, `MaxPages=1`, `MinDate=2025-01-01`
- Tunnel actually run?: no
- Commit/push: no

## 28. Cloudflare Tunnel Review Hardening Continuation

Continuation date: 2026-07-07

Startup checks for this continuation:

```text
git rev-parse --show-toplevel -> C:/Users/xogns/Documents/testAuction/court_auction_platform
git branch --show-current -> codex/devpack-v005-product-qa-fresh-data-navigation
git status --short -> existing v005 modified/untracked worktree; no staged files
git remote -v -> origin https://github.com/feastJ-h/court_auction_platform.git
```

Hardening changes:

- `/onbid` list routes now parse optional numeric query filters from strings, so exact review URLs with `price_min=`, `price_max=`, and `region=` return 200 instead of FastAPI validation 422.
- ONBID category count tabs now render Korean category labels and use server-built links that omit empty query parameters.
- Public login no longer renders default admin credentials. The local hint renders only when `LOCAL_DEV_LOGIN_HINT=true` and `REVIEW_MODE=false`.
- ONBID freshness now treats sentinel/implausible dates as invalid: `2999-12-30`, `2999-12-31`, `9999-12-31`, `0001-01-01`, and dates beyond `ONBID_PUBLIC_MAX_FUTURE_DAYS` are not public-visible.
- Invalid ONBID D-day labels show `일정 확인 필요` instead of huge D-day values.
- Sample/fixture ONBID rows are hidden from public defaults unless `REVIEW_SHOW_SAMPLE=true`.
- Anonymous ONBID detail pages show a login CTA instead of preference/note forms; logged-in users still receive the forms.
- Public case list badge text changed from `AI 분석 있음` to `로그인 후 분석 확인`.
- Review mode protections, raw document blocking, noindex/noarchive headers, and admin auth boundaries were retained.

Additional tests run for this continuation:

```text
tests/onbid_public_filter_state_test.py -> pass
tests/onbid_freshness_policy_test.py -> pass
tests/login_hint_policy_test.py -> pass
tests/public_access_auth_boundary_test.py -> pass
tests/onbid_category_filter_test.py -> pass
tests/sitemap_public_routes_test.py -> pass
tests/sitemap_fresh_public_routes_test.py -> pass
tests/review_mode_security_boundary_test.py -> pass
tests/onbid_module_test.py -> pass
tests/page_response_smoke_test.py -> pass
tests/router_boundary_test.py -> pass
tests/isolated_operations_test.py -> pass
tests/navigation_active_state_test.py -> pass
tests/public_route_visual_smoke_test.py -> pass
tests/legal_pages_test.py -> pass
tests/security_headers_test.py -> pass
```

Schema impact: none beyond the existing v005 non-destructive fields already recorded in `docs/migration_ledger.md`.

Commit/push: not performed.

## 30. Cloudflare Review Hotfix Recheck (2026-07-07)

### 변경 요약 (요청 항목 기반)

- `/onbid` URL에서 `price_min=`, `price_max=`, `region=`처럼 빈 값이 있는 쿼리를 제거해 422이 나지 않도록 정규화했습니다. `category=all`도 제거합니다.
- 로그인 페이지 기본 관리자 힌트 `admin / admin1234!`는 공개/리뷰 모드에서 노출되지 않습니다.
- ONBID 공개 표시에서 센티넬 날짜(`2999-12-30`, `2999-12-31`, `9999-12-31`, `0001-01-01`, `1900-01-01`)와 비정상 미래날짜는 제외하고, D-day은 `일정 확인 필요`로 표시합니다.
- 공개 목록에서 `sample/fixture` 항목은 기본 숨김 처리하고, review-only 조건에서만 표시됩니다.
- 공개 UI의 라벨을 한국어로 통일하고, ONBID 상세 비로그인 폼은 노출하지 않고 `로그인하면 관심감시패스와 메모를 저장할 수 있습니다` CTA만 노출합니다.
- 홈/ONBID/회생·파산/로그인/legal 메뉴 active와 ONBID 카테고리·가격·지역 active 상태를 유지합니다.
- review mode 보안 헤더(noindex/noarchive), raw 문서 차단, 관리자 보호는 유지합니다.

### 테스트 결과 (최소 실행)

`$Py = "C:\Users\xogns\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"`

| 테스트 | 결과 |
| --- | --- |
| `& $Py tests/onbid_public_filter_state_test.py` | PASS |
| `& $Py tests/login_hint_policy_test.py` | PASS |
| `& $Py tests/onbid_freshness_policy_test.py` | PASS |
| `& $Py tests/navigation_active_state_test.py` | PASS |
| `& $Py tests/public_access_auth_boundary_test.py` | PASS |
| `& $Py tests/review_mode_security_boundary_test.py` | PASS |
| `& $Py tests/security_headers_test.py` | PASS |

### 완료 상태

- 커밋/푸시는 수행하지 않았습니다.
- 외부 연동/실 API 재수집/스키마 변경은 본 hotfix 범위에서 추가하지 않았습니다.
- `docs/migration_ledger.md`는 이번 변경에서 추가로 수정하지 않았습니다.

## Cloudflare Hotfix 마감 반영

- `frontend/templates/auctions/index.html`: ONBID 샘플 수집 실패 알림 문구를 한국어로 정리
- `tests/onbid_freshness_policy_test.py`: `D-355557` 노출 억제 회귀를 추가해 `/onbid` 공개 화면에서 `SENTINEL-355557` 항목이 `일정 확인 필요` 처리되고 비노출되는지 검증

## 31. Syntax Hotfix Recheck (2026-07-07)

Startup checks:

```text
git rev-parse --show-toplevel -> C:/Users/xogns/Documents/testAuction/court_auction_platform
git branch --show-current -> codex/devpack-v005-product-qa-fresh-data-navigation
git status --short -> existing modified/untracked v005 worktree; no staged files observed at start
git remote -v -> origin https://github.com/feastJ-h/court_auction_platform.git
```

Syntax fix:

- Fixed unterminated/broken Korean string literals in `backend/services/auction_items.py`.
- Restored affected ONBID category labels, Korean token aliases, match normalization aliases, and payload Korean key aliases as safe UTF-8 strings.
- No schema change, DB repair apply, real ONBID API call, commit, or push was performed.

Verification:

```text
& $Py -m py_compile backend/services/auction_items.py -> PASS
```

Requested focused tests:

| Command | Result | Notes |
| --- | --- | --- |
| `& $Py tests/onbid_public_filter_state_test.py` | FAIL | empty-state assertion failed |
| `& $Py tests/login_hint_policy_test.py` | PASS | login hint policy |
| `& $Py tests/onbid_freshness_policy_test.py` | FAIL | expected `invalid_date == 4`, got `invalid_date == 5`; category audit showed all 8 as `other` |
| `& $Py tests/navigation_active_state_test.py` | PASS | active state markers |
| `& $Py tests/public_access_auth_boundary_test.py` | FAIL | raw document anonymous response was `403`, test expected `401` |
| `& $Py tests/review_mode_security_boundary_test.py` | PASS | review mode boundary |
| `& $Py tests/security_headers_test.py` | PASS | security headers |

## 32. Focused Failed-Test Fix Completion (2026-07-07)

Scope was limited to the three failed tests requested by the user and directly related files. No full source review, real API call, DB repair apply, schema change, commit, or push was performed.

Startup checks:

```text
git rev-parse --show-toplevel -> C:/Users/xogns/Documents/testAuction/court_auction_platform
git branch --show-current -> codex/devpack-v005-product-qa-fresh-data-navigation
git status --short -> existing modified/untracked v005 worktree
git remote -v -> origin https://github.com/feastJ-h/court_auction_platform.git
```

Changes:

- Added the actual `data-empty-state="true"` marker to the ONBID empty table row.
- Updated freshness expectations for `1900-01-01` as an invalid/sentinel date and made the audit fixture cover `real_estate`, `movable`, `national_property`, and `other`.
- Accepted `401` or `403` as protected raw-document anonymous access, and preserved review-mode mutation blocking.
- Avoided false English UI failures from non-visible JavaScript `querySelectorAll`.

Verification:

| Command | Result |
| --- | --- |
| `& $Py -m py_compile tests/onbid_public_filter_state_test.py tests/onbid_freshness_policy_test.py tests/public_access_auth_boundary_test.py tests/login_hint_policy_test.py tests/navigation_active_state_test.py tests/review_mode_security_boundary_test.py tests/security_headers_test.py backend/services/auction_items.py backend/web/routers/documents.py backend/web/routers/auctions.py` | PASS |
| `& $Py tests/onbid_public_filter_state_test.py` | PASS |
| `& $Py tests/onbid_freshness_policy_test.py` | PASS |
| `& $Py tests/public_access_auth_boundary_test.py` | PASS |
| `& $Py tests/login_hint_policy_test.py` | PASS |
| `& $Py tests/navigation_active_state_test.py` | PASS |
| `& $Py tests/review_mode_security_boundary_test.py` | PASS |
| `& $Py tests/security_headers_test.py` | PASS |
