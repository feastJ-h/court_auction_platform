# Codex Development Result Bundle v004

## 1. Work Metadata

- Git root: `C:/Users/xogns/Documents/testAuction/court_auction_platform`
- Branch: `codex/devpack-v004-real-onbid-operations`
- Base commit: `999f04d docs: add v004 devpack instructions`
- Final commit(s): not committed, not pushed
- Remote: `https://github.com/feastJ-h/court_auction_platform.git`
- Work start status: clean
- Work end status: pending local edits only
- Startup log evidence:
  - `git rev-parse --show-toplevel`: `C:/Users/xogns/Documents/testAuction/court_auction_platform`
  - `git branch --show-current`: `codex/devpack-v004-real-onbid-operations`
  - `git status --short`: no output at start
  - `git remote -v`: origin fetch/push `https://github.com/feastJ-h/court_auction_platform.git`
  - `git --no-pager log --oneline --decorate -8`: HEAD `999f04d`

## 2. High-Level Result

Implemented the v004 public ONBID category/filter UX, missing-information badges, same-notice item UX, real limited ONBID API operations, national_property collection/probe support, admin observability additions, dry-run operation scripts, SEO/legal route updates, and focused test coverage.

No commit or push was performed.

## 3. Core Scope Results

### 3.1 ONBID Region/Price/Category UX

- `/onbid` public filters now surface region, price min/max/presets, and category.
- Legacy backend query parameters remain accepted for compatibility, but public UI no longer promotes status, closing-day, discount-rate, notice-link, or detail filters.
- No-result UX now tells users to broaden region/price and notes early real API collection can have sparse region/category data.

### 3.2 Category Rules

- Added `derive_onbid_category(item_or_payload) -> str`.
- Added `get_onbid_category_label(category: str) -> str`.
- Categories: `real_estate`, `movable`, `national_property`, `other`.
- `national_property` is independent and not split into movable/real_estate.

### 3.3 Missing-Information Badges

- Added `build_onbid_info_badges(item)`.
- Public list/detail templates show available/missing badges.
- Public numeric quality/search score UI was removed from ONBID detail.

### 3.4 Same-Notice Items

- Added same-notice lookup from `AuctionNoticeItemLink`.
- `/onbid/{id}` shows up to 20 other items from the same notice.
- Notice cards link to `/onbid?notice_id={notice_id}`.

### 3.5 Real API 20-Row Sync/Probe

- Ran DB backup before real API DB writes.
- Real calls used `Limit=20`, `MaxPages=1`.
- API key was checked as configured and never printed.

### 3.6 National Property API

- Added `national_property` API kind.
- Added `run_onbid_probe.ps1`.
- Added real/sample `fetch_national_property_items` path based on bid-target endpoint settings.
- Sparse rows get deterministic derived duplicate keys when official IDs are absent.

### 3.7 Field Mapping/Normalizer

- Normalizer now preserves `_source_api` in raw payload metadata.
- Category derivation uses source API, asset type, usage, raw payload category fields, and API kind hints.
- Duplicate identity remains `source + cltr_mng_no + pbct_cdtn_no`.

### 3.8 Backup Plan

- Backup script was run before real API writes.
- Backup: `storage/backups/auction_data_20260706_232631.db`
- SHA256: `91B4BC6DFDD7A737F45CB6E644A81567440A453503CC9C8DB1DA9BCE9002142D`
- Restore dry-run verified with `restore_database.ps1 -DryRun`.

### 3.9 Large-Data Performance

- Added category/filter and same-notice focused tests.
- No DB indexes were added in v004; observe query performance after larger real collections before adding non-destructive indexes.

## 4. Extended Scope Results

### 4.1 Admin Observability

- `/api/admin/onbid-quality` now includes category counts, `national_property` count, and missing-information rates.
- `/admin/collection` displays category distribution and missing price/location/schedule rates.

### 4.2 Operations Readiness

- Added dry-run helpers:
  - `restore_database.ps1`
  - `check_scheduled_tasks.ps1`
  - `run_log_retention.ps1`
  - `run_onbid_probe.ps1`

### 4.3 Backup/Restore Dry-Run

- `restore_database.ps1 -BackupPath storage\backups\auction_data_20260706_232631.db -DryRun` succeeded.
- Actual restore requires `-ConfirmRestore`.

### 4.4 Scheduler Dry-Run

- `check_scheduled_tasks.ps1` ran and reported missing expected tasks:
  - `CourtAuction-Onbid-List`
  - `CourtAuction-Onbid-Notice`
  - `CourtAuction-Court-Crawl`
