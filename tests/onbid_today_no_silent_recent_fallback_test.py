from datetime import date

from backend.services.onbid_review import build_today_review_state
from tests._v010_contracts import source


def test_no_today_items_does_not_return_recent_items():
    old = {"first_seen_date": "2026-07-09", "preference": {}}
    result = build_today_review_state([old], today=date(2026, 7, 10))
    assert result["items"] == [] and result["has_today_items"] is False
    assert "최근 수집 항목 보기" in source("frontend/templates/auctions/today.html")
