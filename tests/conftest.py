"""Keep legacy executable checks isolated from pytest module import side effects.

Legacy ``*_test.py`` files configure their own database at module import time and
expose a ``main()`` entrypoint rather than pytest functions. The beta runner
executes those files in separate processes. Pytest collects only files that
actually define product test functions.
"""

from __future__ import annotations

import ast
from pathlib import Path


TESTS_DIR = Path(__file__).resolve().parent
collect_ignore: list[str] = []
for candidate in TESTS_DIR.glob("*_test.py"):
    try:
        tree = ast.parse(candidate.read_text(encoding="utf-8-sig"), filename=str(candidate))
    except (OSError, SyntaxError, UnicodeDecodeError):
        collect_ignore.append(candidate.name)
        continue
    has_pytest_function = any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")
        for node in tree.body
    )
    if not has_pytest_function:
        collect_ignore.append(candidate.name)
