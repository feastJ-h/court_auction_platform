# Sprint 5 - Shared Web Dependencies & Router Smoke Report

## 1. Summary
- Added `backend/web/dependencies.py`.
- Centralized shared web route type aliases and common helpers:
  - `RequireUser`
  - `RequireAdmin`
  - `LoginRedirect`
  - metadata attachment callable types
  - `admin_login_required`
  - `safe_redirect_target`
- Updated route modules to use shared dependency types.
- Enhanced `tests/router_boundary_test.py` to verify router registrar functions are importable and callable.
- Updated `docs/service_boundary_refactoring_plan.md` with the current router separation state.

## 2. Security & Edge Cases
- Admin-only routes continue to return controlled 401 errors.
- Route smoke tests now guard against missing router registration functions.
- No API keys or PII are emitted in reports.

## 3. Test Results
- `py_compile main_app.py backend/web/dependencies.py backend/web/routers/*.py tests/router_boundary_test.py`: Pass
- `tests/router_boundary_test.py`: Pass
- `tests/onbid_module_test.py`: Pass
- `tests/isolated_operations_test.py`: Pass
- Local server restart: Pass
- Local route response check:
  - `/login`: 200
  - `/user`: 303 login redirect
  - `/admin`: 303 login redirect
  - `/auctions`: 303 login redirect
  - `/api/local-analysis/status`: 200

## 4. ONBID Real API Status
- Activated key was verified with real sync.
- Latest real sync: `SUCCEEDED`, `fetched=5`, `inserted=0`, `duplicates=5`.
- Stored public auction item count: `8`.

## 5. Next Recommended Sprint
1. Move OCR admin APIs into `backend/web/routers/ocr_operations.py`.
2. Move raw document serving into `backend/web/routers/documents.py`.
3. Move collection-quality API into `admin_operations.py`.
4. Add page response smoke tests for `/admin`, `/user`, `/auctions`.
5. Add a migration ledger for SQLite schema changes.
