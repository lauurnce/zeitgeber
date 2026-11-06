"""Golden files: compare text with a committed copy; ZEITGEBER_UPDATE_GOLDEN=1 rewrites it."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def check_golden(path: Path, actual: str) -> None:
    if os.environ.get("ZEITGEBER_UPDATE_GOLDEN") == "1" or not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(actual, encoding="utf-8")
    expected = path.read_text(encoding="utf-8")
    assert actual == expected, (
        f"{path.relative_to(ROOT)} differs; rerun with ZEITGEBER_UPDATE_GOLDEN=1 after review"
    )
