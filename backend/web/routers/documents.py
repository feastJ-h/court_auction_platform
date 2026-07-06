from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse

from backend.config import PROJECT_ROOT, get_settings
from backend.database.models import RawDocument
from backend.database.session import session_scope
from backend.web.dependencies import RequireUser


def register_document_routes(
    app: FastAPI,
    *,
    require_user: RequireUser,
) -> None:
    @app.get("/documents/raw/{raw_doc_id}")
    def read_raw_document(request: Request, raw_doc_id: int) -> FileResponse:
        project_root = PROJECT_ROOT.resolve()
        if get_settings().review_mode:
            raise HTTPException(status_code=403, detail="Review mode disables raw document access.")
        with session_scope() as session:
            current_user = require_user(request, session)
            if current_user is None:
                raise HTTPException(status_code=401, detail="Login required.")

            document = session.get(RawDocument, raw_doc_id)
            if document is None:
                raise HTTPException(status_code=404, detail="Raw document not found.")

            path = Path(document.file_path)
            if not path.is_absolute():
                path = PROJECT_ROOT / path
            resolved = path.resolve()
            try:
                resolved.relative_to(project_root)
            except ValueError as exc:
                raise HTTPException(status_code=403, detail="File path is outside the project.") from exc
            if not resolved.is_file():
                raise HTTPException(status_code=404, detail="Raw file not found.")
            return FileResponse(path=str(resolved), filename=resolved.name)
