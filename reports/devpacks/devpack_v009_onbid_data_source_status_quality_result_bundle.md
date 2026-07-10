# Devpack v009 Result Bundle

## 1. Metadata

- Date: 2026-07-10 KST
- Branch: `codex/devpack-v009-onbid-data-source-status-quality`
- Base: `codex/devpack-v008-master-review-data-ux-loop` at `c3a57da`
- Scope: ONBID data quantity, KST deadline state, original-document fallback, detail consistency, admin data quality, and pytest policy.

## 2. Start Git State

- Git root: `C:/Users/xogns/Documents/testAuction/court_auction_platform`
- Initial branch: `codex/devpack-v008-master-review-data-ux-loop`
- Initial status: one untracked user-supplied v009 instruction file.
- Remote: `origin https://github.com/feastJ-h/court_auction_platform.git`
- v008 was already up to date with origin before the v009 branch was created.

## 3. Backup

- Source DB: `C:\Users\xogns\Documents\testAuction\court_auction_platform\auction_data.db`
- Backup: `storage\backups\auction_data_20260710_072156.db`
- SHA-256: `E75EE570831C33D9F0559A146AD5D899484F1C02B4E12E7F955F36D649533F75`
- Restore was not run because all DB changes were additive ONBID upserts and validation passed.

## 4. v008 Carry-Forward

v008 supplied the public review routes, detail four-zone layout, product analytics, data issue queue, and baseline freshness filters. It left public fresh data below target and did not normalize deadline presentation at KST time precision.

## 5. Pre-Work Audit

Initial DB audit: 226 ONBID rows, 145 fresh, 61 stale, 20 invalid-date, and 0 unknown-date. The v008 result reported 138 public-visible fresh non-sample rows, 78 active/upcoming rows, 78 real-estate rows, 60 movable rows, 0 national-property rows, and 0 duplicate keys.

The initial derived-field dry-run checked 226 rows and required 0 updates. The primary defects were date-only D-day logic, raw source status being able to conflict with deadline state, no usable original URL coverage, and detail-marker semantics that could overstate detail availability.

## 6. API Call Summary

| ApiKind | PageNo | Limit | MaxPages | DateRange | fetched | accepted_fresh | inserted | duplicates | dropped_stale | dropped_unknown_date | dropped_invalid_date | detail_attempted | detail_succeeded |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| real_estate | 1 | 50 | 10 | 2026-07-10 to 2026-11-07 | 500 | 500 | 438 | 62 | 0 | 0 | 0 | 20 | not separately returned |
| movable | 1 | 50 | 10 | 2026-07-10 to 2026-10-08 | 500 | 500 | 500 | 0 | 0 | 0 | 0 | 20 | not separately returned |
| notice | 1 | 20 | 1 | MinDate 2025-01-01 | 20 notices | 0 items | 0 | 0 | 20 | 0 | 0 | notice detail/items requested | 0 linked fresh items |
| national_property | 1 | 50 | 1 | MinDate 2025-01-01 | 50 | 0 | 0 | 0 | 41 | 9 | 0 | 0 | 0 |

The first real-estate attempt was blocked by the sandbox socket policy, then rerun with approved external access. API keys and raw payloads were never output or committed.

## 7. Data Before/After

| Metric | Before | After |
| --- | ---: | ---: |
| Public-visible fresh non-sample | 138 | 1,076 |
| Active or upcoming | 78 | 1,016 |
| Real estate | 78 | 516 |
| Movable | 60 | 560 |
| National property | 0 | 0 |
| Duplicate key count | 0 | 0 |
| Sample/fixture public exposure | 0 | 0 |

National-property collection was attempted against the real API. The returned page had no current valid freshness date under the public policy, so its stale/unknown records remain excluded instead of being exposed as current data.

## 8. Original URL and Detail Quality

Direct original URL coverage remained 0% before and after the list, detail, and notice API probes. The ONBID responses collected in this run did not provide an acceptable public original URL field, and notice results were stale under the policy.

The product now renders a non-action fallback on details without an original URL. It supplies only onbid number, auction number, agency, item name, and deadline for direct ONBID confirmation. It does not construct a misleading `원문 보기` link. Original-link analytics continues to store item id/category only, never a full URL or query secret.

