from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

TEST_DB_PATH = PROJECT_ROOT / "storage" / "test" / "public_route_visual_smoke_test.db"
TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

os.environ["DB_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["APP_SECRET_KEY"] = "public-visual-smoke-test-secret"

from fastapi.testclient import TestClient  # noqa: E402

from backend.database.models import Asset, AssetEvent, AuctionItem, RawDocument  # noqa: E402
from backend.database.session import init_db, session_scope  # noqa: E402
from main_app import app  # noqa: E402


def main() -> int:
    init_db()
    with session_scope() as session:
        auction = AuctionItem(source="ONBID", cltr_mng_no="VISUAL-FRESH", pbct_cdtn_no="1", item_name="Visual fresh item", asset_type="Real estate", bid_start_at="2025-02-01")
        raw = RawDocument(file_path="storage/test/visual.txt", source_url="https://example.test/visual", file_hash="visual-hash")
        asset = Asset(main_category="부동산", sub_category="office", address="Seoul")
        session.add_all([auction, raw, asset])
        session.flush()
        event = AssetEvent(asset_id=asset.id, raw_doc_id=raw.id, case_number="VISUAL-CASE", status="OPEN", title="Visual case", url="https://example.test/case", notice_date="2026-07-01", expire_date="2026-08-01", parse_status="TEXT_PARSED", extracted_text="internal")
        session.add(event)
        session.flush()
        auction_id, event_id = auction.id, event.id

    client = TestClient(app)
    paths = ["/", "/onbid", f"/onbid/{auction_id}", "/cases", f"/cases/{event_id}", "/about", "/privacy", "/terms", "/disclaimer"]
    for path in paths:
        response = client.get(path)
        assert response.status_code == 200, f"{path}: {response.status_code}"
        assert "<html" in response.text.lower(), path
        assert 'data-active-section="' in response.text, path
        assert "Traceback" not in response.text, path

    print(f"isolated_db={TEST_DB_PATH}")
    print("PASS - public route HTML smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
