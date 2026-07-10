from tests._v010_contracts import source


def test_category_has_tabs_and_no_select_control():
    template = source("frontend/templates/auctions/index.html")
    tabs = source("frontend/templates/shared/onbid_category_tabs.html")
    assert template.count('shared/onbid_category_tabs.html') == 1
    assert 'name="category"' not in template.replace('<input type="hidden" name="category"', "")
    assert 'data-onbid-category-tabs="true"' in tabs