- No task was registered automatically.

### 4.5 Log Retention

- Added `run_log_retention.ps1`.
- Default behavior is dry-run; deletion requires `-Apply`.
- Raw/processed source document areas are not deletion targets.

### 4.6 Sitemap/Robots

- `robots.txt` disallows `/admin`, `/api/admin`, `/user`, `/my`, `/documents/raw`, `/storage`.
- `sitemap.xml` includes public static routes plus limited public `/onbid/{id}` and `/cases/{id}` entries.
- Protected paths are excluded.

### 4.7 Case Public Search

- `/cases` accepts additional public filters for region, status, notice date lower bound, and expire date upper bound.
- Public case DTO remains free of AI analysis, OCR full text, raw file path, and raw document download URL.

### 4.8 Privacy/Terms/Disclaimer

- Added `/privacy` and `/terms`.
- `/privacy-draft` redirects to `/privacy`.
- Existing `/disclaimer` remains.
- Text is beta draft content, not final legal review.

## 5. Stretch Scope Results

- Added source/check badges and external notice links on ONBID detail without exposing raw payload paths.
- Dynamic sitemap now includes public detail URLs.
- UTF-8 cleanup was applied in newly touched ONBID/legal templates where practical; historical mojibake in unrelated templates/reports was not broadly rewritten.

## 6. Real API Call Results

| API kind | Limit | MaxPages | Result | Stored/Updated/Duplicate/Failed | Notes |
| --- | ---: | ---: | --- | --- | --- |
| `real_estate` | 20 | 1 | succeeded | inserted 15, duplicates 5 | total_count 62441, used_sample false |
| `movable` | 20 | 1 | succeeded | fetched 0 | total_count 0, used_sample false |
| `notice` | 20 | 1 | succeeded | notices inserted 3, updated 17; notice items inserted 60, duplicates 340; links created 60, updated 340 | 20 notices and 400 notice item rows processed |
| `national_property` | 20 | 1 | succeeded | inserted 1, duplicates 19 | total_count 80925, used_sample false |

Initial non-escalated real-estate attempt failed with sandbox/network denial (`WinError 10013`); rerun with approved escalation succeeded.

## 7. National Property Field Mapping Summary

| Source key candidates | Mapped field | Confidence | Notes |
| --- | --- | --- | --- |
| `cltrMngNo`, `cltrNo` | `cltr_mng_no` | medium | deterministic derived fallback used when absent |
| `pbctCdtnNo`, `pbctCdtnNoNm` | `pbct_cdtn_no` | medium | deterministic derived fallback used when absent |
| `onbidPbancNo`, `pbancMngNo`, `pbancNo` | `pbanc_mng_no` | medium | supports notice linkage when present |
| `onbidCltrNm`, `cltrNm`, `itemName` | `item_name` | medium | public display falls back to missing badge if sparse |
| `prptDivNm`, `cltrUsgLclsCtgrNm`, source API metadata | category derivation | high for `national_property` source_api | no stored category column added |
| `cltrRadr`, location parts | `address` | medium | missing badge shown when absent |
| `apslEvlAmt` | `appraisal_price` | medium | digits-only parse |
| `lowstBidPrcIndctCont` | `minimum_bid_price` | medium | price filter uses minimum bid price |
| `cltrBidBgngDt`, `cltrBidEndDt`, `opengDt` | bid/open datetimes | medium | normalized to date/time strings |

## 8. Changed Files

