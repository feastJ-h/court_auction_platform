import asyncio

from backend.crawler.scraper import crawl_court_notices


def test_real_court_download() -> None:
    downloaded = asyncio.run(crawl_court_notices(max_posts=3, max_downloads=1))
    assert downloaded
    assert downloaded[0].file_path.exists()
    assert downloaded[0].file_size > 0
    assert downloaded[0].sequence == 1
    assert downloaded[0].notice_date
    assert downloaded[0].expire_date


if __name__ == "__main__":
    test_real_court_download()
    print("Sprint 4 crawler test passed")
