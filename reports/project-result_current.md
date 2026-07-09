# Project Current Status

Updated: 2026-07-10

## Current Branch

Branch: `codex/devpack-v008-master-review-data-ux-loop`

Latest work: devpack v008 master loop - public ONBID UX recovery, home curation, today review stabilization, detail 4-Zone layout, shared summary management, admin issue queue, product analytics summary, limited ONBID data refresh, and external tunnel QA.

## v008 Completed Capabilities

- Home now shows four curation cards and recent public ONBID items.
- `/onbid` uses clearer Korean copy, active/upcoming priority, source-document checks, original-link prominence, data-quality guidance, and login CTA for personal actions.
- `/onbid/today` returns 200 for anonymous and logged-in users and keeps review completion summary.
- `/onbid/{id}` is organized into 4 zones: source status, objective facts, source checkpoints, and personal actions.
- Development Insight CTA is visible only for real_estate details and hidden for movable details.
- `/my/onbid/shared-summaries` lets users view and revoke public-safe share links.
- `/admin/onbid-issue-reports` lets admins review ONBID data issue reports.
- `/admin/product-analytics` summarizes sanitized product events without raw payload, full URL, or private memo exposure.
- Public mojibake and banned-copy scans pass on local and Cloudflare QA routes.

## Data State

Backup before DB work:

```text
C:\Users\xogns\Documents\testAuction\court_auction_platform\storage\backups\auction_data_20260710_065322.db
sha256: DE754FACDE6C183D3703F580D8A0E326C6E4AE84CE0A44AE33284F6DACF82BEF
```

Limited ONBID refresh:

```text
real_estate: fetched 20, accepted 20, inserted 18, duplicates 2
movable: fetched 20, accepted 20, inserted 20, duplicates 0
national_property: fetched 20, accepted 0, dropped stale/unknown 20
```

Current public-visible fresh non-sample:

```text
total 138
real_estate 78
movable 60
national_property 0
active_or_upcoming 78
duplicate_key_count 0
```

The v008 target of 250 public-visible fresh non-sample rows remains unmet.

## Tests

Script-style required and v008 tests passed, including:

```text
onbid_freshness_policy_test
onbid_public_filter_state_test
onbid_category_mapping_test
sitemap_fresh_public_routes_test
onbid_module_test
page_response_smoke_test
public_access_auth_boundary_test
router_boundary_test
isolated_operations_test
product_copy_safety_test
onbid_today_review_completion_test
onbid_data_quality_needed_filter_test
onbid_data_issue_report_test
onbid_review_summary_share_test
product_analytics_events_test
development_insight_cta_safety_test
all 11 v008 new tests
```

`python -m pytest` was installed and attempted. It collected old pytest-style tests and failed on environment-dependent or pre-existing assertions: default analyzer provider mismatch, blocked court-site Playwright access, OCR-required PDF with empty extraction, and orchestrator network access.

## External QA

Cloudflare quick tunnel used:

```text
https://lamp-walnut-auckland-connected.trycloudflare.com
```

Routes `/`, `/onbid`, `/onbid/today`, ONBID category/data-quality filters, `/cases`, and `/disclaimer` returned 200 with mojibake=False and banned=False. Detail QA confirmed real_estate CTA visible and movable CTA hidden.

## Remaining Risks

- Data volume still below v008 goals.
- national_property needs a better fresh-date/API parameter strategy.
- Operating DB items currently have little or no public original detail URL linkage.
- Full pytest collection needs a separate cleanup pass because it includes real-network and legacy environment assumptions.