| File | Summary | Risk | Notes |
| --- | --- | --- | --- |
| `backend/services/auction_items.py` | categories, badges, deterministic fallback keys, category/notice filters, same-notice lookup | medium | core service behavior |
| `backend/onbid/client.py` | national_property sample/real fetch path | medium | depends on configured bid-target endpoint |
| `backend/workers/onbid_sync.py` | national_property sync API kind | medium | verified real probe |
| `backend/web/routers/auctions.py` | category/notice filters, same-notice context, max_pages admin sync | medium | public/admin route behavior |
| `backend/services/onbid_observability.py` | category and missing-info metrics | low | admin-only |
| `frontend/templates/auctions/index.html` | public ONBID filter UX and badges | medium | public UI |
| `frontend/templates/auctions/detail.html` | badges, same-notice items, removed numeric score UI | medium | public UI |
| `frontend/templates/admin/collection.html` | category/missing metrics, 20-row real API buttons | low | admin UI |
| `main_app.py` | privacy/terms routes, robots, dynamic sitemap | medium | public SEO routes |
| `frontend/templates/public/terms.html` | beta terms page | low | draft legal copy |
| `backend/web/routers/cases.py` | lightweight extra public filters | low | DTO boundary retained |
| `run_onbid_scheduled_sync.ps1` | accepts `national_property` | low | script option |
| `run_onbid_probe.ps1` | new limited probe script | low | dry/limited operation |
| `restore_database.ps1` | restore dry-run/confirm helper | medium | actual restore gated by `-ConfirmRestore` |
| `check_scheduled_tasks.ps1` | scheduler inspection dry-run | low | read-only |
| `run_log_retention.ps1` | log/backup retention dry-run | medium | deletion requires `-Apply`; no raw/processed deletion |
| `tests/onbid_category_filter_test.py` | v004 ONBID category/badge/same-notice tests | low | isolated DB |
| `tests/sitemap_public_routes_test.py` | robots/sitemap/legal route tests | low | isolated DB |
| `tests/router_boundary_test.py` | expected route additions | low | test metadata |
| `tests/public_access_auth_boundary_test.py` | legal route public access coverage | low | auth boundary |
| `docs/migration_ledger.md` | v004 no-schema migration note | low | docs |
| `reports/project-result_current.md` | v004 current state | low | docs |

## 9. DB/Migration Changes

- New tables: none
- New columns: none
- New indexes: none
- Non-destructive: yes
- Rollback: restore the pre-run DB backup if real API inserted rows must be reverted.

## 10. Public/Login/Admin Boundaries

- Public ONBID responses do not expose raw payloads.
- Public case DTO remains free of AI analysis, OCR full text, raw file path, and raw download URL.
- `/documents/raw/{raw_doc_id}` remains login/admin protected.
- ONBID preference POST/API requires login.
- Admin collection and ONBID quality APIs require admin authentication.

## 11. Test Results

| Command | Result | Notes |
| --- | --- | --- |
| `py_compile ...` | pass | edited backend modules and new tests |
| `tests/onbid_category_filter_test.py` | pass | category, national_property, badges, same notice, admin metrics |
| `tests/sitemap_public_routes_test.py` | pass | robots/sitemap/legal routes |
| `tests/onbid_module_test.py` | pass | existing ONBID persistence/observability/link test |
| `tests/page_response_smoke_test.py` | pass | page/admin/raw document smoke |
| `tests/router_boundary_test.py` | pass | route registration |
| `tests/isolated_operations_test.py` | pass | existing guarded operations |
| `tests/public_access_auth_boundary_test.py` | pass | public/auth/admin boundary |
| `run_onbid_scheduled_sync.ps1 -Sample -ApiKind notice -Limit 20 -MaxPages 1 -IncludeNoticeDetails -IncludeNoticeItems` | pass | sample scheduler smoke |
| `restore_database.ps1 ... -DryRun` | pass | no restore applied |
| `run_log_retention.ps1 -DryRun` | pass | no expired candidates printed |
| `check_scheduled_tasks.ps1` | pass | expected tasks currently missing |

## 12. Local Server Check Guide

Not started automatically in this run. To inspect manually:

```powershell
powershell -ExecutionPolicy Bypass -File .\run_fastapi.ps1
```

Then open:

- `http://127.0.0.1:8000/onbid`
- `http://127.0.0.1:8000/onbid?category=national_property`
- `http://127.0.0.1:8000/admin/collection` after admin login

## 13. Incomplete / Deferred / Risks

- Movable real API returned zero rows for the current call; v005 should tune movable filters with more samples.
- `national_property` is derived at service level, not stored as a DB column.
- No new indexes were added; large real datasets may need non-destructive indexes later.
- Scheduler tasks were not registered automatically.
- Legal/privacy text is beta draft content and needs formal review.
- Alerts, real AdSense integration, and auction results were intentionally excluded.

## 14. v005 Recommended Work

1. Tune ONBID movable and national_property mappings from additional real samples.
2. Add non-destructive indexes after measuring `/onbid` performance on larger datasets.
3. Register and rehearse production scheduled tasks.
4. Add failure notification/alerting in a separate alert-focused pack.
5. Formalize privacy/terms/disclaimer.

## 15. Codex CLI Operations Memo

- No commit or push was performed.
- Real API calls were first blocked by sandbox networking, then succeeded after explicit escalation.
- API secrets were not printed in shell output, logs, or docs.
- Runtime DB backup/log files remain under ignored runtime paths and must not be committed.
