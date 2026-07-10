from urllib.parse import parse_qs, urlsplit

import pytest

from backend.web.pagination import build_pagination


FILTERS = {
    "region": "서울", "category": "real_estate", "data_quality": "needs_confirmation",
    "price_min": 1, "price_max": 100000000, "closing_within_days": 7, "sort": "price_asc",
    "q": "테스트", "status": "입찰중", "agency": "기관", "usage": "토지",
    "has_notice": "yes", "has_detail": "no",
}


@pytest.mark.parametrize("key", list(FILTERS))
def test_next_page_preserves_each_supported_filter(key):
    model = build_pagination("/onbid", current_page=2, total_pages=10, query_state=FILTERS)
    query = parse_qs(urlsplit(str(model["next_href"])).query)
    assert query[key] == [str(FILTERS[key])]
    assert query["page"] == ["3"]
