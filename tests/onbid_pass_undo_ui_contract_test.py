from tests._v010_contracts import source


def test_list_exposes_pass_forms_and_review_cards():
    page = source("frontend/templates/auctions/index.html")
    assert 'data-preference-form="passed"' in page and 'data-review-card="true"' in page


def test_undo_toast_is_polite_and_lasts_five_seconds():
    toast = source("frontend/templates/shared/toast.html")
    script = source("frontend/static/beta.js")
    assert 'aria-live="polite"' in toast and "5000" in script and "실행 취소" in toast


def test_failed_request_restores_card():
    script = source("frontend/static/beta.js")
    assert "card.hidden = false" in script and "저장하지 못했습니다" in script
