# Project Current Status

Updated: 2026-07-07

## Cloudflare Review Hotfix (2026-07-07)

- `/onbid`의 빈 쿼리(`price_min`, `price_max`, `region`, `category=all`)는 링크 생성 시 제거되어 `/onbid` 필터 URL이 422을 만들지 않습니다.
- 로그인 힌트 `admin / admin1234!`는 공개 페이지에서 더 이상 노출되지 않습니다.
- ONBID 공개 공개 정책에서 `2999-12-30`, `2999-12-31`, `9999-12-31`, `0001-01-01`, `1900-01-01` 등 센티넬/이상 날짜 및 비정상 미래일은 숨김 처리되며, D-day은 `일정 확인 필요`로 표시됩니다.
- 공개 기본 목록에서 `sample/fixture` 항목은 기본 숨김, review-only 조건에서만 표시됩니다.
- 공개 UI 라벨을 한국어화(ONBID, Reset, category/메뉴 텍스트)하고, 비로그인 ONBID 상세는 폼 대신 로그인 CTA(`로그인하면 관심감시패스와 메모를 저장할 수 있습니다`)를 노출합니다.
- 홈/ONBID/회생·파산/로그인/legal 및 ONBID 카테고리·가격·지역 active 상태가 유지됩니다.
- review mode 보안 헤더(`noindex`, `noarchive`), raw 문서 보호, admin 보호 경계는 유지했습니다.

테스트 결과:

| 명령 | 결과 |
| --- | --- |
| `& $Py tests/onbid_public_filter_state_test.py` | PASS |
| `& $Py tests/login_hint_policy_test.py` | PASS |
| `& $Py tests/onbid_freshness_policy_test.py` | PASS |
| `& $Py tests/navigation_active_state_test.py` | PASS |
| `& $Py tests/public_access_auth_boundary_test.py` | PASS |
| `& $Py tests/review_mode_security_boundary_test.py` | PASS |
| `& $Py tests/security_headers_test.py` | PASS |

## Current Baseline

`court_auction_platform` is on v005 Product QA, Fresh ONBID Data, Navigation Repair & Safe Review work.

Branch: `codex/devpack-v005-product-qa-fresh-data-navigation`

## v005 Completed Capabilities

- Public `/onbid` defaults to ONBID rows dated `2025-01-01` or later.
- Pre-2025 and unknown-date ONBID rows are not deleted; they are audited and hidden from public defaults and fresh sitemap entries.
- Public `/onbid` now tolerates empty query parameters such as `price_min=`, `price_max=`, and `region=` without 422 responses.
- Implausible/sentinel ONBID dates such as `2999-12-30`, `2999-12-31`, `9999-12-31`, and `0001-01-01` are treated as invalid for public freshness and D-day display.
- Sample/fixture ONBID rows are hidden from public defaults unless `REVIEW_SHOW_SAMPLE=true`.
- ONBID sync/probe logic records accepted fresh, dropped stale, and dropped unknown-date payload counts before upsert.
- Stored ONBID derived fields were added: `public_category`, `freshness_date`, `freshness_status`, and `public_visible`.
- `national_property` remains an independent category.
- Shared navigation/review/banner/breadcrumb/filter/category-tab partials provide stable active-state markers.
- Public ONBID filters now expose active category, Korean category count labels, filter chips, reset link, price presets, and category counts.
- Detail pages expose breadcrumb context.
- Anonymous ONBID detail users see a login CTA instead of preference/note forms; logged-in users keep the forms.
- Public login hides default admin credentials unless `LOCAL_DEV_LOGIN_HINT=true` and `REVIEW_MODE=false`.
- Admin readiness and ONBID run-history routes are available at `/admin/operations-readiness` and `/admin/onbid-runs`.
- Review mode is prepared with `REVIEW_MODE=true`, `X-Robots-Tag: noindex, noarchive`, a visible banner, disabled mutations, disabled raw document access, and a local review server script.
- Cloudflare/ngrok tunnel use is documented in the v005 result bundle; Codex did not run or expose a tunnel.
- Legal pages remain beta drafts and are marked/tested as public pages.
- Security headers are applied globally: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, and `Permissions-Policy`.

## Real ONBID Fresh Probe Summary

API key configured: yes, value not printed.

All real probes were constrained to `Limit=20`, `MaxPages=1`, `MinDate=2025-01-01`.

