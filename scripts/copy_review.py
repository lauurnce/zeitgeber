"""Write docs/COPY_REVIEW.md from the string catalog.

uv run python scripts/copy_review.py
"""

from pathlib import Path

from zeitgeber.output.copy import review_markdown

TARGET = Path(__file__).resolve().parents[1] / "docs" / "COPY_REVIEW.md"

if __name__ == "__main__":
    TARGET.write_text(review_markdown(), encoding="utf-8")
    print(f"wrote {TARGET.relative_to(TARGET.parents[1])}")
