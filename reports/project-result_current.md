# Project Current Status

Updated: 2026-07-10

## Current Baseline

Branch: `codex/devpack-v007-product-ux-safety-analytics`

Latest completed work: devpack v007 Nightly - product UX safety, today review flow, data confirmation filter, data issue reports, public-safe review summary sharing, analytics foundation, and Development Insight CTA.

## v007 Completed Capabilities

- Public copy now emphasizes source-document confirmation and removes public “AI analysis” phrasing from public ONBID/case/public templates.
- `/onbid/today` provides a logged-in today review queue with pass/favorite completion state.
- `/onbid?data_quality=needs_confirmation` filters fresh public ONBID rows that need source/data confirmation.
- ONBID detail pages support issue reports without immediately exposing report contents publicly.
- Logged-in users can create public-safe review summary share pages at `/onbid/share/{token}`.
- Shared summaries are `noindex, noarchive` and exclude private notes, account info, raw AI/OCR text, raw payloads, and internal paths.
- Product analytics events are stored in `product_analytics_events` with sanitized metadata.
- Development Insight CTA appears only for real-estate ONBID items and uses conservative disclaimer copy without external API integration.
- My ONBID includes a memo tab at `/my/onbid/notes`.

## Schema

New non-destructive tables:

- `product_analytics_events`
- `onbid_data_issue_reports`
- `onbid_review_summary_shares`

Migration path remains SQLite `create_all` plus `ensure_schema_migrations`; no existing columns/tables/data were deleted.

Before applying local DB migration:

```text
backup: C:\Users\xogns\Documents\testAuction\court_auction_platform\storage\backups\auction_data_20260710_014324.db
sha256: 20BED6D406F1571BBD91EA3B96DC0BFA1420C2099E6D458FCE263D909ED95EEB
restore tested: not run
```

## Tests

Verified with Codex runtime Python:

```powershell
& $Py -m py_compile backend\database\models.py backend\database\session.py backend\services\auction_items.py backend\services\product_engagement.py backend\web\routers\auctions.py tests\_v007_helpers.py tests\product_copy_safety_test.py tests\onbid_today_review_completion_test.py tests\onbid_data_quality_needed_filter_test.py tests\onbid_data_issue_report_test.py tests\onbid_review_summary_share_test.py tests\product_analytics_events_test.py tests\development_insight_cta_safety_test.py
& $Py tests\onbid_freshness_policy_test.py
& $Py tests\onbid_public_filter_state_test.py
& $Py tests\onbid_category_mapping_test.py
& $Py tests\sitemap_fresh_public_routes_test.py
& $Py tests\onbid_module_test.py
& $Py tests\page_response_smoke_test.py
& $Py tests\public_access_auth_boundary_test.py
& $Py tests\product_copy_safety_test.py
& $Py tests\onbid_today_review_completion_test.py
& $Py tests\onbid_data_quality_needed_filter_test.py
& $Py tests\onbid_data_issue_report_test.py
& $Py tests\onbid_review_summary_share_test.py
& $Py tests\product_analytics_events_test.py
& $Py tests\development_insight_cta_safety_test.py
& $Py tests\router_boundary_test.py
& $Py tests\isolated_operations_test.py
```

All commands above passed. Common warning: Starlette `httpx` deprecation warning from `fastapi.testclient`.

Full pytest was attempted but unavailable in the bundled runtime:

```text
No module named pytest
```

## Remaining Risks

- `repair_onbid_derived_fields.ps1 -Apply` was not run.
- Development Insight is only a conservative CTA/info flow; no Archi-Pro or external API integration was added.
- Issue reports require future admin review UI and operations policy.
- Shared summary revoke/manage UI is not yet implemented.
- Real ONBID backfill, notice-list API expansion, national property API validation, production ads, payments, and notification integrations remain deferred.
