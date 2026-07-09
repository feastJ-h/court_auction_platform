from __future__ import annotations

from datetime import date, timedelta

from _v007_helpers import configure_test_env

TEST_DB_PATH = configure_test_env("onbid_default_active_priority_test")

from fastapi.testclient import TestClient  # noqa: E402

from backend.database.models import AuctionItem  # noqa: E402
from backend.database.session import init_db, session_scope  # noqa: E402
from main_app import app  # noqa: E402


def main() -> int:
    init_db()
    past = (date.today() - timedelta(days=10)).isoformat()
    future = (date.today() + timedelta(days=5)).isoformat()
    with session_scope() as session:
        session.add_all(
            [
                AuctionItem(source="ONBID", cltr_mng_no="V008-ENDED", pbct_cdtn_no="1", item_name="Ended item", asset_type="Real estate", bid_start_at=past, bid_end_at=past, public_category="real_estate", freshness_date=future, freshness_status="fresh", public_visible=True),
                AuctionItem(source="ONBID", cltr_mng_no="V008-ACTIVE", pbct_cdtn_no="1", item_name="Active item", asset_type="Real estate", bid_start_at=date.today().isoformat(), bid_end_at=future, public_category="real_estate", freshness_date=future, freshness_status="fresh", public_visible=True),
            ]
        )
    page = TestClient(app).get("/onbid")
    assert page.status_code == 200, page.status_code
    assert page.text.index("Active item") < page.text.index("Ended item")
    print(f"isolated_db={TEST_DB_PATH}")
    print("PASS - default active priority")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
