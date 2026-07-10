from __future__ import annotations

import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import time

import pytest


pytestmark = pytest.mark.visual
ROOT = Path(__file__).resolve().parents[1]
SCREENSHOT_DIR = ROOT / "storage" / "qa" / "v010"
AXE_PATH = ROOT / "node_modules" / "axe-core" / "axe.min.js"


def _wait_for_port(port: int, timeout: float = 20.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(0.5)
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                return
        time.sleep(0.2)
    raise RuntimeError(f"local server did not start on port {port}")


def _critical_accessibility_violations(page) -> list[dict]:
    page.add_script_tag(path=str(AXE_PATH))
    results = page.evaluate("async () => await axe.run(document, { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa'] } })")
    return [violation for violation in results["violations"] if violation.get("impact") in {"critical", "serious"}]


def test_public_beta_core_routes_and_responsive_contracts():
    pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import expect, sync_playwright

    port = 8765
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main_app:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait_for_port(port)
        SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as playwright:
            try:
                browser = playwright.chromium.launch(headless=True)
            except Exception as exc:  # browser package is an environment prerequisite
                pytest.skip(f"Playwright Chromium unavailable: {type(exc).__name__}")
            try:
                routes = [
                    ("home", "/"),
                    ("onbid", "/onbid"),
                    ("real-estate", "/onbid?category=real_estate"),
                    ("movable", "/onbid?category=movable"),
                    ("national-property", "/onbid?category=national_property"),
                    ("today", "/onbid/today"),
                    ("cases", "/cases"),
                    ("terms", "/terms"),
                    ("privacy", "/privacy"),
                    ("login", "/login"),
                ]
                for width, height in ((360, 800), (390, 844), (768, 1024), (1024, 768), (1440, 900)):
                    context = browser.new_context(viewport={"width": width, "height": height})
                    page = context.new_page()
                    for name, path in routes:
                        response = page.goto(f"http://127.0.0.1:{port}{path}", wait_until="networkidle")
                        assert response and response.status == 200, (path, response.status if response else None)
                        overflow = page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
                        assert overflow <= 1, (path, width, overflow)
                        if width in {390, 1440}:
                            page.screenshot(path=str(SCREENSHOT_DIR / f"{name}-{width}x{height}.png"), full_page=True)
                        if width == 390:
                            assert _critical_accessibility_violations(page) == [], path
                    context.close()

                context = browser.new_context(viewport={"width": 390, "height": 844})
                page = context.new_page()
                page.goto(f"http://127.0.0.1:{port}/onbid", wait_until="networkidle")
                tabs = page.locator('[data-onbid-category-tabs="true"]')
                filters = page.locator('[data-filter-drawer="true"]')
                assert tabs.count() == 1
                assert tabs.bounding_box()["y"] < filters.bounding_box()["y"]
                assert page.locator('select[name="category"]').count() == 0
                if page.locator('[data-pagination-mobile="true"]').count():
                    assert page.locator('[data-pagination-mobile="true"]').is_visible()
                    assert not page.locator('[data-pagination-desktop="true"]').is_visible()
                detail_href = page.locator('[data-review-card="true"] h2 a').first.get_attribute("href")
                assert detail_href
                page.goto(f"http://127.0.0.1:{port}{detail_href}", wait_until="networkidle")
                assert _critical_accessibility_violations(page) == []

                username = os.getenv("BETA_TEST_USERNAME", "")
                password = os.getenv("BETA_TEST_PASSWORD", "")
                if username and password:
                    page.goto(f"http://127.0.0.1:{port}/login?next=/onbid")
                    page.fill('input[name="username"]', username)
                    page.fill('input[name="password"]', password)
                    page.click('button[type="submit"]')
                    page.wait_for_url(f"http://127.0.0.1:{port}/onbid")
                    assert page.locator('form[data-preference-form="passed"]').count() > 0
                context.close()
            finally:
                browser.close()
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()


def test_logged_in_pass_undo_restore_and_memo_flow():
    pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import expect, sync_playwright

    port = 8766
    db_path = ROOT / "storage" / "test" / "v010_playwright_login.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    username = f"beta_{secrets.token_hex(4)}"
    password = secrets.token_urlsafe(18)
    env = os.environ.copy()
    env.update(
        {
            "DB_URL": f"sqlite:///{db_path.as_posix()}",
            "APP_SECRET_KEY": secrets.token_urlsafe(32),
            "REVIEW_MODE": "false",
            "BETA_MODE": "true",
            "BETA_TEST_USERNAME": username,
            "BETA_TEST_PASSWORD": password,
        }
    )
    seed_code = """
import os
from datetime import date, timedelta
from backend.database.models import AuctionItem
from backend.database.session import init_db, session_scope
from backend.services.auth import create_user
init_db()
with session_scope() as db:
    create_user(db, os.environ['BETA_TEST_USERNAME'], os.environ['BETA_TEST_PASSWORD'], 'Beta E2E', 'user')
    db.add(AuctionItem(source='ONBID', cltr_mng_no='V010-E2E', pbct_cdtn_no='1', item_name='베타 E2E 검토 물건', asset_type='동산', address='서울 테스트', minimum_bid_price=1000000, bid_start_at=date.today().isoformat(), bid_end_at=(date.today()+timedelta(days=5)).isoformat(), status='입찰중', public_category='movable', freshness_date=date.today().isoformat(), freshness_status='fresh', public_visible=True))
"""
    subprocess.run([sys.executable, "-c", seed_code], cwd=ROOT, env=env, check=True, capture_output=True)
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main_app:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait_for_port(port)
        with sync_playwright() as playwright:
            try:
                browser = playwright.chromium.launch(headless=True)
            except Exception as exc:
                pytest.skip(f"Playwright Chromium unavailable: {type(exc).__name__}")
            try:
                page = browser.new_page(viewport={"width": 390, "height": 844})
                page.goto(f"http://127.0.0.1:{port}/login?next=/onbid")
                page.fill('input[name="username"]', username)
                page.fill('input[name="password"]', password)
                page.click('button[type="submit"]')
                page.wait_for_url(f"http://127.0.0.1:{port}/onbid")
                card = page.locator('[data-review-card="true"]').first
                expect(card).to_be_visible()

                card.locator('form[data-preference-form="favorite"] button').click()
                expect(page.locator('[data-toast-message]')).to_have_text("관심에 저장했습니다")
                card.locator('form[data-preference-form="passed"] button').click()
                expect(card).to_be_hidden()
                page.locator('[data-toast-undo]').click()
                expect(card).to_be_visible()
                card.locator('form[data-preference-form="passed"] button').click()
                expect(card).to_be_hidden()

                page.goto(f"http://127.0.0.1:{port}/my/onbid/passed")
                passed_card = page.locator('[data-review-card="true"]').first
                expect(passed_card).to_be_visible()
                passed_card.locator('form[data-preference-form="passed"] button').click()
                expect(passed_card).to_be_hidden()

                page.goto(f"http://127.0.0.1:{port}/onbid/1")
                page.fill('textarea[name="note"]', "베타 메모 1")
                page.click('button:has-text("메모 저장")')
                page.wait_for_load_state("networkidle")
                page.goto(f"http://127.0.0.1:{port}/my/onbid/notes")
                expect(page.get_by_text("베타 메모 1")).to_be_visible()
                assert _critical_accessibility_violations(page) == []
                page.screenshot(path=str(SCREENSHOT_DIR / "logged-in-review-390x844.png"), full_page=True)
            finally:
                browser.close()
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
