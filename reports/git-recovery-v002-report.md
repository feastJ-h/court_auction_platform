# Git recovery report for v002

Generated: 2026-07-06
Workspace: `C:\Users\xogns\Documents\testAuction\court_auction_platform`

## Scope

This was a Git recovery-only task. No feature development, DB schema edits, `git init`, `git reset --hard`, `git clean`, `.git` deletion, `.env` staging, DB staging, or `storage/` staging was performed.

Protected data policy observed:

- `.env` was not read into this report and was not staged.
- `*.db` files were not staged.
- `storage/`, `storage/logs/`, raw documents, cookies, sessions, and API keys were not exposed or staged.
- Ignored storage/raw file names are intentionally omitted from this report.

## Initial diagnostic commands

### `pwd`

```text
Path
----
C:\Users\xogns\Documents\testAuction
```

### `.git` directories found before recovery action

Command:

```powershell
Get-ChildItem -Force -Recurse -Directory -Filter ".git" | Select-Object FullName
```

Result:

```text
C:\Users\xogns\Documents\testAuction\.git
C:\Users\xogns\Documents\testAuction\court_auction_platform\.git
C:\Users\xogns\Documents\testAuction\court_auction_platform_git_recovery_backup_20260706_182549\.git
```

### Parent path Git diagnostics

Command:

```powershell
git -C "C:\Users\xogns\Documents\testAuction" rev-parse --show-toplevel
git -C "C:\Users\xogns\Documents\testAuction" status --short
git -C "C:\Users\xogns\Documents\testAuction" branch --show-current
git -C "C:\Users\xogns\Documents\testAuction" remote -v
```

Result for all four commands:

```text
fatal: not a git repository (or any of the parent directories): .git
```

Observation:

- `C:\Users\xogns\Documents\testAuction\.git` exists as a directory but `Get-ChildItem -Force ".git"` returned no entries.
- The parent `.git` is not a valid Git repository in its current state.

### Project path Git diagnostics before rename

Command:

```powershell
git -C "C:\Users\xogns\Documents\testAuction\court_auction_platform" rev-parse --show-toplevel
git -C "C:\Users\xogns\Documents\testAuction\court_auction_platform" status --short
git -C "C:\Users\xogns\Documents\testAuction\court_auction_platform" branch --show-current
git -C "C:\Users\xogns\Documents\testAuction\court_auction_platform" remote -v
```

Result:

```text
C:/Users/xogns/Documents/testAuction/court_auction_platform
```

`status --short` showed all project files as untracked, including top-level source directories and `storage/`:

```text
?? .gitignore
?? AGENTS.md
?? PROJECT_BRIEF.md
?? PROJECT_CONTEXT.md
?? backend/
?? docs/
?? frontend/
?? main_app.py
?? orchestrator.py
?? reports/
?? requirements.txt
?? run_onbid_scheduled_sync.ps1
?? run_onbid_sync.ps1
?? runtime_settings.json
?? storage/
?? tests/
```

Branch:

```text
codex/devpack-v002-onbid-observability
```

Remote:

```text
<no output>
```

Additional check:

```text
fatal: your current branch 'codex/devpack-v002-onbid-observability' does not have any commits yet
```

Observation:

- The internal repository at `court_auction_platform\.git` was an empty newly initialized repository.
- It had no commits, no remote, and no tracked files.
- This matches the v002 report note that existing files appeared as untracked after a new repository was initialized inside the project folder.

## Backup directory diagnostics

Candidate:

```text
C:\Users\xogns\Documents\testAuction\court_auction_platform_git_recovery_backup_20260706_182549
```

Using command-local `safe.directory` only, because Git reported dubious ownership for this backup path:

```powershell
git -c safe.directory="C:/Users/xogns/Documents/testAuction/court_auction_platform_git_recovery_backup_20260706_182549" -C "C:\Users\xogns\Documents\testAuction\court_auction_platform_git_recovery_backup_20260706_182549" rev-parse --show-toplevel
git -c safe.directory="C:/Users/xogns/Documents/testAuction/court_auction_platform_git_recovery_backup_20260706_182549" -C "C:\Users\xogns\Documents\testAuction\court_auction_platform_git_recovery_backup_20260706_182549" status --short
git -c safe.directory="C:/Users/xogns/Documents/testAuction/court_auction_platform_git_recovery_backup_20260706_182549" -C "C:\Users\xogns\Documents\testAuction\court_auction_platform_git_recovery_backup_20260706_182549" branch --show-current
git -c safe.directory="C:/Users/xogns/Documents/testAuction/court_auction_platform_git_recovery_backup_20260706_182549" -C "C:\Users\xogns\Documents\testAuction\court_auction_platform_git_recovery_backup_20260706_182549" log --oneline --decorate --max-count=10
```

Result:

```text
C:/Users/xogns/Documents/testAuction/court_auction_platform_git_recovery_backup_20260706_182549
```

The backup directory also showed all files as untracked, branch `codex/devpack-v002-onbid-observability`, no remote, and:

```text
fatal: your current branch 'codex/devpack-v002-onbid-observability' does not have any commits yet
```

Object/refs check:

