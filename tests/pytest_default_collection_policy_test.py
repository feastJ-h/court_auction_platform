from __future__ import annotations

from pathlib import Path


def main() -> int:
    config = (Path(__file__).resolve().parents[1] / "pytest.ini").read_text(encoding="utf-8")
    assert "testpaths = tests" in config
    assert "not integration and not external" in config
    assert "integration:" in config and "external:" in config
    print("PASS - pytest default collection policy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
