# Sprint 3 - Recovery Case/User Router Report

## 1. Summary
- Added `backend/web/routers/cases.py`.
- Moved user recovery/bankruptcy routes out of `main_app.py`:
  - `/user`
  - `/user/passed`
  - `/user/bookmarks`
  - `/user/my`
  - `/user/watching`
  - `/user/watchlist`
  - user event pass/bookmark/watch/note actions
- Extended route boundary tests for the user routes.

## 2. Security & Edge Cases
- User pages and actions still require `require_user`.
- User actions still write audit logs.
- User event notes remain scoped by authenticated user ID.

## 3. Test Results
- `py_compile main_app.py backend/web/routers/cases.py tests/router_boundary_test.py`: Pass
- `tests/router_boundary_test.py`: Pass
- `tests/isolated_operations_test.py`: Pass

## 4. Next Step
- Extract analysis and analysis-job APIs into `backend/web/routers/analysis.py`.
