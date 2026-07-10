# Project Current Status

Updated: 2026-07-10

## Current Branch

Branch: `codex/devpack-v010-beta-release-candidate-ux`

Latest work: devpack v010 Beta RC UX — top-level ONBID category navigation, compact shared pagination, query-state preservation, pass/5-second undo, truthful today queue, home diversity, beta mode UI, local CSS, security hardening, expanded pytest/Playwright/axe QA.

## Current Product State

- ONBID category tabs are directly below the page title and are the only category selection control.
- Desktop pagination is windowed; mobile uses previous/current-total/next; ONBID and cases share one component.
- Logged-in users can favorite, pass, undo, restore from the passed list, and save notes.
- Today queue uses KST first-seen date and never silently presents recent items as today items.
- Home counts match their queries; preview prioritizes two real-estate and two movable items with notice diversity.
- Beta banner replaces public technical review copy; internal review details remain admin-only.
- Tailwind CDN was replaced with a 28 KB compiled local stylesheet.
- Official ONBID homepage + identifier-copy fallback is used; no unverified detail URL is generated.

## Data State

```text
public_visible_fresh_non_sample 1076
active_or_upcoming 1015
real_estate 516
movable 560
national_property 0
duplicate_groups 0
sample_public 0
stale_or_unknown_public 0
public_status_conflicts 0
last_updated 2026-07-10 07:46 KST
```

Pre-v010 backup:

```text
storage/backups/auction_data_20260710_110441.db
sha256 D0FD97632C840086AD6D983CD69AD8390531CBD09D091DC5F2C870DA03D3731B
```

## Verification

- Default pytest: 58 passed, 2 visual deselected
- Playwright visual/login E2E: 2 passed
- Legacy core scripts: 4 passed in beta runner; 13 additional security/product scripts passed
- axe-core critical/serious: 0
- Body overflow: 0 at 360, 390, 768, 1024, 1440 widths
- `run_beta_qa.ps1 -Visual`: PASS
- Cloudflare quick tunnel: public routes 200, unauthenticated admin 303, noindex/noarchive present
- Sensitive staged files: 0

## Release Assessment

`조건부 베타 오픈 가능`

Conditions: stable named staging URL, beta account/operations policy, single-instance rate-limit/session-revoke constraint or shared store, and monitoring. Direct ONBID item links and national-property fresh data remain unresolved; safe fallbacks are active.

Full detail: `reports/devpacks/devpack_v010_beta_release_candidate_result_bundle.md`
