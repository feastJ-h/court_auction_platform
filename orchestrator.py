import asyncio
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from backend.ai_engine.analyzer import (
    AiAnalysisProviderError,
    GeminiAnalysisError,
    analyze_asset_text,
    is_hallucinated,
)
from backend.config import PROJECT_ROOT
from backend.config import raw_quarantine_dir
from backend.crawler.scraper import DownloadedFile, crawl_court_notices
from backend.crawler.scraper import extract_notice_dates, sha256_file
from backend.database.crud import (
    create_ai_analysis,
    create_asset,
    create_asset_event,
    get_or_create_raw_document,
    get_raw_document_by_hash,
    upsert_collection_evidence,
)
from backend.database.models import AiAnalysis, AssetEvent, RawDocument
from backend.database.session import init_db, session_scope
from backend.parser.extractor import extract_document
from sqlalchemy import func, select
import re


MAX_PIPELINE_ITEMS = 5
JULY_2026_TARGET_MONTH = "2026-07"
JUNE_15_2026_START_DATE = "2026-06-15"


@dataclass
class PipelineResult:
    downloaded: int = 0
    parsed: int = 0
    ai_success: int = 0
    ai_failed: int = 0
    stored: int = 0
    skipped_existing: int = 0
    stored_without_analysis: int = 0


def build_case_number(downloaded: DownloadedFile) -> str:
    date_part = (downloaded.notice_date or "UNKNOWN").replace("-", "")
    if date_part == "UNKNOWN":
        date_part = "UNDATE"
    return f"RP-{date_part}-{downloaded.sequence:03d}"


def next_case_number_for_date(session, notice_date: str) -> str:
    date_part = (notice_date or "UNKNOWN").replace("-", "")
    if date_part == "UNKNOWN":
        date_part = "UNDATE"
    prefix = f"RP-{date_part}-"
    rows = session.scalars(
        select(AssetEvent.case_number).where(AssetEvent.case_number.like(f"{prefix}%"))
    ).all()
    max_sequence = 0
    for case_number in rows:
        match = re.search(r"-(\d{3,})$", case_number)
        if match:
            max_sequence = max(max_sequence, int(match.group(1)))
    return f"{prefix}{max_sequence + 1:03d}"


def build_placeholder_payload(downloaded: DownloadedFile) -> dict[str, str]:
    title_blob = f"{downloaded.title} {downloaded.file_path.name}"
    main_category = "부동산" if "부동산" in title_blob else "동산"
    return {
        "main_category": main_category,
        "sub_category": "확인 필요",
        "address": "확인 필요",
    }


def store_evidence(session, document, downloaded: DownloadedFile) -> None:
    upsert_collection_evidence(
        session=session,
        document=document,
        source_title=downloaded.title,
        attachment_name=downloaded.attachment_name,
        notice_date=downloaded.notice_date,
        expire_date=downloaded.expire_date,
        detail_page_text=downloaded.detail_page_text,
    )


def store_event_without_analysis(
    downloaded: DownloadedFile,
    status: str,
    parse_status: str,
    extracted_text: str = "",
) -> None:
    with session_scope() as session:
        document = get_or_create_raw_document(
            session=session,
            file_path=str(downloaded.file_path),
            source_url=downloaded.detail_url,
            file_hash=downloaded.file_hash,
        )
        store_evidence(session, document, downloaded)
        asset = create_asset(session=session, payload=build_placeholder_payload(downloaded))
        create_asset_event(
            session=session,
            asset=asset,
            document=document,
            case_number=build_case_number(downloaded),
            status=status,
            title=downloaded.title,
            url=downloaded.detail_url,
            notice_date=downloaded.notice_date,
            expire_date=downloaded.expire_date,
            parse_status=parse_status,
            extracted_text=extracted_text,
        )


