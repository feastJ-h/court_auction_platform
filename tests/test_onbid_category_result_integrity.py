import re

from fastapi.testclient import TestClient

from main_app import app


def test_each_category_route_only_renders_matching_cards():
    client = TestClient(app)
    for category in ("real_estate", "movable", "national_property"):
        response = client.get(f"/onbid?category={category}&sort=closing_soon")
        assert response.status_code == 200
        assert f'data-active-category="{category}"' in response.text
        rendered = re.findall(r'data-item-category="([^"]+)"', response.text)
        assert all(value == category for value in rendered)
        if not rendered:
            assert 'data-empty-state="true"' in response.text


def test_all_route_is_canonical_and_active():
    response = TestClient(app).get("/onbid?sort=closing_soon")
    assert response.status_code == 200
    assert 'data-active-category="all"' in response.text