Detail body coverage after enrichment is 100%; false `상세 설명: 확인됨` count is 0. The checklist now labels each independent datum as `확인됨` or `확인 필요`.

## 9. Deadline and Status Repair

- Added KST-aware deadline parsing; date-only values resolve to 23:59:59 KST.
- Past deadlines use `입찰마감` or `마감 후 N일`, never `D+N`.
- Public serializer overrides a stale raw "in progress" source value with the deadline-derived closed state.
- `/onbid` prioritizes active/upcoming rows; `/onbid/today` only includes active/upcoming rows; `closing_within_days` filters active/upcoming rows only.
- Home counts and preview items now use the same active/upcoming boundary.

The operations dashboard retains 17 raw source-status conflicts for follow-up, but public display uses the corrected deadline status, so no past-deadline item is shown as active.

## 10. Implementation Files

- `backend/services/auction_items.py`
- `backend/services/onbid_observability.py`
- `backend/web/routers/auctions.py`
- `backend/web/routers/admin_operations.py`
- `frontend/templates/auctions/detail.html`
- `frontend/templates/admin/onbid_data_quality.html`
- `main_app.py`
- `run_onbid_scheduled_sync.ps1`
- `pytest.ini`
- v009 tests under `tests/`

No schema change was required, so `docs/migration_ledger.md` was not changed.

## 11. Privacy and Secret Review

- No `.env`, database, storage backup, runtime log, raw payload dump, API key, secret, or token was staged.
- Public serializers do not return raw payloads, internal paths, OCR body, or raw documents.
- Original-link analytics strips full URLs and unsafe metadata keys.

## 12. Local and External QA

Local QA ran all required public routes plus active real-estate, active movable, and ended detail examples. Public routes returned 200. Admin routes redirected to the protected login flow when unauthenticated. No `D+` label was found. Both no-URL details displayed the direct-confirmation fallback; the real-estate detail displayed the Development Insight CTA and the movable detail did not.

Cloudflare quick tunnel QA: `https://directed-install-mainland-chapter.trycloudflare.com`

- `/`, `/onbid`, `/onbid/today`, all requested list filters, `/cases`, `/disclaimer`, and sampled details returned 200.
- `/onbid/today` showed no `D+` labels.
- Real-estate detail `89`: fallback shown, Development Insight CTA shown.
- Movable detail `665`: fallback shown, Development Insight CTA hidden.
- Tunnel and uvicorn processes were stopped after QA.

## 13. Tests

All required script-style core and v007/v008 tests run in this devpack passed after the CTA test hook was restored. New v009 tests passed:

- deadline KST state and date-only boundaries
- today excludes ended rows
- closing-within-days active-only filter
- home empty-state route
- original URL coverage and fallback
- original-link analytics safety
- detail consistency/checklist/no false availability
- admin data-quality dashboard
- pytest collection policy

`python -m pytest` passed: 2 collected default product tests. `pytest.ini` restricts default collection to `tests/test_*.py` and excludes explicitly marked `integration` and `external` tests; script-style tests remain runnable through their documented commands.

## 14. Remaining Risks

- Direct original URL coverage is 0% because current ONBID API responses did not provide a safe official URL. The detail fallback is implemented, but a verified official search URL pattern is still needed for a future direct-link improvement.
- National-property fresh rows remain unavailable because the source page returned only stale or unknown dates.
- 17 raw source-status values conflict with their past deadline. Public rendering is corrected; data-source repair remains an operations follow-up.
- No DB restore rehearsal was required for this non-destructive run.

## 15. Next Devpack Recommendation

Validate an official ONBID search/detail URL pattern with a small approved sample, improve national-property date normalization, and add an admin workflow to resolve the retained raw-status conflict queue.

## 16. Completion Git State

- Final status: clean worktree after commit.
- Final commit: `a2b1ae8 feat: improve onbid data source status quality v009`
- Push: `origin/codex/devpack-v009-onbid-data-source-status-quality` created and set as upstream.
- Sensitive staged-file scan: no matches for environment files, databases, storage/logs, runtime settings, or invalid git metadata.
