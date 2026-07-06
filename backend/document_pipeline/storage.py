import re
import shutil
from pathlib import Path

from sqlalchemy.orm import Session

from backend.config import PROJECT_ROOT
from backend.database.models import AssetEvent, RawDocument


ANALYZED_DOCUMENT_DIR = PROJECT_ROOT / "storage" / "processed" / "analyzed_documents"


def project_relative(path: Path) -> str:
    return str(path.resolve().relative_to(PROJECT_ROOT.resolve()))


def safe_existing_path(file_path: str) -> Path:
    path = Path(file_path)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    resolved = path.resolve()
    if not str(resolved).startswith(str(PROJECT_ROOT.resolve())):
        raise ValueError("Document path is outside the project root")
    return resolved


def sanitize_path_part(value: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value).strip("._ ")
    return cleaned[:120] or "document"


def archive_analyzed_document(document: RawDocument, case_number: str) -> str:
    source = safe_existing_path(document.file_path)
    if not source.exists():
        return document.file_path
    if ANALYZED_DOCUMENT_DIR.resolve() in source.parents:
        return document.file_path

    ANALYZED_DOCUMENT_DIR.mkdir(parents=True, exist_ok=True)
    safe_case = sanitize_path_part(case_number)
    destination = ANALYZED_DOCUMENT_DIR / f"{safe_case}_{source.name}"
    if destination.exists():
        destination = ANALYZED_DOCUMENT_DIR / f"{safe_case}_{document.file_hash[:12]}_{source.name}"

    shutil.move(str(source), str(destination))
    document.file_path = project_relative(destination)
    return document.file_path


def archive_event_document(session: Session, event: AssetEvent) -> str:
    archived_path = archive_analyzed_document(event.raw_document, event.case_number)
    session.flush()
    return archived_path
