# Project Current Status

Updated: 2026-07-10

## Current Branch

Branch: `codex/devpack-v009-onbid-data-source-status-quality`

Latest work: devpack v009 - ONBID data-volume refresh, KST deadline-state repair, source-document fallback, detail consistency, admin data-quality operations view, default pytest policy, and external tunnel QA.

## v009 Completed Capabilities

- KST-aware deadline state prevents past dates from displaying as `D+N` or active.
- `/onbid/today` and seven-day closing filters include active/upcoming rows only.
- Details without an official URL show non-action direct-confirmation fields instead of a fake source link.
- Detail checklists use independent confirmed/needs-confirmation states; false detail availability is zero.
- `/admin/onbid-data-quality` reports public freshness, category counts, original URL/detail coverage, missing fields, source API counts, and status conflicts.
- Default `python -m pytest` is isolated from external/environment-dependent tests.

## Data State

Backup before v009 DB work:

```text
C:\Users\xogns\Documents\testAuction\court_auction_platform\storage\backups\auction_data_20260710_072156.db
sha256: E75EE570831C33D9F0559A146AD5D899484F1C02B4E12E7F955F36D649533F75
```

v009 real ONBID refresh:

```text
real_estate: fetched 500, accepted 500, inserted 438, duplicates 62
movable: fetched 500, accepted 500, inserted 500, duplicates 0
notice: 20 fetched, all stale under public freshness policy
national_property: 50 fetched, 0 accepted (41 stale, 9 unknown-date)
```

Current public-visible fresh non-sample:

```text
total 1076
real_estate 516
movable 560
national_property 0
active_or_upcoming 1016
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

All core, v007/v008, and v009 script-style tests passed. `python -m pytest` passes with 2 default product tests; integration and external tests are now explicitly excluded from the default collection.

## External QA

Cloudflare quick tunnel used:

```text
https://directed-install-mainland-chapter.trycloudflare.com
```

Routes `/`, `/onbid`, `/onbid/today`, ONBID category/data-quality filters, `/cases`, and `/disclaimer` returned 200. Detail QA confirmed no D+ label, original-link fallback for no-URL items, real_estate CTA visible, and movable CTA hidden.

## Remaining Risks

- Direct original URLs are still unavailable from the tested ONBID payloads; the detail fallback is active.
- national_property needs a better fresh-date/API parameter strategy.
- 17 raw source-status values conflict with past deadlines; public display is corrected and the admin dashboard exposes the queue.