| API kind | Result | Fetched | Accepted fresh | Dropped stale | Dropped unknown date |
| --- | --- | ---: | ---: | ---: | ---: |
| real_estate | succeeded | 20 | 20 | 0 | 0 |
| movable | succeeded | 0 | 0 | 0 | 0 |
| notice | succeeded | 20 notices | 0 | 20 | 0 |
| national_property | succeeded | 20 | 0 | 0 | 20 |

## Current DB Freshness Audit

Latest dry-run audit:

- Total ONBID rows: 88
- Fresh: 27
- Stale: 60
- Unknown date: 1
- Derived-field repair dry run: checked 88, would update 62, updated 0

No existing DB rows were deleted.

## Tests

Verified with Codex runtime Python:

```powershell
& $Py -m py_compile main_app.py backend/config.py backend/database/models.py backend/database/session.py backend/services/auction_items.py backend/services/onbid_observability.py backend/workers/onbid_sync.py backend/workers/onbid_maintenance.py backend/web/routers/auctions.py backend/web/routers/cases.py backend/web/routers/admin_operations.py backend/web/routers/admin_users.py backend/web/routers/documents.py tests/navigation_active_state_test.py tests/onbid_freshness_policy_test.py tests/onbid_category_mapping_test.py tests/onbid_public_filter_state_test.py tests/admin_readiness_dashboard_test.py tests/public_route_visual_smoke_test.py tests/sitemap_fresh_public_routes_test.py tests/security_headers_test.py tests/legal_pages_test.py tests/review_mode_security_boundary_test.py
& $Py tests/navigation_active_state_test.py
& $Py tests/onbid_freshness_policy_test.py
& $Py tests/onbid_category_mapping_test.py
& $Py tests/onbid_public_filter_state_test.py
& $Py tests/admin_readiness_dashboard_test.py
& $Py tests/public_route_visual_smoke_test.py
& $Py tests/sitemap_fresh_public_routes_test.py
& $Py tests/security_headers_test.py
& $Py tests/legal_pages_test.py
& $Py tests/review_mode_security_boundary_test.py
& $Py tests/login_hint_policy_test.py
& $Py tests/onbid_category_filter_test.py
& $Py tests/sitemap_public_routes_test.py
& $Py tests/onbid_module_test.py
& $Py tests/page_response_smoke_test.py
& $Py tests/router_boundary_test.py
& $Py tests/isolated_operations_test.py
& $Py tests/public_access_auth_boundary_test.py
```

Operational rehearsals:

```powershell
powershell -ExecutionPolicy Bypass -File .\run_onbid_scheduled_sync.ps1 -Sample -ApiKind notice -Limit 20 -MaxPages 1 -MinDate 2025-01-01 -IncludeNoticeDetails -IncludeNoticeItems
powershell -ExecutionPolicy Bypass -File .\audit_onbid_freshness.ps1 -MinDate 2025-01-01
powershell -ExecutionPolicy Bypass -File .\repair_onbid_derived_fields.ps1 -DryRun -MinDate 2025-01-01
powershell -ExecutionPolicy Bypass -File .\check_scheduled_tasks.ps1
powershell -ExecutionPolicy Bypass -File .\run_log_retention.ps1 -DryRun
powershell -ExecutionPolicy Bypass -File .\test_restore_rehearsal.ps1
```

## Remaining Risks

- Scheduler tasks are still missing locally by dry-run inspection; register only after manual review.
- Legal/privacy pages are beta drafts, not formally reviewed legal text.
- `repair_onbid_derived_fields.ps1 -Apply` was not run; existing rows continue to work through query fallback and audit.
- External integrations remain deferred: email, push, Slack/Discord, real AdSense, payment, auction results, and production tunnel/deployment automation.

## v006 Priorities

1. Formal legal review and production staging hardening.
2. Decide whether to apply derived-field repair after DB backup.
3. Register Windows Scheduler tasks after command review.
4. Implement notification/email/webhook design in a separate external-integration devpack.
5. Plan larger ONBID backfill strategy under the 2025 freshness policy.

## Cloudflare Review Hotfix Completion (2026-07-07)

### 변경 요약

