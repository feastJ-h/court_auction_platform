from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

TEST_DB_PATH = PROJECT_ROOT / "storage" / "test" / "sitemap_fresh_public_routes_test.db"
TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

os.environ["DB_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["APP_SECRET_KEY"] = "sitemap-fresh-test-secret"

from fastapi.testclient import TestClient  # noqa: E402

from backend.database.models import AuctionItem  # noqa: E402
from backend.database.session import init_db, session_scope  # noqa: E402
from main_app import app  # noqa: E402


def main() -> int:
    init_db()
    with session_scope() as session:
        fresh = AuctionItem(source="ONBID", cltr_mng_no="SITEMAP-FRESH", pbct_cdtn_no="1", item_name="Sitemap fresh", asset_type="Real estate", bid_start_at="2025-03-01")
        stale = AuctionItem(source="ONBID", cltr_mng_no="SITEMAP-STALE", pbct_cdtn_no="1", item_name="Sitemap stale", asset_type="Real estate", bid_start_at="2024-12-31")
        unknown = AuctionItem(source="ONBID", cltr_mng_no="SITEMAP-UNKNOWN", pbct_cdtn_no="1", item_name="Sitemap unknown", asset_type="Real estate")
        session.add_all([fresh, stale, unknown])
        session.flush()
        fresh_id, stale_id, unknown_id = fresh.id, stale.id, unknown.id

    sitemap = TestClient(app).get("/sitemap.xml")
    assert sitemap.status_code == 200, sitemap.status_code
    assert f"/onbid/{fresh_id}" in sitemap.text, sitemap.text
    assert f"/onbid/{stale_id}" not in sitemap.text, sitemap.text
    assert f"/onbid/{unknown_id}" not in sitemap.text, sitemap.text

    print(f"isolated_db={TEST_DB_PATH}")
    print("PASS - sitemap includes only fresh public ONBID items")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
