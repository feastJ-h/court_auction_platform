from __future__ import annotations

import os
import sys
from pathlib import Path
import re
from urllib.parse import parse_qs, urlparse

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

TEST_DB_PATH = PROJECT_ROOT / "storage" / "test" / "onbid_public_filter_state_test.db"
TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

os.environ["DB_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["APP_SECRET_KEY"] = "filter-state-test-secret"

from fastapi.testclient import TestClient  # noqa: E402

from backend.config import get_settings  # noqa: E402
from backend.database.models import AuctionItem  # noqa: E402
from backend.database.session import init_db, session_scope  # noqa: E402
from main_app import app  # noqa: E402


def parse_links(text: str) -> list[str]:
    return re.findall(r'href="([^"]+)"', text)


def assert_clean_public_links(links: list[str]) -> None:
    for link in links:
        if not link.startswith("/onbid") or link.startswith("/onbid/"):
            continue
        query = parse_qs(urlparse(link).query, keep_blank_values=True)
        for key in ("region", "price_min", "price_max", "category"):
            if key in query:
                assert all(value != "" for value in query.get(key, [])), f"empty {key} in {link}"
        assert query.get("category") is None or "all" not in query.get("category", []), f"all category leaked: {link}"


def main() -> int:
    init_db()
    with session_scope() as session:
        session.add(
            AuctionItem(
                source="ONBID",
                cltr_mng_no="FILTER-REAL",
                pbct_cdtn_no="1",
                item_name="Filter real item",
                asset_type="Real estate",
                address="Seoul",
                bid_start_at="2025-04-01",
                bid_end_at="2025-04-10",
                minimum_bid_price=90000000,
            )
        )
        session.add(
            AuctionItem(
                source="ONBID",
                cltr_mng_no="ONBID-REAL-202607-SAMPLE",
                pbct_cdtn_no="S",
                item_name="Fixture sample item",
                asset_type="Real estate",
                address="Seoul sample",
                bid_start_at="2025-04-01",
                bid_end_at="2025-04-10",
                minimum_bid_price=90000000,
                raw_payload='{"fixture":"sample"}',
            )
        )

    client = TestClient(app)
    response = client.get("/onbid?category=movable&region=NoSuchRegion&price_max=100000000")
    assert response.status_code == 200, response.status_code
    assert 'data-active-section="onbid"' in response.text
    assert 'data-active-category="movable"' in response.text
    assert 'data-filter-chips="true"' in response.text
    assert 'data-onbid-category-tabs="true"' in response.text
    assert 'data-category-tab="movable"' in response.text
    assert 'aria-current="page"' in response.text
    assert 'data-empty-state="true"' in response.text or "검색 결과가 없습니다" in response.text

    assert_clean_public_links(parse_links(response.text))

    empty_filter_urls = [
        "/onbid?category=real_estate&price_min=&price_max=&region=",
        "/onbid?price_min=&price_max=&region=&category=all",
        "/onbid?region=&price_min=&price_max=",
    ]
    for url in empty_filter_urls:
        empty_response = client.get(url)
        assert empty_response.status_code == 200, f"{url}: {empty_response.status_code}"
        assert_clean_public_links(parse_links(empty_response.text))

    reset = client.get("/onbid")
    assert "Filter real item" in reset.text
    assert "Fixture sample item" not in reset.text

    assert re.search(r">\s*All\s*<", response.text) is None
    banned_phrases = (
        "ONBID Public Auction",
        "Recovery and Bankruptcy Notices",
        "Reset",
        "AI 분류 있음",
        "AI 분석 있음",
        "Real estate",
        "Movable",
        "National property",
        "Other",
    )
    for phrase in banned_phrases:
        assert phrase not in response.text, f"found english phrase on /onbid: {phrase}"

    os.environ["REVIEW_SHOW_SAMPLE"] = "true"
    get_settings.cache_clear()
    show_sample = client.get("/onbid")
    assert "Fixture sample item" in show_sample.text
    os.environ.pop("REVIEW_SHOW_SAMPLE", None)
    get_settings.cache_clear()

    print(f"isolated_db={TEST_DB_PATH}")
    print("PASS - ONBID public filter state")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
