from __future__ import annotations

import os
import sys
from pathlib import Path
from datetime import date, timedelta

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

TEST_DB_PATH = PROJECT_ROOT / "storage" / "test" / "onbid_freshness_policy_test.db"
TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

os.environ["DB_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["APP_SECRET_KEY"] = "freshness-policy-test-secret"
os.environ["ONBID_MIN_PUBLIC_DATE"] = "2025-01-01"

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

from backend.database.models import AuctionItem  # noqa: E402
from backend.database.session import init_db, session_scope  # noqa: E402
from backend.services.auction_items import audit_onbid_freshness, repair_onbid_derived_fields, serialize_auction_item  # noqa: E402
from backend.workers.onbid_sync import filter_fresh_payloads  # noqa: E402
from main_app import app  # noqa: E402


def seed_items() -> None:
    future_355557 = (date.today() + timedelta(days=355557)).isoformat()
    with session_scope() as session:
        session.add_all(
            [
                AuctionItem(
                    source="ONBID",
                    cltr_mng_no="FRESH-2025",
                    pbct_cdtn_no="A",
                    item_name="Fresh public item",
                    asset_type="Real estate",
                    public_category="real_estate",
                    bid_start_at="2025-01-01",
                    bid_end_at="2025-01-10",
                    minimum_bid_price=100,
                ),
                AuctionItem(
                    source="ONBID",
                    cltr_mng_no="STALE-2003",
                    pbct_cdtn_no="B",
                    item_name="Stale hidden item",
                    asset_type="Real estate",
                    public_category="real_estate",
                    bid_start_at="2003-01-01",
                    bid_end_at="2003-01-10",
                    minimum_bid_price=100,
                ),
                AuctionItem(
                    source="ONBID",
                    cltr_mng_no="UNKNOWN-DATE",
                    pbct_cdtn_no="C",
                    item_name="Unknown date hidden item",
                    asset_type="Movable",
                    public_category="movable",
                    bid_start_at="UNKNOWN",
                    minimum_bid_price=100,
                ),
                AuctionItem(
                    source="ONBID",
                    cltr_mng_no="SENTINEL-2999",
                    pbct_cdtn_no="D",
                    item_name="Sentinel future hidden item",
                    asset_type="National property",
                    public_category="national_property",
                    bid_start_at="2999-12-30",
                    bid_end_at="2999-12-31",
                    minimum_bid_price=100,
                ),
                AuctionItem(
                    source="ONBID",
                    cltr_mng_no="SENTINEL-0001",
                    pbct_cdtn_no="E",
                    item_name="Sentinel ancient hidden item",
                    asset_type="Real estate",
                    public_category="real_estate",
                    bid_start_at="0001-01-01",
                    bid_end_at="0001-01-01",
                    minimum_bid_price=100,
                ),
                AuctionItem(
                    source="ONBID",
                    cltr_mng_no="SENTINEL-1900",
                    pbct_cdtn_no="F",
                    item_name="Sentinel historic hidden item",
                    asset_type="National property",
                    public_category="national_property",
                    bid_start_at="1900-01-01",
                    bid_end_at="1900-01-01",
                    minimum_bid_price=100,
                ),
                AuctionItem(
                    source="ONBID",
                    cltr_mng_no="SENTINEL-9999",
                    pbct_cdtn_no="G",
                    item_name="Sentinel max hidden item",
                    asset_type="Other",
                    public_category="other",
                    bid_start_at="9999-12-31",
                    bid_end_at="9999-12-31",
                    minimum_bid_price=100,
                ),
                AuctionItem(
                    source="ONBID",
                    cltr_mng_no="SENTINEL-355557",
                    pbct_cdtn_no="H",
                    item_name="Extreme future hidden item",
                    asset_type="Movable",
                    public_category="movable",
                    bid_start_at=future_355557,
                    bid_end_at=future_355557,
                    minimum_bid_price=100,
                ),
            ]
        )


def main() -> int:
    init_db()
    seed_items()
    client = TestClient(app)
    active_end = (date.today() + timedelta(days=30)).strftime("%Y%m%d")

    page = client.get("/onbid")
    assert page.status_code == 200, page.status_code
    assert "Fresh public item" in page.text
    assert "Stale hidden item" not in page.text
    assert "Unknown date hidden item" not in page.text
    assert "Sentinel future hidden item" not in page.text
    assert "Sentinel ancient hidden item" not in page.text
    assert "Sentinel historic hidden item" not in page.text
    assert "Sentinel max hidden item" not in page.text
    assert "Extreme future hidden item" not in page.text
    assert "D-355557" not in page.text

    with session_scope() as session:
        audit = audit_onbid_freshness(session, min_date="2025-01-01")
        assert audit["fresh"] == 1, audit
        assert audit["stale"] == 1, audit
        assert audit["unknown_date"] == 1, audit
        assert audit["invalid_date"] == 5, audit
        assert audit["by_category"]["real_estate"] == 3, audit
        assert audit["by_category"]["movable"] == 2, audit
        assert audit["by_category"]["national_property"] == 2, audit
        assert audit["by_category"]["other"] == 1, audit
        repair = repair_onbid_derived_fields(session, dry_run=True, min_date="2025-01-01")
        assert repair["would_update"] >= 6, repair
        sentinel = session.scalar(select(AuctionItem).where(AuctionItem.cltr_mng_no == "SENTINEL-2999"))
        view = serialize_auction_item(sentinel)
        assert view["d_day"]["label"] == "일정 확인 필요", view["d_day"]
        historic = session.scalar(select(AuctionItem).where(AuctionItem.cltr_mng_no == "SENTINEL-1900"))
        historic_view = serialize_auction_item(historic)
        assert historic_view["d_day"]["label"] == "일정 확인 필요", historic_view["d_day"]
        overflow = session.scalar(select(AuctionItem).where(AuctionItem.cltr_mng_no == "SENTINEL-355557"))
        overflow_view = serialize_auction_item(overflow)
        assert overflow_view["d_day"]["label"] == "일정 확인 필요", overflow_view["d_day"]

    accepted, summary = filter_fresh_payloads(
        [
            {"cltrMngNo": "API-FRESH", "pbctCdtnNo": "1", "bidStartAt": "20250101"},
            {"cltrMngNo": "API-STALE", "pbctCdtnNo": "2", "bidStartAt": "20241231"},
            {"cltrMngNo": "API-UNKNOWN", "pbctCdtnNo": "3"},
            {"cltrMngNo": "API-SENTINEL", "pbctCdtnNo": "4", "bidStartAt": "29991231"},
            {"cltrMngNo": "API-NATIONAL-FRESH", "pbctCdtnNo": "5", "FRST_BID_SLCTN_YMD": "20250102"},
            {"cltrMngNo": "API-NATIONAL-STALE", "pbctCdtnNo": "6", "FRST_BID_SLCTN_YMD": "20030711"},
            {"cltrMngNo": "API-ACTIVE-LONG", "pbctCdtnNo": "7", "bidStartAt": "20240101", "bidEndAt": active_end},
        ],
        min_date="2025-01-01",
    )
    assert [item["cltrMngNo"] for item in accepted] == ["API-FRESH", "API-NATIONAL-FRESH", "API-ACTIVE-LONG"]
    assert summary["accepted_fresh"] == 3, summary
    assert summary["dropped_stale"] == 2, summary
    assert summary["dropped_unknown_date"] == 2, summary

    print(f"isolated_db={TEST_DB_PATH}")
    print("PASS - ONBID freshness policy hides stale and unknown-date public rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
