from tests._v010_contracts import source


def test_cases_uses_same_pagination_partial():
    assert 'shared/pagination.html' in source("frontend/templates/cases/index.html")
    assert "build_pagination(" in source("backend/web/routers/cases.py")