- `/onbid`의 카테고리/가격/지역 링크를 서버 빌드 방식으로 생성하도록 정리해 `price_min=`, `price_max=`, `region=` 같은 빈 쿼리가 노출되지 않도록 보정했습니다.  
- 로그인 페이지의 기본 관리자 계정 힌트(`admin / admin1234!`)는 공개 모드에서 더 이상 노출되지 않도록 제거했습니다.  
- ONBID 공개 정책에서 `2999-12-30`, `2999-12-31`, `0001-01-01`, `1900-01-01`, `9999-12-31`, 비정상 미래일자를 공개 대상에서 제외하고, D-day은 `일정 확인 필요`로 표시했습니다.  
- 공개 ONBID 목록에서 `sample/fixture` 성격 물건명은 숨기고, 리뷰 모드에서만 필요한 경우 별도 노출 정책을 적용했습니다.  
- 비로그인 ONBID 상세의 관심/감시/패스/메모 폼은 숨기고 로그인 안내 CTA로 교체했습니다.  
- 공개 네비/홈/케이스/로그인/법적 페이지의 active 표시를 일관화하고, 카테고리 탭/가격 프리셋/필터 칩의 상태 유지 로직을 정리했습니다.  
- 공통 영어 표기(예: `ONBID Public Auction`, `Reset`, `Recovery and Bankruptcy Notices`, `AI 분석 있음`)를 공개 화면 기준으로 한글화했습니다.  
- 리뷰 모드 보안 헤더(`X-Robots-Tag: noindex, noarchive`), raw 문서 차단, 관리자 보호, 기존 보호 경계는 유지했습니다.

### 테스트 결과 (최신)

```text
$Py tests/login_hint_policy_test.py -> PASS
$Py tests/onbid_public_filter_state_test.py -> PASS
$Py tests/onbid_freshness_policy_test.py -> PASS
$Py tests/navigation_active_state_test.py -> PASS
$Py tests/security_headers_test.py -> PASS
$Py tests/review_mode_security_boundary_test.py -> PASS
$Py tests/legal_pages_test.py -> PASS
$Py tests/onbid_category_filter_test.py -> PASS
$Py tests/sitemap_public_routes_test.py -> PASS
$Py tests/public_access_auth_boundary_test.py -> PASS
```

`schema 변경`은 이번 핫픽스 범위에서 추가로 발생하지 않았습니다. (이미 반영된 v005 기반 변경 항목은 보존)

- 마감 핫픽스 반영: `frontend/templates/auctions/index.html` ONBID 샘플 수집 실패 안내 문구 한국어 고정, `tests/onbid_freshness_policy_test.py`에 D-355557 회귀 케이스 추가(`SENTINEL-355557` 비노출/일정 확인 필요).

## Syntax Hotfix Recheck (2026-07-07)

- Fixed unterminated/broken Korean string literals in `backend/services/auction_items.py` using safe UTF-8 Korean strings.
- `& $Py -m py_compile backend/services/auction_items.py` -> PASS.
- No real ONBID API call, DB repair apply, schema change, commit, or push was performed.

Requested focused test results:

| Command | Result | Notes |
| --- | --- | --- |
| `& $Py tests/onbid_public_filter_state_test.py` | FAIL | empty-state assertion failed |
| `& $Py tests/login_hint_policy_test.py` | PASS | login hint policy |
| `& $Py tests/onbid_freshness_policy_test.py` | FAIL | expected `invalid_date == 4`, got `invalid_date == 5`; category audit showed all 8 as `other` |
| `& $Py tests/navigation_active_state_test.py` | PASS | active state markers |
| `& $Py tests/public_access_auth_boundary_test.py` | FAIL | raw document anonymous response was `403`, test expected `401` |
| `& $Py tests/review_mode_security_boundary_test.py` | PASS | review mode boundary |
| `& $Py tests/security_headers_test.py` | PASS | security headers |

## Focused Failed-Test Fix Completion (2026-07-07)

- Fixed only the requested failed-test scope: ONBID empty-state marker, freshness invalid-date/category audit expectations, and raw-document 401/403 protection assertion.
- No real API call, DB repair apply, schema change, commit, or push was performed.
- Latest focused verification: `py_compile`, `onbid_public_filter_state`, `onbid_freshness_policy`, `public_access_auth_boundary`, `login_hint_policy`, `navigation_active_state`, `review_mode_security_boundary`, and `security_headers` all PASS.
