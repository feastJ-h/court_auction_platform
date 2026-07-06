# OCR, Documents, and Page Smoke Sprint Report

## 1. Summary
- Added `backend/web/routers/ocr_operations.py`.
- Moved OCR admin APIs out of `main_app.py`:
  - `POST /api/admin/events/{event_id}/ocr/jobs`
  - `POST /api/admin/ocr/enqueue`
  - `GET /api/admin/ocr/status`
- Added `backend/web/routers/documents.py`.
- Moved raw document serving out of `main_app.py`:
  - `GET /documents/raw/{raw_doc_id}`
- Moved `GET /api/admin/collection-quality` into `backend/web/routers/admin_operations.py`.
- Added `tests/page_response_smoke_test.py`.
- Extended `tests/router_boundary_test.py` for OCR, document, and collection-quality routes.

## 2. Security & Edge Cases
- OCR APIs remain admin-only.
- Raw document serving now requires an authenticated user.
- Raw document paths are resolved under `PROJECT_ROOT` using `Path.relative_to`, blocking path escape.
- Missing raw files and missing DB rows return controlled 404 responses.
- Page smoke test verifies unauthenticated raw document access returns 401.

## 3. Test Results
- `py_compile main_app.py backend/web/routers/ocr_operations.py backend/web/routers/documents.py backend/web/routers/admin_operations.py tests/router_boundary_test.py tests/page_response_smoke_test.py`: Pass
- `tests/router_boundary_test.py`: Pass
- `tests/page_response_smoke_test.py`: Pass
- `tests/onbid_module_test.py`: Pass
- `tests/isolated_operations_test.py`: Pass

## 4. Notes
- FastAPI TestClient still emits a Starlette `httpx` deprecation warning. It does not block current tests.
- The next sensible cleanup target is account/settings routes and admin metadata correction routes.
