from collections import Counter
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.config import PROJECT_ROOT
from backend.database.models import AssetEvent, CollectionEvidence, RawDocument


def _resolve_document_path(file_path: str) -> Path:
    path = Path(file_path)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path


def build_collection_quality_summary(session: Session) -> dict:
    total_documents = session.scalar(select(func.count(RawDocument.id))) or 0
    total_events = session.scalar(select(func.count(AssetEvent.id))) or 0
    evidence_count = session.scalar(select(func.count(CollectionEvidence.id))) or 0

    parse_rows = session.execute(
        select(AssetEvent.parse_status, func.count(AssetEvent.id)).group_by(AssetEvent.parse_status)
    ).all()
    parse_status_counts = {str(status): int(count) for status, count in parse_rows}

    unknown_notice_count = session.scalar(
        select(func.count(AssetEvent.id)).where(AssetEvent.notice_date == "UNKNOWN")
    ) or 0
    unknown_expire_count = session.scalar(
        select(func.count(AssetEvent.id)).where(AssetEvent.expire_date == "UNKNOWN")
    ) or 0
    local_ingested_count = session.scalar(
        select(func.count(AssetEvent.id)).where(AssetEvent.status == "LOCAL_INGESTED")
    ) or 0

    duplicate_rows = session.execute(
        select(RawDocument.file_hash, func.count(RawDocument.id))
        .group_by(RawDocument.file_hash)
        .having(func.count(RawDocument.id) > 1)
    ).all()

    missing_files = []
    extension_counts: Counter[str] = Counter()
    for document in session.scalars(select(RawDocument)).all():
        resolved = _resolve_document_path(document.file_path)
        extension_counts[resolved.suffix.lower() or "NO_EXTENSION"] += 1
        if not resolved.exists():
            missing_files.append(
                {
                    "raw_doc_id": document.id,
                    "file_path": document.file_path,
                    "source_url": document.source_url,
                }
            )

    quality_warnings = []
    if unknown_notice_count:
        quality_warnings.append(f"작성일 UNKNOWN {unknown_notice_count}건")
    if unknown_expire_count:
        quality_warnings.append(f"공고만료일 UNKNOWN {unknown_expire_count}건")
    if local_ingested_count:
        quality_warnings.append(f"LOCAL_INGESTED {local_ingested_count}건")
    if missing_files:
        quality_warnings.append(f"원본 파일 누락 {len(missing_files)}건")
    if duplicate_rows:
        quality_warnings.append(f"중복 file_hash {len(duplicate_rows)}개")

    return {
        "total_documents": total_documents,
        "total_events": total_events,
        "evidence_count": evidence_count,
        "parse_status_counts": parse_status_counts,
        "unknown_notice_count": unknown_notice_count,
        "unknown_expire_count": unknown_expire_count,
        "local_ingested_count": local_ingested_count,
        "duplicate_hash_count": len(duplicate_rows),
        "duplicate_hashes": [
            {"file_hash": str(file_hash), "count": int(count)}
            for file_hash, count in duplicate_rows[:20]
        ],
        "missing_file_count": len(missing_files),
        "missing_files": missing_files[:20],
        "extension_counts": dict(sorted(extension_counts.items())),
        "quality_warnings": quality_warnings,
        "quality_state": "warning" if quality_warnings else "ok",
    }
