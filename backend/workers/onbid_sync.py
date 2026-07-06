from __future__ import annotations

import argparse
from datetime import datetime
from zoneinfo import ZoneInfo

from backend.database.session import init_db, session_scope
from backend.database.models import CrawlRun
from backend.onbid.client import OnbidClient, first_value, normalize_onbid_api_item
from backend.services.auction_items import (
    upsert_auction_item,
    upsert_auction_notice_item_link,
    upsert_auction_notice_payload,
)
from backend.services.crawl_runs import begin_crawl_run, finish_crawl_run

KST = ZoneInfo("Asia/Seoul")


def run_onbid_sync(
    *,
    limit: int = 20,
    sample: bool = False,
    log_path: str = "",
    page_no: int = 1,
    max_pages: int = 1,
    prpt_div_cd: str = "0007,0010,0005,0002,0003,0006,0008,0011,0013",
    pvct_trgt_yn: str = "N",
    api_kind: str = "real_estate",
    include_details: bool = False,
    include_notice_details: bool = False,
    include_notice_items: bool = False,
    run_type: str = "",
) -> dict:
    init_db()
    today = datetime.now(tz=KST).date().isoformat()
    resolved_run_type = run_type or ("onbid_sample" if sample else "onbid_sync")
    with session_scope() as session:
        run = begin_crawl_run(
            session=session,
            run_type=resolved_run_type,
            target_start_date=today,
            target_end_date=today,
            max_pages=max(1, max_pages),
            log_path=log_path,
        )
        run_id = run.id

    try:
        client = OnbidClient()
        payloads = []
        notice_bundles: list[dict] = []
        total_count = 0
        used_sample = sample
        fetched_sources: list[str] = []
        if api_kind in ("real_estate", "all"):
            real_estate_payloads, real_estate_total_count, real_estate_used_sample = collect_real_estate_pages(
                client,
                limit=limit,
                page_no=page_no,
                max_pages=max_pages,
                sample=sample,
                prpt_div_cd=prpt_div_cd,
                pvct_trgt_yn=pvct_trgt_yn,
                include_details=include_details,
            )
            payloads.extend(real_estate_payloads)
            total_count += real_estate_total_count
            used_sample = used_sample or real_estate_used_sample
            fetched_sources.append("real_estate")
        if api_kind in ("movable", "all"):
            movable_payloads, movable_total_count, movable_used_sample = collect_movable_pages(
                client,
                limit=limit,
                page_no=page_no,
                max_pages=max_pages,
                sample=sample,
                include_details=include_details,
            )
            payloads.extend(movable_payloads)
            total_count += movable_total_count
            used_sample = used_sample or movable_used_sample
            fetched_sources.append("movable")
        if api_kind == "notice":
            notice_bundles, notice_total_count, notice_used_sample = collect_notice_pages(
                client,
                limit=limit,
                page_no=page_no,
                max_pages=max_pages,
                sample=sample,
                include_notice_details=include_notice_details,
                include_notice_items=include_notice_items,
            )
            total_count += notice_total_count
            used_sample = used_sample or notice_used_sample
            fetched_sources.append("notice")
        if not fetched_sources:
            raise ValueError(f"Unsupported ONBID api_kind: {api_kind}")
        created_count = 0
        duplicate_count = 0
        notice_inserted = 0
        notice_updated = 0
        notice_item_inserted = 0
        notice_item_duplicates = 0
        notice_item_links = 0
        notice_item_link_updates = 0
        with session_scope() as session:
            for payload in payloads:
                _, created = upsert_auction_item(session, payload)
                if created:
                    created_count += 1
                else:
                    duplicate_count += 1
            for bundle in notice_bundles:
                notice, notice_created = upsert_auction_notice_payload(
                    session,
                    bundle["payload"],
                    detail_payload=bundle.get("detail_payload") or {},
                    item_count=len(bundle.get("items") or []),
                )
                if notice_created:
                    notice_inserted += 1
                else:
                    notice_updated += 1
                for item_payload in bundle.get("items") or []:
                    item, item_created = upsert_auction_item(session, item_payload)
                    if item_created:
                        notice_item_inserted += 1
                    else:
                        notice_item_duplicates += 1
                    _, link_created = upsert_auction_notice_item_link(session, notice, item, item_payload)
                    if link_created:
                        notice_item_links += 1
                    else:
                        notice_item_link_updates += 1
            run = session.get(CrawlRun, run_id)
            finish_crawl_run(
                session,
                run,
                status="SUCCEEDED",
                documents_found=len(payloads) + len(notice_bundles) + notice_item_inserted + notice_item_duplicates,
                documents_downloaded=len(payloads) + len(notice_bundles),
                documents_inserted=created_count + notice_inserted + notice_item_inserted,
                duplicates_skipped=duplicate_count + notice_updated + notice_item_duplicates,
            )
        return {
            "status": "SUCCEEDED",
            "run_id": run_id,
            "api_kind": api_kind,
            "include_details": include_details,
            "include_notice_details": include_notice_details,
            "include_notice_items": include_notice_items,
            "max_pages": max(1, max_pages),
            "fetched_sources": fetched_sources,
            "fetched": len(payloads),
            "notices_fetched": len(notice_bundles),
            "notice_items_fetched": notice_item_inserted + notice_item_duplicates,
            "total_count": total_count,
            "inserted": created_count,
            "duplicates": duplicate_count,
            "notices_inserted": notice_inserted,
            "notices_updated": notice_updated,
            "notice_items_inserted": notice_item_inserted,
            "notice_items_duplicates": notice_item_duplicates,
            "notice_item_links_created": notice_item_links,
            "notice_item_links_updated": notice_item_link_updates,
            "used_sample": used_sample,
            "run_type": resolved_run_type,
        }
    except Exception as exc:
        with session_scope() as session:
            run = session.get(CrawlRun, run_id)
            finish_crawl_run(session, run, status="FAILED", error_message=str(exc))
        return {"status": "FAILED", "run_id": run_id, "error": str(exc)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync ONBID public auction items.")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--page-no", type=int, default=1)
    parser.add_argument("--max-pages", type=int, default=1)
    parser.add_argument("--prpt-div-cd", default="0007,0010,0005,0002,0003,0006,0008,0011,0013")
    parser.add_argument("--pvct-trgt-yn", default="N")
    parser.add_argument("--api-kind", choices=("real_estate", "movable", "all", "notice"), default="real_estate")
    parser.add_argument("--include-details", action="store_true")
    parser.add_argument("--include-notice-details", action="store_true")
    parser.add_argument("--include-notice-items", action="store_true")
    parser.add_argument("--sample", action="store_true")
    parser.add_argument("--run-type", default="")
    parser.add_argument("--log-path", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run_onbid_sync(
        limit=args.limit,
        sample=args.sample,
        log_path=args.log_path,
        page_no=args.page_no,
        max_pages=args.max_pages,
        prpt_div_cd=args.prpt_div_cd,
        pvct_trgt_yn=args.pvct_trgt_yn,
        api_kind=args.api_kind,
        include_details=args.include_details,
        include_notice_details=args.include_notice_details,
        include_notice_items=args.include_notice_items,
        run_type=args.run_type,
    )
    print(result)
    return 0 if result.get("status") == "SUCCEEDED" else 1


def collect_real_estate_pages(
    client: OnbidClient,
    *,
    limit: int,
    page_no: int,
    max_pages: int,
    sample: bool,
    prpt_div_cd: str,
    pvct_trgt_yn: str,
    include_details: bool,
) -> tuple[list[dict], int, bool]:
    payloads: list[dict] = []
    total_count = 0
    used_sample = sample
    for current_page in range(max(1, page_no), max(1, page_no) + max(1, max_pages)):
        page_payloads, fetch_result = client.fetch_real_estate_items(
            limit=limit,
            sample=sample,
            page_no=current_page,
            prpt_div_cd=prpt_div_cd,
            pvct_trgt_yn=pvct_trgt_yn,
            include_details=include_details,
        )
        payloads.extend(page_payloads)
        total_count = max(total_count, fetch_result.total_count)
        used_sample = used_sample or fetch_result.used_sample
        if sample or not page_payloads or len(page_payloads) < limit:
            break
    return payloads, total_count, used_sample


def collect_movable_pages(
    client: OnbidClient,
    *,
    limit: int,
    page_no: int,
    max_pages: int,
    sample: bool,
    include_details: bool,
) -> tuple[list[dict], int, bool]:
    payloads: list[dict] = []
    total_count = 0
    used_sample = sample
    for current_page in range(max(1, page_no), max(1, page_no) + max(1, max_pages)):
        page_payloads, fetch_result = client.fetch_movable_items(
            limit=limit,
            sample=sample,
            page_no=current_page,
            include_details=include_details,
        )
        payloads.extend(page_payloads)
        total_count = max(total_count, fetch_result.total_count)
        used_sample = used_sample or fetch_result.used_sample
        if sample or not page_payloads or len(page_payloads) < limit:
            break
    return payloads, total_count, used_sample


def collect_notice_pages(
    client: OnbidClient,
    *,
    limit: int,
    page_no: int,
    max_pages: int,
    sample: bool,
    include_notice_details: bool,
    include_notice_items: bool,
) -> tuple[list[dict], int, bool]:
    bundles: list[dict] = []
    total_count = 0
    used_sample = sample or not client.settings.onbid_api_key
    for current_page in range(max(1, page_no), max(1, page_no) + max(1, max_pages)):
        notice_payloads, page_total_count = client.fetch_notice_items(
            limit=limit,
            page_no=current_page,
            sample=sample,
        )
        total_count = max(total_count, page_total_count)
        for notice_payload in notice_payloads:
            pbanc_mng_no = str(first_value(notice_payload, "pbancMngNo", "onbidPbancNo", "pbancNo", "noticeNo") or "")
            detail_payload = (
                client.fetch_notice_detail(pbanc_mng_no=pbanc_mng_no, sample=sample)
                if include_notice_details and pbanc_mng_no
                else {}
            )
            normalized_items: list[dict] = []
            if include_notice_items and pbanc_mng_no:
                raw_items, _ = client.fetch_notice_cltr_items(
                    pbanc_mng_no=pbanc_mng_no,
                    limit=limit,
                    page_no=1,
                    sample=sample,
                )
                for raw_item in raw_items:
                    normalized = normalize_onbid_api_item(raw_item, source_api="notice_cltr")
                    normalized["pbancMngNo"] = pbanc_mng_no
                    normalized["noticeTitle"] = first_value(
                        notice_payload,
                        "pbancNm",
                        "pbancTtl",
                        "noticeTitle",
                        default=normalized.get("noticeTitle", ""),
                    )
                    normalized["noticeBody"] = first_value(
                        detail_payload,
                        "pbancDtlCn",
                        "noticeBody",
                        default=normalized.get("noticeBody", ""),
                    )
                    normalized_items.append(normalized)
            bundles.append(
                {
                    "payload": notice_payload,
                    "detail_payload": detail_payload,
                    "items": normalized_items,
                }
            )
        if sample or not notice_payloads or len(notice_payloads) < limit:
            break
    return bundles, total_count, used_sample


if __name__ == "__main__":
    raise SystemExit(main())
