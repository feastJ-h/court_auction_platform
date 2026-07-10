from urllib.parse import parse_qs, urlsplit

from backend.web.routers.auctions import build_category_links


def test_category_tab_preserves_non_category_filters_and_resets_page():
    filters = {"category": "all", "region": "서울", "price_max": 100000000, "data_quality": "needs_confirmation", "sort": "price_asc", "page": 9}
    link = next(item for item in build_category_links("/onbid", filters, {"real_estate": 3}) if item["value"] == "real_estate")
    query = parse_qs(urlsplit(str(link["href"])).query)
    assert query["region"] == ["서울"]
    assert query["price_max"] == ["100000000"]
    assert query["data_quality"] == ["needs_confirmation"]
    assert query["sort"] == ["price_asc"]
    assert query["category"] == ["real_estate"]
    assert "page" not in query


def test_all_category_omits_category_query():
    filters = {"category": "movable", "sort": "closing_soon", "page": 3}
    link = next(item for item in build_category_links("/onbid", filters, {"all": 3}) if item["value"] == "all")
    query = parse_qs(urlsplit(str(link["href"])).query)
    assert query == {"sort": ["closing_soon"]}


def test_zero_count_primary_category_is_still_available():
    links = build_category_links("/onbid", {"category": "all"}, {"national_property": 0})
    assert any(item["value"] == "national_property" for item in links)
