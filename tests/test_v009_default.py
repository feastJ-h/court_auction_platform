from datetime import datetime
from zoneinfo import ZoneInfo

from backend.services.auction_items import get_onbid_deadline_status


def test_kst_deadline_status_never_uses_d_plus_label() -> None:
    now = datetime(2026, 7, 10, 12, 0, tzinfo=ZoneInfo("Asia/Seoul"))
    result = get_onbid_deadline_status("2026-07-09", now=now)
    assert result["state"] == "closed"
    assert result["label"] == "입찰마감"
    assert "D+" not in result["label"]


def test_date_only_deadline_uses_end_of_kst_day() -> None:
    now = datetime(2026, 7, 10, 12, 0, tzinfo=ZoneInfo("Asia/Seoul"))
    result = get_onbid_deadline_status("2026-07-10", now=now)
    assert result["is_active"] is True
    assert result["label"] == "오늘 마감"