- `.git\objects` contained only `info` and `pack` directories.
- `.git\refs` contained only empty `heads` and `tags` directories.
- `.git\HEAD` was `ref: refs/heads/codex/devpack-v002-onbid-observability`.

Observation:

- The backup candidate is not the original Git repository.
- It appears to be another copy of the same empty initialized repository state.

## Nearby repository search

Additional read-only checks were run against `C:\Users\xogns\Documents`:

```powershell
git -C "C:\Users\xogns\Documents" rev-parse --show-toplevel
Get-ChildItem -Force -Directory "C:\Users\xogns\Documents" -Recurse -Filter ".git" -ErrorAction SilentlyContinue
```

Results:

```text
fatal: not a git repository (or any of the parent directories): .git
```

Only these `.git` directories were found under `Documents`:

```text
C:\Users\xogns\Documents\testAuction\.git
C:\Users\xogns\Documents\testAuction\court_auction_platform\.git
C:\Users\xogns\Documents\testAuction\court_auction_platform_git_recovery_backup_20260706_182549\.git
```

Observation:

- No valid original Git root was found in the accessible nearby directory tree.

## Recovery action performed

The bad internal Git metadata was renamed, not deleted:

```text
From: C:\Users\xogns\Documents\testAuction\court_auction_platform\.git
To:   C:\Users\xogns\Documents\testAuction\court_auction_platform\.git.bad-init-v002-20260706_182549
```

Command used:

```powershell
Move-Item -LiteralPath "C:\Users\xogns\Documents\testAuction\court_auction_platform\.git" -Destination "C:\Users\xogns\Documents\testAuction\court_auction_platform\.git.bad-init-v002-20260706_182549"
```

Post-rename `.git` directories:

```text
C:\Users\xogns\Documents\testAuction\.git
C:\Users\xogns\Documents\testAuction\court_auction_platform_git_recovery_backup_20260706_182549\.git
```

Post-rename project Git check:

```text
fatal: not a git repository (or any of the parent directories): .git
```

Observation:

- Renaming the bad internal `.git` did not reveal a valid parent repository.
- The parent `.git` remains invalid.

## Follow-up action: parent invalid `.git` renamed

The invalid parent Git metadata was also renamed, not deleted:

```text
From: C:\Users\xogns\Documents\testAuction\.git
To:   C:\Users\xogns\Documents\testAuction\.git.empty-invalid-v002-20260706
```

Command used:

```powershell
Rename-Item -LiteralPath ".git" -NewName ".git.empty-invalid-v002-20260706"
```

Verification:

```text
C:\Users\xogns\Documents\testAuction\.git.empty-invalid-v002-20260706
C:\Users\xogns\Documents\testAuction\court_auction_platform\.git.bad-init-v002-20260706_182549
```

Post-action project Git check:

```text
fatal: not a git repository (or any of the parent directories): .git
```

## v002 change candidates

The v002 report identifies these intended code/document/test changes:

```text
backend/database/models.py
backend/database/session.py
backend/onbid/client.py
backend/workers/onbid_sync.py
backend/services/auction_items.py
backend/services/onbid_observability.py
backend/web/routers/admin_operations.py
backend/web/routers/auctions.py
frontend/templates/admin/collection.html
run_onbid_sync.ps1
run_onbid_scheduled_sync.ps1
docs/onbid_scheduled_sync_runbook.md
docs/onbid_notice_persistence_design.md
docs/migration_ledger.md
tests/onbid_module_test.py
tests/page_response_smoke_test.py
tests/router_boundary_test.py
reports/codex-devpack-v002-report.md
reports/project-result_v002.md
reports/git-recovery-v002-report.md
```

These are candidates only. Because the original Git history is unavailable, Git cannot distinguish v002 edits from pre-existing tracked files.

## Commit status

Not performed:

- Branch creation in the original repository.
- Staging.
- Commit.

Reason:

- No valid original Git repository was found.
- The only repository that initially worked was the bad internal empty repository.
- Committing there would preserve files in a newly initialized repository, but it would not satisfy the requirement to commit against the original Git repository.

## Current state

- v002 working files remain in `C:\Users\xogns\Documents\testAuction\court_auction_platform`.
- The bad internal `.git` is preserved as `.git.bad-init-v002-20260706_182549`.
- The parent `.git` at `C:\Users\xogns\Documents\testAuction\.git` still exists but is invalid/empty.
- No valid original Git root is currently available from the checked paths.
- v003 should not start until a valid original repository is restored or explicitly selected.

## Required next recovery input

To complete the original objective, one of the following is needed:

1. Provide the path to the actual original repository root or its intact `.git` directory.
2. Restore the original `.git` metadata for `court_auction_platform` or `testAuction` from backup.
3. Provide permission to use a remote origin or archived repository copy as the original baseline.

After that, the safe continuation should be:

```text
1. Verify original root with git rev-parse --show-toplevel.
2. Create/switch to codex/devpack-v002-onbid-observability from the original baseline.
3. Stage only the v002 candidate files listed above, excluding .env, *.db, storage/, storage/logs/, logs, caches, and raw documents.
4. Commit v002 recovery changes.
5. Re-run git status and update this report with the final commit hash.
```
