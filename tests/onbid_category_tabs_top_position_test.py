from tests._v010_contracts import source


def test_category_tabs_render_before_filter_controls():
    template = source("frontend/templates/auctions/index.html")
    assert template.index('shared/onbid_category_tabs.html') < template.index('data-compact-filter="true"')
