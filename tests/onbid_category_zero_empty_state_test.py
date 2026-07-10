from tests._v010_contracts import source


def test_national_property_has_truthful_empty_state():
    page = source("frontend/templates/auctions/index.html")
    assert "현재 공개 가능한 국유일반재산 항목이 없습니다" in page
    assert "오래되거나 확인되지 않은 자료를 대신 노출하지 않습니다" in page
