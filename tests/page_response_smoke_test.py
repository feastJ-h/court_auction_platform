from __future__ import annotations

import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

TEST_DB_PATH = PROJECT_ROOT / "storage" / "test" / "page_response_smoke_test.db"
TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

os.environ["DB_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["APP_SECRET_KEY"] = "page-smoke-test-secret"

from fastapi.testclient import TestClient  # noqa: E402

from backend.database.models import RawDocument  # noqa: E402
from backend.database.session import init_db, session_scope  # noqa: E402
from main_app import app  # noqa: E402


def seed_raw_document() -> int:
    raw_file = PROJECT_ROOT / "storage" / "test" / "page_smoke_raw.txt"
    raw_file.write_text("page smoke raw document", encoding="utf-8")
    with session_scope() as session:
        document = RawDocument(
            file_path=str(raw_file),
            source_url="isolated://page-smoke",
            file_hash="page-smoke-raw-hash",
        )
        session.add(document)
        session.flush()
        return document.id


def login_admin(client: TestClient):
    response = client.post(
        "/login",
        data={"username": "admin", "password": "admin1234!", "next_url": "/admin"},
        follow_redirects=False,
    )
    assert response.status_code in (302, 303), response.status_code
    return response.cookies


def main() -> int:
    init_db()
    raw_doc_id = seed_raw_document()
    unauth_client = TestClient(app)
    unauth_document = unauth_client.get(f"/documents/raw/{raw_doc_id}")
    assert unauth_document.status_code == 401, unauth_document.status_code

    client = TestClient(app)
    cookies = login_admin(client)

    public_page = client.get("/login")
    assert public_page.status_code == 200, public_page.status_code

    protected_pages = (
        "/user",
        "/admin",
        "/admin/assets",
        "/admin/analysis",
        "/admin/collection",
        "/admin/reviews",
        "/admin/users",
        "/auctions",
    )
    for path in protected_pages:
        response = client.get(path, cookies=cookies)
        assert response.status_code == 200, f"{path}: {response.status_code}"

    for path in (
        "/api/local-analysis/status",
        "/api/admin/collection-quality",
        "/api/admin/onbid-quality",
        "/api/admin/ocr/status",
    ):
        response = client.get(path, cookies=cookies)
        assert response.status_code == 200, f"{path}: {response.status_code} {response.text}"

    raw_document = client.get(f"/documents/raw/{raw_doc_id}", cookies=cookies)
    assert raw_document.status_code == 200, raw_document.status_code
    assert b"page smoke raw document" in raw_document.content

    print(f"isolated_db={TEST_DB_PATH}")
    print("PASS - page response smoke test")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
