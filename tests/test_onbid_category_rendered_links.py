import html
import re
from urllib.parse import parse_qs, urlsplit

from fastapi.testclient import TestClient

from main_app import app


def category_hrefs(markup: str) -> dict[str, str]:
    pairs = re.findall(r'data-category-tab="([^"]+)" href="([^"]+)"', markup)
    return {category: html.unescape(href) for category, href in pairs}


def test_rendered_category_anchors_replace_category_and_reset_page():
    response = TestClient(app).get(
        "/onbid?region=서울&price_max=100000000&data_quality=needs_confirmation&sort=price_asc&page=9"
    )
    assert response.status_code == 200
    hrefs = category_hrefs(response.text)
    assert set(hrefs) >= {"all", "real_estate", "movable", "national_property"}
    for category, href in hrefs.items():
        query = parse_qs(urlsplit(href).query)
        assert query["region"] == ["서울"]
        assert query["price_max"] == ["100000000"]
        assert query["data_quality"] == ["needs_confirmation"]
        assert query["sort"] == ["price_asc"]
        assert "page" not in query
        if category == "all":
            assert "category" not in query
        else:
            assert query["category"] == [category]
