from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from _v007_helpers import configure_test_env

configure_test_env("onbid_deadline_status_kst_test")

from backend.services.auction_items import get_onbid_deadline_status


def main() -> int:
    now = datetime(2026, 7, 10, 12, 0, tzinfo=ZoneInfo("Asia/Seoul"))
    assert get_onbid_deadline_status("2026-07-09", now=now)["label"] == "입찰마감"
    assert get_onbid_deadline_status("2026-07-10", now=now)["label"] == "오늘 마감"
    assert get_onbid_deadline_status("2026-07-13", now=now)["label"] == "D-3"
    assert get_onbid_deadline_status("2026-07-20", now=now)["state"] == "normal"
    assert get_onbid_deadline_status("", now=now)["state"] == "unknown"
    assert get_onbid_deadline_status("2026-07-10 00:01", now=now)["state"] == "closed"
    print("PASS - KST deadline status")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