def process_downloaded_file(downloaded: DownloadedFile) -> str:
    with session_scope() as session:
        existing_document = get_raw_document_by_hash(session, downloaded.file_hash)
        if existing_document:
            store_evidence(session, existing_document, downloaded)
            existing_path = existing_document.file_path
            if str(downloaded.file_path) != existing_path:
                downloaded.file_path.unlink(missing_ok=True)
            return "skipped"

    try:
        parsed = extract_document(downloaded.file_path)
    except Exception:
        store_event_without_analysis(
            downloaded=downloaded,
            status="PARSE_FAILED",
            parse_status="PARSE_FAILED",
        )
        return "stored_without_analysis"

    try:
        payload = analyze_asset_text(parsed.extracted_text)
    except (GeminiAnalysisError, AiAnalysisProviderError):
        store_event_without_analysis(
            downloaded=downloaded,
            status="AI_FAILED",
            parse_status=parsed.parse_status,
            extracted_text=parsed.extracted_text,
        )
        return "stored_without_analysis"

    with session_scope() as session:
        document = get_or_create_raw_document(
            session=session,
            file_path=str(downloaded.file_path),
            source_url=downloaded.detail_url,
            file_hash=downloaded.file_hash,
        )
        store_evidence(session, document, downloaded)
        asset = create_asset(session=session, payload=payload)
        event = create_asset_event(
            session=session,
            asset=asset,
            document=document,
            case_number=build_case_number(downloaded),
            status="AI_ANALYZED",
            title=downloaded.title,
            url=downloaded.detail_url,
            notice_date=downloaded.notice_date,
            expire_date=downloaded.expire_date,
            parse_status=parsed.parse_status,
            extracted_text=parsed.extracted_text,
        )
        create_ai_analysis(
            session=session,
            event=event,
            payload=payload,
            is_hallucinated=is_hallucinated(payload),
        )
    return "stored_analyzed"


async def run_pipeline(
    max_items: int = MAX_PIPELINE_ITEMS,
    target_month: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    max_pages: int = 1,
) -> PipelineResult:
    init_db()
    limit = max_items if target_month or start_date or end_date else min(max_items, MAX_PIPELINE_ITEMS)
    result = PipelineResult()
    downloaded_files = await crawl_court_notices(
        max_posts=limit,
        max_downloads=limit,
        target_month=target_month,
        start_date=start_date,
        end_date=end_date,
        max_pages=max_pages,
    )
    downloaded_files = downloaded_files[:limit]
    result.downloaded = len(downloaded_files)

    for downloaded in downloaded_files:
        try:
            status = process_downloaded_file(downloaded)
            if status == "stored_analyzed":
                result.parsed += 1
                result.ai_success += 1
                result.stored += 1
            elif status == "stored_without_analysis":
                result.ai_failed += 1
                result.stored += 1
                result.stored_without_analysis += 1
            else:
                result.skipped_existing += 1
        except Exception:
            result.ai_failed += 1

    print(
        f"처리 건수: {result.stored}, 다운로드: {result.downloaded}, "
        f"파싱: {result.parsed}, AI 성공: {result.ai_success}, "
        f"AI 실패: {result.ai_failed}, 중복 스킵: {result.skipped_existing}, "
        f"분석대기 저장: {result.stored_without_analysis}"
    )
    return result


async def run_july_2026_collection(max_items: int = 20) -> PipelineResult:
    return await run_pipeline(max_items=max_items, target_month=JULY_2026_TARGET_MONTH, max_pages=5)


async def run_since_2026_06_15_collection(max_items: int = 50, max_pages: int = 15) -> PipelineResult:
    result = await run_pipeline(
        max_items=max_items,
        start_date=JUNE_15_2026_START_DATE,
        max_pages=max_pages,
    )
    write_collection_report(
        result=result,
        report_name="collection_since_2026_06_15_report.md",
        title="2026-06-15 이후 법원 공고 수집 리포트",
        start_date=JUNE_15_2026_START_DATE,
        end_date=None,
    )
    return result


