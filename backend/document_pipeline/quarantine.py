from pathlib import Path

from backend.config import raw_quarantine_dir


def quarantine_dir() -> Path:
    return raw_quarantine_dir()
