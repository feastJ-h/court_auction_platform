from __future__ import annotations

from datetime import date, timedelta

from _v007_helpers import configure_test_env

TEST_DB_PATH = configure_test_env("onbid_closing_within_days_active_only_test")

from backend.database.models import AuctionItem  # noqa: E402
from backend.database.session import init_db, session_scope  # noqa: E402
from backend.services.auction_items import list_auction_items  # noqa: E402


def main() -> int:
    init_db()
    today = date.today()
    with session_scope() as session:
        session.add_all([
            AuctionItem(source="ONBID", cltr_mng_no="CLOSED", pbct_cdtn_no="1", item_name="closed", bid_end_at=(today - timedelta(days=1)).isoformat(), freshness_date=today.isoformat(), freshness_status="fresh", public_visible=True),
            AuctionItem(source="ONBID", cltr_mng_no="SOON", pbct_cdtn_no="1", item_name="soon", bid_end_at=(today + timedelta(days=3)).isoformat(), freshness_date=today.isoformat(), freshness_status="fresh", public_visible=True),
            AuctionItem(source="ONBID", cltr_mng_no="LATER", pbct_cdtn_no="1", item_name="later", bid_end_at=(today + timedelta(days=8)).isoformat(), freshness_date=today.isoformat(), freshness_status="fresh", public_visible=True),
        ])
    with session_scope() as session:
        items = list_auction_items(session, public_only=True, closing_within_days=7, limit=20)
        item_names = [item.item_name for item in items]
    assert item_names == ["soon"]
    print(f"isolated_db={TEST_DB_PATH}")
    print("PASS - closing filter active only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