def ingest_local_quarantine_files(max_items: int = 100) -> PipelineResult:
    init_db()
    result = PipelineResult()
    candidates = [
        path
        for path in raw_quarantine_dir().iterdir()
        if path.is_file() and path.suffix.lower() in {".pdf", ".hwp", ".hwpx"}
    ][:max_items]
    result.downloaded = len(candidates)

    for file_path in candidates:
        try:
            file_hash = sha256_file(file_path)
            with session_scope() as session:
                existing = get_raw_document_by_hash(session, file_hash)
                if existing:
                    result.skipped_existing += 1
                    continue

            try:
                parsed = extract_document(file_path)
                extracted_text = parsed.extracted_text
                parse_status = parsed.parse_status
            except Exception:
                extracted_text = ""
                parse_status = "PARSE_FAILED"

            notice_date, expire_date = extract_notice_dates(extracted_text or file_path.name)
            if notice_date != "UNKNOWN" and notice_date < JUNE_15_2026_START_DATE:
                notice_date = "UNKNOWN"
            with session_scope() as session:
                document = get_or_create_raw_document(
                    session=session,
                    file_path=str(file_path),
                    source_url=f"local_quarantine://{file_path.name}",
                    file_hash=file_hash,
                )
                upsert_collection_evidence(
                    session=session,
                    document=document,
                    source_title=file_path.stem,
                    attachment_name=file_path.name,
                    notice_date=notice_date,
                    expire_date=expire_date,
                    detail_page_text="로컬 격리소에서 인입된 문서입니다. 원 상세 페이지 정보는 재수집 시 갱신됩니다.",
                )
                asset = create_asset(
                    session=session,
                    payload={
                        "main_category": "부동산" if "부동산" in file_path.name else "동산",
                        "sub_category": "로컬 인입",
                        "address": "확인 필요",
                    },
                )
                create_asset_event(
                    session=session,
                    asset=asset,
                    document=document,
                    case_number=next_case_number_for_date(session, notice_date),
                    status="LOCAL_INGESTED",
                    title=file_path.stem,
                    url=f"local_quarantine://{file_path.name}",
                    notice_date=notice_date,
                    expire_date=expire_date,
                    parse_status=parse_status,
                    extracted_text=extracted_text,
                )
            result.stored += 1
            result.stored_without_analysis += 1
        except Exception:
            result.ai_failed += 1

    write_collection_report(
        result=result,
        report_name="local_quarantine_ingest_report.md",
        title="로컬 격리소 미등록 파일 인입 리포트",
    )
    return result


def collect_db_snapshot() -> dict:
    with session_scope() as session:
        notice_rows = session.execute(
            select(AssetEvent.notice_date, func.count(AssetEvent.id))
            .group_by(AssetEvent.notice_date)
            .order_by(AssetEvent.notice_date.asc())
        ).all()
        return {
            "raw_documents": session.scalar(select(func.count(RawDocument.id))) or 0,
            "asset_events": session.scalar(select(func.count(AssetEvent.id))) or 0,
            "ai_analyses": session.scalar(select(func.count(AiAnalysis.id))) or 0,
            "notice_dates": {str(date): int(count) for date, count in notice_rows},
        }


def write_collection_report(
    result: PipelineResult,
    report_name: str,
    title: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> Path:
    snapshot = collect_db_snapshot()
    report_path = PROJECT_ROOT / "reports" / report_name
    report_path.parent.mkdir(parents=True, exist_ok=True)
    date_lines = "\n".join(
        f"- {notice_date}: {count}건" for notice_date, count in snapshot["notice_dates"].items()
    ) or "- 저장된 날짜 없음"
    content = f"""# {title}

## 1. 실행 조건
- 실행 시각: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- 시작일: {start_date or "제한 없음"}
- 종료일: {end_date or "제한 없음"}

## 2. 수집 결과
- 다운로드 확인: {result.downloaded}건
- 새 저장: {result.stored}건
- 중복 스킵: {result.skipped_existing}건
- 파싱 성공 및 기본 분석 성공: {result.ai_success}건
- 파싱/AI 실패로 분석대기 저장: {result.stored_without_analysis}건
- 전체 실패 카운트: {result.ai_failed}건

## 3. 현재 DB 상태
- raw_documents: {snapshot["raw_documents"]}건
- asset_events: {snapshot["asset_events"]}건
- ai_analyses: {snapshot["ai_analyses"]}건

## 4. 저장된 공고일 분포
{date_lines}

## 5. 검토 메모
- 수집기는 날짜 조건과 페이지네이션을 함께 사용한다.
- 동일 파일은 SHA-256 해시 기준으로 중복 저장하지 않는다.
- 중복 문서는 기존 RawDocument의 수집 증거를 갱신한다.
"""
    report_path.write_text(content, encoding="utf-8")
    return report_path


if __name__ == "__main__":
    pipeline_result = asyncio.run(run_pipeline())
    print(pipeline_result)
