# Service Boundary Refactoring Plan

## Purpose
This document keeps the project maintainable as it grows into a commercial-grade service. Each feature area should have a clear ownership boundary so future fixes, security work, or UI changes can be made in the smallest possible place.

## Domain Boundaries

### 1. Recovery / Bankruptcy Cases
- User-facing case list and detail UI stay in `frontend/templates/user`.
- Case metadata correction and review flows stay in `main_app.py` until they are extracted to `backend/web/routers/cases.py`.
- Database reads and writes should use `backend/database/crud.py` or a dedicated case repository.
- Raw court text must remain stored locally and exposed only through authenticated routes.

### 2. Public Auction / ONBID
- ONBID collection and public auction screens are owned by `backend/web/routers/auctions.py`.
- ONBID API client logic stays in `backend/onbid/client.py`.
- ONBID sync orchestration stays in `backend/workers/onbid_sync.py`.
- Auction persistence and matching logic stay in `backend/services/auction_items.py`.
- UI templates stay in `frontend/templates/auctions`.

### 3. Admin Operations
- Admin dashboards, users, collection status, worker status, and review queues stay under `frontend/templates/admin`.
- Audit records should be written with `backend/services/audit_logs.py`.
- Admin-only APIs must call `require_admin` before doing work.
- New admin sections should avoid mixing domain business logic into templates.

### 4. Analysis
- Basic and deep analysis provider logic stays in `backend/ai_engine`.
- Analysis result persistence stays in `backend/database/analysis_results.py`.
- Review/approval workflows stay in `backend/services/analysis_reviews.py`.
- Provider-specific prompts and throttling rules must not leak into UI handlers.

### 5. Collection / Parsing / OCR
- Court crawling stays in `backend/crawler`.
- Text extraction and PII masking stay in `backend/parser`.
- OCR job orchestration stays in `backend/jobs`.
- Processed files should move away from raw quarantine once text is extracted, so files are not repeatedly requested.

## Current Refactor Step
- Extracted public auction web routes and ONBID admin APIs from `main_app.py` into `backend/web/routers/auctions.py`.
- Extracted admin user-management routes from `main_app.py` into `backend/web/routers/admin_users.py`.
- Extracted admin dashboard/collection/review pages into `backend/web/routers/admin_operations.py`.
- Extracted recovery/bankruptcy user routes into `backend/web/routers/cases.py`.
- Extracted analysis and analysis-job APIs into `backend/web/routers/analysis.py`.
- Extracted OCR operation APIs into `backend/web/routers/ocr_operations.py`.
- Extracted raw document serving into `backend/web/routers/documents.py`.
- Moved collection-quality API into `backend/web/routers/admin_operations.py`.
- Added shared route dependency types and helpers in `backend/web/dependencies.py`.
- Kept `main_app.py` responsible for app creation, authentication helpers, and legacy routes that are not yet extracted.
- Preserved the existing UI and test behavior.

## Next Refactor Queue
1. Add response-level smoke tests for individual admin forms and mutation APIs.
2. Move account/password and user settings routes into an account router.
3. Move admin event metadata correction into an admin operations or case moderation router.
4. Add Alembic-style migration history or a project migration ledger for SQLite schema changes.
5. Normalize Korean text encoding in legacy sample/test display strings.

## Change Rule
When adding or changing a feature:
- Public auction or ONBID: start in `backend/web/routers/auctions.py`, then service/client files.
- Analysis: start in `backend/ai_engine` and `backend/web/routers/analysis.py` after extraction.
- Admin visibility/operations: start in `backend/web/routers/admin.py` after extraction.
- Recovery/bankruptcy case UI: start in `backend/web/routers/cases.py` after extraction.
