# Project Current Status

Updated: 2026-07-06

## Current Baseline

`court_auction_platform` is on v004 Real ONBID API & Public Beta Operations work.

## v004 Completed Capabilities

- Public `/onbid` filtering is centered on region, price, and category.
- ONBID categories are derived as `real_estate`, `movable`, `national_property`, and `other`; `national_property` is kept independent.
- Public ONBID pages show missing-information badges instead of numeric quality scores.
- `/onbid/{auction_item_id}` shows other items linked to the same notice.
- Real ONBID limited calls were attempted with `Limit=20`, `MaxPages=1` after DB backup when a configured key was present.
- Admin collection observability includes category counts, national_property count, missing-information rates, notice links, and recent run status.
- Dry-run operation helpers exist for restore, scheduler inspection, and log retention.
- Public legal/SEO routes include `/privacy`, `/terms`, `/disclaimer`, protected `robots.txt`, and dynamic public sitemap entries.

## Real API Summary

- Backup before real calls: `storage/backups/auction_data_20260706_232631.db`
- `real_estate`: succeeded, fetched 20, inserted 15, duplicates 5.
- `movable`: succeeded, fetched 0.
- `notice`: succeeded, fetched 20 notices and 400 notice item rows, inserted 3 notices, updated 17 notices, created 60 notice-item links, updated 340 links.
- `national_property`: succeeded through `run_onbid_probe.ps1`, fetched 20, inserted 1, duplicates 19.
- API key value was not printed.

## Public/Auth/Admin Boundaries

- Public users can browse ONBID and case basic pages.
- Login is required for ONBID preferences and raw document access.
- Admin APIs, including `/api/admin/onbid-quality`, remain admin-protected.
- Public DTOs do not expose raw payload, internal raw file paths, OCR full text, or case AI analysis.

## Tests

Verified with Codex runtime Python:

```powershell
& $Py -m py_compile main_app.py backend/database/models.py backend/database/session.py backend/web/routers/auctions.py backend/web/routers/cases.py backend/web/routers/admin_operations.py backend/services/auction_items.py backend/services/onbid_observability.py backend/onbid/client.py backend/workers/onbid_sync.py tests/onbid_category_filter_test.py tests/sitemap_public_routes_test.py
& $Py tests/onbid_category_filter_test.py
& $Py tests/sitemap_public_routes_test.py
& $Py tests/onbid_module_test.py
& $Py tests/page_response_smoke_test.py
& $Py tests/router_boundary_test.py
& $Py tests/isolated_operations_test.py
& $Py tests/public_access_auth_boundary_test.py
powershell -ExecutionPolicy Bypass -File .\run_onbid_scheduled_sync.ps1 -Sample -ApiKind notice -Limit 20 -MaxPages 1 -IncludeNoticeDetails -IncludeNoticeItems
```

## Remaining Risks

- ONBID movable returned zero rows for the current query window; v005 should tune movable filters with more real samples.
- National property mapping is real-sample based but still relies on derived category metadata rather than a stored DB column.
- Scheduler tasks are not registered in Windows Task Scheduler; `check_scheduled_tasks.ps1` reports missing tasks by design.
- Legal/privacy pages are beta drafts, not reviewed final legal text.

## v005 Priorities

1. Improve ONBID field mapping with more real national_property/movable samples.
2. Add non-destructive indexes if larger real datasets show query slowdown.
3. Register and rehearse production scheduler jobs.
4. Formalize privacy/terms/disclaimer text.
5. Add backup/restore rehearsal and alerting around failed syncs.
