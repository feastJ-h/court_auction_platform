from dataclasses import dataclass
from datetime import date
from pathlib import Path
import hashlib
import random
import re
from typing import Any
from urllib.parse import urljoin

from backend.config import raw_quarantine_dir


TARGET_URL = "https://www.scourt.go.kr/portal/notice/realestate/RealNoticeList.work"
ALLOWED_EXTENSIONS = {".pdf", ".hwp", ".hwpx"}
USER_AGENTS = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 Version/17 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
)


@dataclass(frozen=True)
class CrawlerCandidate:
    index: int
    text: str
    href: str
    onclick: str


@dataclass(frozen=True)
class DownloadedFile:
    sequence: int
    title: str
    detail_url: str
    notice_date: str
    expire_date: str
    detail_page_text: str
    attachment_name: str
    file_path: Path
    file_hash: str
    file_size: int


def sha256_file(file_path: Path) -> str:
    digest = hashlib.sha256()
    with file_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sanitize_filename(file_name: str, fallback: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", file_name).strip("._ ")
    return cleaned[:180] or fallback


def validate_download(file_path: Path) -> None:
    if not file_path.exists() or file_path.stat().st_size == 0:
        file_path.unlink(missing_ok=True)
        raise ValueError("Rejected 0 byte or missing download")
    if file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
        file_path.unlink(missing_ok=True)
        raise ValueError(f"Rejected abnormal extension: {file_path.suffix}")


def normalize_date(raw: str) -> str:
    match = re.search(r"(20\d{2})[.\-/년\s]+(\d{1,2})[.\-/월\s]+(\d{1,2})", raw)
    if not match:
        return "UNKNOWN"
    year, month, day = match.groups()
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def extract_notice_dates(text: str) -> tuple[str, str]:
    compact = re.sub(r"\s+", " ", text)
    labeled_patterns = {
        "notice": (
            r"(작성일|게시일|공고일|등록일)\s*[:：]?\s*(20\d{2}[.\-/년\s]+\d{1,2}[.\-/월\s]+\d{1,2})",
        ),
        "expire": (
            r"(만료일|마감일|종료일|공고만료일|입찰마감)\s*[:：]?\s*(20\d{2}[.\-/년\s]+\d{1,2}[.\-/월\s]+\d{1,2})",
        ),
    }

    notice_date = "UNKNOWN"
    expire_date = "UNKNOWN"
    for pattern in labeled_patterns["notice"]:
        match = re.search(pattern, compact)
        if match:
            notice_date = normalize_date(match.group(2))
            break
    for pattern in labeled_patterns["expire"]:
        match = re.search(pattern, compact)
        if match:
            expire_date = normalize_date(match.group(2))
            break

    if notice_date == "UNKNOWN" or expire_date == "UNKNOWN":
        dates = [normalize_date(item) for item in re.findall(r"20\d{2}[.\-/년\s]+\d{1,2}[.\-/월\s]+\d{1,2}", compact)]
        dates = [date for date in dates if date != "UNKNOWN"]
        if notice_date == "UNKNOWN" and dates:
            notice_date = dates[0]
        if expire_date == "UNKNOWN" and len(dates) > 1:
            expire_date = dates[-1]

    return notice_date, expire_date


def parse_date(value: str | None) -> date | None:
    if not value or value == "UNKNOWN":
        return None
    try:
        year, month, day = value.split("-")
        return date(int(year), int(month), int(day))
    except ValueError:
        return None


def date_in_range(
    notice_date: str,
    target_month: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> bool:
    if target_month and not notice_date.startswith(target_month):
        return False

    parsed = parse_date(notice_date)
    if start_date:
        start = parse_date(start_date)
        if parsed is None or (start is not None and parsed < start):
            return False
    if end_date:
        end = parse_date(end_date)
        if parsed is None or (end is not None and parsed > end):
            return False
    return True


async def collect_candidates(page: Any) -> list[CrawlerCandidate]:
    raw_candidates = await page.eval_on_selector_all(
        "a, button, input[type=button], input[type=submit]",
        """
        elements => elements.map((element, index) => ({
            index,
            text: (
                element.innerText ||
                element.value ||
                element.title ||
                element.getAttribute('aria-label') ||
                ''
            ).trim(),
            href: element.href || element.getAttribute('href') || '',
            onclick: element.getAttribute('onclick') || ''
        }))
        """,
    )
    return [
        CrawlerCandidate(
            index=int(item["index"]),
            text=str(item.get("text") or ""),
            href=str(item.get("href") or ""),
            onclick=str(item.get("onclick") or ""),
        )
        for item in raw_candidates
    ]


def is_detail_candidate(candidate: CrawlerCandidate) -> bool:
    blob = f"{candidate.text} {candidate.href} {candidate.onclick}".lower()
    return "realnoticeview.work" in blob


def is_download_candidate(candidate: CrawlerCandidate) -> bool:
    blob = f"{candidate.text} {candidate.href} {candidate.onclick}".lower()
    if "javascript:download(" in blob:
        return True
    return any(ext in blob for ext in ALLOWED_EXTENSIONS)


def is_next_page_candidate(candidate: CrawlerCandidate) -> bool:
    blob = f"{candidate.text} {candidate.href} {candidate.onclick}".lower()
    text = candidate.text.strip().lower()
    if text in {">", "›", "다음", "다음페이지", "next"}:
        return True
    return any(token in blob for token in ("fncsearch", "gopage", "pageindex", "page_index")) and any(
        token in blob for token in ("next", "다음")
    )


def candidate_key(candidate: CrawlerCandidate) -> str:
    return "|".join((candidate.href.strip(), candidate.onclick.strip(), candidate.text.strip()))


async def click_next_page(page: Any) -> bool:
    candidates = await collect_candidates(page)
    next_candidates = [candidate for candidate in candidates if is_next_page_candidate(candidate)]
    if not next_candidates:
        return False

    previous_url = page.url
    previous_text = ""
    try:
        previous_text = await page.locator("body").inner_text(timeout=5_000)
    except Exception:
        previous_text = ""

    for candidate in next_candidates:
        try:
            locator = page.locator("a, button, input[type=button], input[type=submit]").nth(candidate.index)
            await locator.click(timeout=10_000)
            await page.wait_for_load_state("domcontentloaded", timeout=15_000)
            await page.wait_for_timeout(800)
            current_text = await page.locator("body").inner_text(timeout=5_000)
            if page.url != previous_url or current_text != previous_text:
                return True
        except Exception:
            continue
    return False


async def crawl_court_notices(
    max_posts: int = 5,
    max_downloads: int = 5,
    target_month: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    max_pages: int = 1,
) -> list[DownloadedFile]:
    from playwright.async_api import async_playwright

    destination = raw_quarantine_dir()
    downloaded: list[DownloadedFile] = []

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            accept_downloads=True,
            locale="ko-KR",
        )
        page = await context.new_page()
        await page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=45_000)
        await page.wait_for_timeout(1_000)
        seen_detail_keys: set[str] = set()
        visited_pages = 0

        while visited_pages < max(1, max_pages):
            visited_pages += 1
            detail_candidates = [
                candidate
                for candidate in await collect_candidates(page)
                if is_detail_candidate(candidate) and candidate_key(candidate) not in seen_detail_keys
            ][:max_posts]
            for candidate in detail_candidates:
                seen_detail_keys.add(candidate_key(candidate))

            if not detail_candidates:
                break

            for detail_candidate in detail_candidates:
                if len(downloaded) >= max_downloads:
                    break

                detail_page = await context.new_page()
                try:
                    detail_url = urljoin(TARGET_URL, detail_candidate.href)
                    await detail_page.goto(detail_url, wait_until="domcontentloaded", timeout=30_000)
                    await detail_page.wait_for_timeout(500)
                    detail_text = await detail_page.locator("body").inner_text(timeout=10_000)
                    notice_date, expire_date = extract_notice_dates(detail_text)
                    if not date_in_range(
                        notice_date,
                        target_month=target_month,
                        start_date=start_date,
                        end_date=end_date,
                    ):
                        continue
                    download_candidates = [
                        candidate for candidate in await collect_candidates(detail_page) if is_download_candidate(candidate)
                    ]

                    for download_candidate in download_candidates:
                        if len(downloaded) >= max_downloads:
                            break
                        locator = detail_page.locator("a, button, input[type=button], input[type=submit]").nth(
                            download_candidate.index
                        )
                        async with detail_page.expect_download(timeout=20_000) as download_info:
                            await locator.click(timeout=10_000)
                        download = await download_info.value
                        file_name = sanitize_filename(
                            download.suggested_filename or "",
                            f"court_attachment_{len(downloaded) + 1}.pdf",
                        )
                        file_path = destination / file_name
                        await download.save_as(str(file_path))
                        validate_download(file_path)
                        downloaded.append(
                            DownloadedFile(
                                sequence=len(downloaded) + 1,
                                title=detail_candidate.text or file_path.stem,
                                detail_url=detail_page.url,
                                notice_date=notice_date,
                                expire_date=expire_date,
                                detail_page_text=detail_text,
                                attachment_name=file_name,
                                file_path=file_path,
                                file_hash=sha256_file(file_path),
                                file_size=file_path.stat().st_size,
                            )
                        )
                finally:
                    await detail_page.close()

            if len(downloaded) >= max_downloads:
                break
            if not await click_next_page(page):
                break

        await context.close()
        await browser.close()

    return downloaded
