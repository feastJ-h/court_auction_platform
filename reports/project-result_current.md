# Project Current Status

Updated: 2026-07-10

## Current Branch

Branch: `codex/devpack-v011-beta-launch-hardening`

Latest work: devpack v011 Beta Launch Hardening — ONBID category navigation recovery, rendered/result contract tests, beta fail-closed config, CSRF/POST logout, persistent security state, invite account lifecycle, health/process/tunnel gates, sync history, backup restore, CI and operations runbooks.

## Current Product State

- `/onbid` category tabs now produce distinct canonical URLs and strictly isolated results.
- Public fresh data: total 1,076 / real estate 516 / movable 560 / national property 0; duplicates/sample/stale-or-unknown exposure 0.
- Beta/production reject default secrets, default admin password, test DB and local login hint.
- Admin accounts are one-time bootstrapped; beta users must change their temporary password and accept versioned policies.
- Signed double-submit CSRF protects HTML/JSON mutations; logout is POST-only; revoke/rate-limit state persists in SQLite with optional Redis adapter.
- live/ready/version endpoints, structured request IDs, single-worker start/stop/status, quick/named tunnel runbook and external E2E are available.
- Official ONBID URLs are never guessed. Stored official URLs are used; otherwise identifier-copy + official-home fallback remains.

## Verification

```text
default pytest 80 passed
Playwright visual/login E2E 2 passed
axe critical/serious 0
body overflow 0 at 360/390/768/1024/1440
legacy core scripts 4 passed
external quick-tunnel E2E PASS
backup restore integrity/count/startup PASS
pip-audit 0 known vulnerabilities
npm critical/high 0 (17 moderate in Lighthouse QA dependency tree)
Lighthouse performance 1.00 / accessibility 1.00 / best-practices 0.96 / SEO 0.54 (beta noindex)
```

## Release Assessment

Invite-only supervised beta: `GO`.

Stable public beta hostname: `NO-GO` until existing Cloudflare account/domain credentials are provided and named-tunnel external gates are rerun. Quick tunnel is verified but not an uptime commitment.

Remote branch push: `origin/codex/devpack-v011-beta-launch-hardening` PASS.

Full detail: `reports/devpacks/devpack_v011_beta_launch_hardening_result_bundle.md`
