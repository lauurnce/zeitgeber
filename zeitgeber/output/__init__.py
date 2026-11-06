"""Plan outputs: the versioned plan document, timeline, calendar export and nudges.

- :mod:`zeitgeber.output.plan`: :class:`PlanDocument` (JSON schema 1.0) and the text timeline.
- :mod:`zeitgeber.output.ics`: the calendar export with reminders.
- :mod:`zeitgeber.output.nudges`: template nudges in English and Taglish.
- :mod:`zeitgeber.output.wording`: optional rewording held to the plan by a grounding check.
- :mod:`zeitgeber.output.copy`: the string catalog every user-facing string comes from.
"""

from __future__ import annotations

from datetime import datetime

from zeitgeber.output.nudges import build_nudges
from zeitgeber.output.plan import PlanDocument, build_document
from zeitgeber.output.wording import GroundingCheck, Rewriter
from zeitgeber.plan import PlanResult

__all__ = ["PlanDocument", "plan_document"]


def plan_document(
    result: PlanResult,
    generated_at: datetime,
    rewriter: Rewriter | None = None,
    check: GroundingCheck | None = None,
) -> PlanDocument:
    """The full plan document with nudges. Without a rewriter every nudge is its template."""
    doc = build_document(result, generated_at)
    return doc.model_copy(update={"nudges": build_nudges(doc, rewriter, check)})
