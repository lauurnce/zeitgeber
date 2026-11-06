"""Template nudges in English and Taglish, one per plan event that asks something of the worker.

Each nudge names its event and its catalog template. Times and minutes in a nudge come from that
event only. Optional rewording goes through :func:`zeitgeber.output.wording.finalize_all`, which
keeps the template whenever the rewording fails the grounding check.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from zeitgeber.output.copy import LANGS, Lang, clock, text
from zeitgeber.output.plan import Nudge, PlanDocument, PlanEvent, Text
from zeitgeber.output.wording import GroundingCheck, Rewriter, finalize_all

NUDGE_KINDS = ("sunglasses", "caffeine", "light_seek", "sleep", "rest_sleep", "light_brake", "nap")


def template_for(event: PlanEvent, lows: Sequence[datetime]) -> tuple[str, dict[str, object]]:
    """Catalog key and values for an event's nudge; ``lows`` are the predicted CBTmin times."""
    values: dict[str, object] = {
        "start": clock(event.start_local),
        "end": clock(event.end_local),
        "minutes": round((event.end_utc - event.start_utc).total_seconds() / 60),
    }
    if event.kind == "sleep":
        low_inside = any(event.start_local <= c < event.end_local for c in lows)
        return ("nudge.sleep_low" if low_inside else "nudge.sleep"), values
    return f"nudge.{event.kind}", values


def build_nudges(
    doc: PlanDocument, rewriter: Rewriter | None = None, check: GroundingCheck | None = None
) -> list[Nudge]:
    """Nudges for every event of a kind in :data:`NUDGE_KINDS`, in event order."""
    lows = [d.cbt_min_local for d in doc.days if d.cbt_min_local is not None]
    drafts: list[tuple[PlanEvent, str, dict[Lang, str]]] = []
    for event in doc.events():
        if event.kind not in NUDGE_KINDS:
            continue
        key, values = template_for(event, lows)
        drafts.append((event, key, {lang: text(key, lang, **values) for lang in LANGS}))
    worded = finalize_all(
        [(t[lang], lang) for _, _, t in drafts for lang in LANGS], rewriter, check
    )
    nudges = []
    for event, key, filled in drafts:
        results = {lang: worded[(filled[lang], lang)] for lang in LANGS}
        nudges.append(
            Nudge(
                event_id=event.id,
                template=key,
                text=Text(en=results["en"].text, tl=results["tl"].text),
                source={lang: results[lang].source for lang in LANGS},
            )
        )
    return nudges
