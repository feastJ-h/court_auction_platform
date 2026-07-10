import pytest

from backend.web.pagination import ELLIPSIS, pagination_window


@pytest.mark.parametrize(
    ("current", "total", "expected"),
    [
        (1, 54, [1, 2, 3, ELLIPSIS, 54]),
        (2, 54, [1, 2, 3, 4, ELLIPSIS, 54]),
        (27, 54, [1, ELLIPSIS, 25, 26, 27, 28, 29, ELLIPSIS, 54]),
        (53, 54, [1, ELLIPSIS, 51, 52, 53, 54]),
        (54, 54, [1, ELLIPSIS, 52, 53, 54]),
        (1, 1, [1]),
        (4, 7, [1, 2, 3, 4, 5, 6, 7]),
        (-10, 54, [1, 2, 3, ELLIPSIS, 54]),
        (999, 54, [1, ELLIPSIS, 52, 53, 54]),
    ],
)
def test_pagination_window_cases(current, total, expected):
    assert pagination_window(current, total) == expected


def test_pagination_window_never_duplicates_ellipsis():
    window = pagination_window(27, 100)
    assert all(not (left == right == ELLIPSIS) for left, right in zip(window, window[1:]))
