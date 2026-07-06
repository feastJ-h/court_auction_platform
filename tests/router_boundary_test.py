from __future__ import annotations

from collections import Counter
import importlib
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

TEST_DB_PATH = PROJECT_ROOT / "storage" / "test" / "router_boundary_test.db"
TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

os.environ["DB_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["APP_SECRET_KEY"] = "router-boundary-test-secret"

from main_app import app  # noqa: E402


EXPECTED_SINGLETON_ROUTES = {
    ("GET", "/auctions"),
    ("GET", "/auctions/{auction_item_id}"),
    ("GET", "/onbid"),
    ("GET", "/onbid/{auction_item_id}"),
    ("POST", "/onbid/{auction_item_id}/preference"),
    ("POST", "/api/onbid/{auction_item_id}/preference"),
    ("GET", "/my"),
    ("GET", "/my/onbid/favorites"),
    ("GET", "/my/onbid/passed"),
    ("GET", "/my/onbid/watching"),
    ("GET", "/cases"),
    ("GET", "/cases/{event_id}"),
    ("GET", "/about"),
    ("GET", "/disclaimer"),
    ("GET", "/privacy"),
    ("GET", "/terms"),
    ("GET", "/privacy-draft"),
    ("GET", "/robots.txt"),
    ("GET", "/sitemap.xml"),
    ("POST", "/api/admin/auctions/onbid/sync"),
    ("POST", "/api/admin/auctions/{auction_item_id}/links"),
    ("GET", "/api/admin/auctions/{auction_item_id}/link-candidates"),
    ("GET", "/api/cases/{case_id}/auction-link-candidates"),
    ("GET", "/admin/users"),
    ("POST", "/admin/users"),
    ("POST", "/admin/users/{user_id}/active"),
    ("POST", "/admin/users/{user_id}/role"),
    ("GET", "/admin"),
    ("POST", "/admin/analysis-provider"),
    ("GET", "/admin/assets"),
    ("GET", "/admin/analysis"),
    ("GET", "/admin/collection"),
    ("GET", "/admin/settings"),
    ("GET", "/admin/reviews"),
    ("GET", "/user"),
    ("GET", "/user/passed"),
    ("GET", "/user/bookmarks"),
    ("GET", "/user/my"),
    ("GET", "/user/watching"),
    ("GET", "/user/watchlist"),
    ("POST", "/user/events/{event_id}/pass"),
    ("POST", "/user/events/{event_id}/unpass"),
    ("POST", "/user/events/{event_id}/bookmark"),
    ("POST", "/user/events/{event_id}/unbookmark"),
    ("POST", "/user/events/{event_id}/watch"),
    ("POST", "/user/events/{event_id}/unwatch"),
    ("POST", "/user/events/{event_id}/note"),
    ("POST", "/api/admin/events/{event_id}/basic-analysis"),
    ("GET", "/api/local-analysis/status"),
    ("GET", "/api/admin/analysis-reviews/summary"),
    ("POST", "/api/admin/analysis-results/{analysis_result_id}/reviews"),
    ("POST", "/admin/analysis-results/{analysis_result_id}/reviews"),
    ("POST", "/api/analyze/deep/{event_id}"),
    ("POST", "/api/analyze/deep/{event_id}/jobs"),
    ("GET", "/api/analyze/jobs/{job_id}"),
    ("GET", "/api/analyze/deep/{event_id}/jobs/latest"),
    ("POST", "/api/analyze/jobs/{job_id}/cancel"),
    ("POST", "/api/analyze/jobs/{job_id}/cancel-request"),
    ("POST", "/api/analyze/jobs/{job_id}/retry"),
    ("GET", "/api/analyze/jobs/{job_id}/events"),
    ("POST", "/api/analyze/jobs/{job_id}/continue"),
    ("POST", "/api/admin/events/{event_id}/ocr/jobs"),
    ("POST", "/api/admin/ocr/enqueue"),
    ("GET", "/api/admin/ocr/status"),
    ("GET", "/api/admin/collection-quality"),
    ("GET", "/api/admin/onbid-quality"),
    ("GET", "/documents/raw/{raw_doc_id}"),
}

EXPECTED_ROUTER_REGISTRARS = {
    "backend.web.routers.admin_operations": "register_admin_operation_routes",
    "backend.web.routers.admin_users": "register_admin_user_routes",
    "backend.web.routers.analysis": "register_analysis_routes",
    "backend.web.routers.auctions": "register_auction_routes",
    "backend.web.routers.cases": "register_case_routes",
    "backend.web.routers.documents": "register_document_routes",
    "backend.web.routers.ocr_operations": "register_ocr_operation_routes",
}


def main() -> int:
    route_counts = Counter(
        (method, route.path)
        for route in app.routes
        for method in getattr(route, "methods", set())
        if method not in {"HEAD", "OPTIONS"}
    )
    missing = sorted(route for route in EXPECTED_SINGLETON_ROUTES if route_counts[route] == 0)
    duplicated = sorted(route for route in EXPECTED_SINGLETON_ROUTES if route_counts[route] > 1)

    assert not missing, f"Missing routes: {missing}"
    assert not duplicated, f"Duplicated routes: {duplicated}"

    for module_name, function_name in EXPECTED_ROUTER_REGISTRARS.items():
        module = importlib.import_module(module_name)
        registrar = getattr(module, function_name, None)
        assert callable(registrar), f"Missing router registrar: {module_name}.{function_name}"

    print(f"isolated_db={TEST_DB_PATH}")
    print("PASS - router boundary registration")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
