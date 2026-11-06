"""Write the plan outputs for a fixture worker: JSON, timelines and calendars.

    uv run python scripts/plan_outputs.py [fixture] [--seed N] [--out DIR]

Writes <fixture>.json, <fixture>.en.txt, <fixture>.tl.txt, <fixture>.en.ics and
<fixture>.tl.ics into DIR (default: out/). Rewording follows the ZEITGEBER_LLM_* settings and
is off unless configured.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from zeitgeber.output import plan_document
from zeitgeber.output.ics import render_ics
from zeitgeber.output.plan import render_timeline
from zeitgeber.output.providers import rewriter_from_settings
from zeitgeber.plan import SearchConfig, search
from zeitgeber.schedule import Schedule

FIXTURES = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "schedules"


def load(name: str) -> Schedule:
    data = json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))
    data.pop("description")
    return Schedule.model_validate(data)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", nargs="?", default="permanent_nights")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", type=Path, default=Path("out"))
    args = parser.parse_args()
    result = search(load(args.fixture), SearchConfig(seed=args.seed))
    doc = plan_document(result, datetime.now(UTC), rewriter=rewriter_from_settings())
    args.out.mkdir(parents=True, exist_ok=True)
    base = args.out / args.fixture
    base.with_suffix(".json").write_text(doc.model_dump_json(indent=2) + "\n", encoding="utf-8")
    for lang in ("en", "tl"):
        Path(f"{base}.{lang}.txt").write_text(render_timeline(doc, lang), encoding="utf-8")
        Path(f"{base}.{lang}.ics").write_bytes(render_ics(doc, lang).encode())
    print(f"wrote {base}.json, .en.txt, .tl.txt, .en.ics, .tl.ics")
    return 0


if __name__ == "__main__":
    sys.exit(main())
