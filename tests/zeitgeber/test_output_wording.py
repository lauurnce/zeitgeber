"""Grounding check, rewording fallback and the provider adapter, with fake providers only."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest
from fixture_plans import planned

from zeitgeber.output import plan_document
from zeitgeber.output.copy import LANGS, entries, fields_of
from zeitgeber.output.providers import AnthropicRewriter, RewriteError, rewriter_from_settings
from zeitgeber.output.wording import GroundingCheck, finalize, finalize_all, tokens
from zeitgeber.settings import Settings

CHECK = GroundingCheck()
CAFFEINE_TL = "2:30 AM ang huling kape mo. Tubig na lang pagkatapos, para madali kang makatulog."


@dataclass
class FakeRewriter:
    """Returns a scripted reply per input, or the input unchanged, and records each call."""

    replies: dict[str, str] = field(default_factory=dict)
    calls: list[tuple[str, str]] = field(default_factory=list)

    def rewrite(self, text: str, lang: str) -> str:
        self.calls.append((text, lang))
        return self.replies.get(text, text)


def test_tokens_read_times_and_numbers_in_both_languages() -> None:
    assert tokens("2:30 AM, 9 am, 14:30 at 4:45 p.m.") == {
        "t:02:30",
        "t:09:00",
        "t:14:30",
        "t:16:45",
    }
    assert tokens("15 minuto, apat na oras, 1.5 h, two cups") == {"n:15", "n:4", "n:1.5", "n:2"}
    assert tokens("by noon or hatinggabi") == {"t:12:00", "t:00:00"}
    assert tokens("dalawang tasa, isang beses, tatlong oras") == {"n:2", "n:1", "n:3"}


@pytest.mark.parametrize(
    "rewording",
    [
        "3 AM ang huling kape mo. Tubig na lang pagkatapos.",  # invented time
        "Huling kape bago mag-2:45 AM, tapos tubig na.",  # time moved
        "2:30 AM ang huling kape mo, mga dalawang tasa lang.",  # invented count in words
        "2:30 AM ang huling kape mo. Iwasan ito 6 na oras bago matulog.",  # invented number
    ],
)
def test_check_rejects_an_invented_time_or_number(rewording: str) -> None:
    problems = CHECK.problems(rewording, CAFFEINE_TL)
    assert problems and problems[0].startswith("not in the plan")


@pytest.mark.parametrize(
    ("rewording", "term"),
    [
        ("2:30 AM ang huling kape mo. A melatonin dose helps after that.", "melatonin"),
        ("2:30 AM ang huling kape mo. This can cure poor sleep.", "cure"),
        ("2:30 AM ang huling kape mo. No need to diagnose anything.", "diagnose"),
        ("2:30 AM ang huling kape mo. Uminom ng gamot pampatulog kung kailangan.", "gamot"),
        ("2:30 AM ang huling kape mo. Good for a sleep disorder.", "disorder"),
    ],
)
def test_check_rejects_medical_terms(rewording: str, term: str) -> None:
    problems = CHECK.problems(rewording, CAFFEINE_TL)
    assert any(p.startswith("blocked term") and term in p for p in problems)


def test_check_accepts_a_faithful_rewording_and_rejects_padding() -> None:
    good = "Hanggang 2:30 AM lang ang kape mo. Tubig na pagkatapos para madali kang makatulog."
    assert CHECK.passes(good, CAFFEINE_TL)
    assert CHECK.problems("", CAFFEINE_TL) == ["empty"]
    assert "too long" in CHECK.problems(CAFFEINE_TL + " Kape." * 40, CAFFEINE_TL)


@pytest.mark.parametrize("entry", list(entries().values()), ids=lambda e: e.key)
def test_no_catalog_string_contains_a_blocked_term(entry: Any) -> None:
    for lang in LANGS:
        assert CHECK.banned_in(entry.text(lang)) == [], (entry.key, lang)


def test_nudge_templates_carry_no_numbers_of_their_own() -> None:
    """Every number in a nudge comes from a placeholder, that is from the plan."""
    for key, entry in entries().items():
        if key.startswith("nudge."):
            for lang in LANGS:
                literal = entry.text(lang).format(**dict.fromkeys(fields_of(entry.text(lang)), ""))
                assert tokens(literal) == set(), (key, lang)


def test_finalize_uses_the_rewording_or_falls_back_with_a_reason() -> None:
    fake = FakeRewriter({CAFFEINE_TL: "Last coffee at 4 AM."})
    worded = finalize(CAFFEINE_TL, "tl", fake, CHECK)
    assert (worded.text, worded.source) == (CAFFEINE_TL, "fallback")
    assert worded.reason is not None and "t:04:00" in worded.reason
    assert finalize(CAFFEINE_TL, "tl", None, CHECK).source == "template"
    same = finalize(CAFFEINE_TL, "tl", FakeRewriter(), CHECK)
    assert (same.text, same.source) == (CAFFEINE_TL, "rewritten")


def test_provider_errors_fall_back_to_the_template() -> None:
    class Broken:
        def rewrite(self, text: str, lang: str) -> str:
            raise TimeoutError("slow")

    worded = finalize(CAFFEINE_TL, "tl", Broken(), CHECK)
    assert worded.source == "fallback" and worded.reason == "provider error: TimeoutError"


def test_plan_nudges_go_through_the_fake_provider_once_per_distinct_text() -> None:
    result = planned("permanent_nights")
    template_doc = plan_document(result, datetime(2026, 11, 6, tzinfo=UTC))
    sleep = next(n for n in template_doc.nudges if n.template == "nudge.sleep_low")
    caffeine = next(n for n in template_doc.nudges if n.template == "nudge.caffeine")
    fake = FakeRewriter(
        {
            sleep.text.en: "Time to sleep at 9 AM. Curtains shut, phone down.",
            caffeine.text.en: "Stop coffee at 3 AM.",  # invented time, must fall back
            caffeine.text.tl: "Take a melatonin dose at 2:30 AM.",  # blocked, must fall back
        }
    )
    doc = plan_document(result, datetime(2026, 11, 6, tzinfo=UTC), rewriter=fake)
    texts = {(n.text.en, n.text.tl) for n in template_doc.nudges}
    assert len(fake.calls) == len({t for pair in texts for t in pair})
    for n in doc.nudges:
        if n.template == "nudge.sleep_low" and n.event_id == sleep.event_id:
            assert n.text.en.startswith("Time to sleep") and n.source["en"] == "rewritten"
        if n.template == "nudge.caffeine":
            assert n.text == caffeine.text and n.source == {"en": "fallback", "tl": "fallback"}


def test_finalize_all_deduplicates() -> None:
    fake = FakeRewriter()
    out = finalize_all([(CAFFEINE_TL, "tl"), (CAFFEINE_TL, "tl")], fake)
    assert len(out) == 1 and fake.calls == [(CAFFEINE_TL, "tl")]


def test_wording_is_off_unless_configured() -> None:
    assert Settings.from_env({}) == Settings()
    assert rewriter_from_settings(Settings()) is None
    on = Settings.from_env({"ZEITGEBER_LLM_WORDING": "true", "ZEITGEBER_LLM_MODEL": "m"})
    assert on.llm_wording and on.llm_model == "m" and on.llm_provider == "anthropic"
    with pytest.raises(ValueError):
        Settings.from_env({"ZEITGEBER_LLM_PROVIDER": "other"})


class FakeMessages:
    def __init__(self, stop_reason: str, reply: str) -> None:
        self.stop_reason, self.reply = stop_reason, reply
        self.requests: list[dict[str, Any]] = []

    def create(self, **request: Any) -> SimpleNamespace:
        self.requests.append(request)
        block = SimpleNamespace(type="text", text=self.reply)
        return SimpleNamespace(stop_reason=self.stop_reason, content=[block])


def test_adapter_sends_only_the_template_text() -> None:
    messages = FakeMessages("end_turn", " Reworded. ")
    rewriter = AnthropicRewriter("model-x", 5.0, client=SimpleNamespace(messages=messages))
    assert rewriter.rewrite(CAFFEINE_TL, "tl") == "Reworded."
    (request,) = messages.requests
    assert request["model"] == "model-x"
    assert request["messages"] == [{"role": "user", "content": CAFFEINE_TL}]
    assert "Taglish" in request["system"]


def test_adapter_raises_on_a_refusal_so_the_template_is_kept() -> None:
    messages = FakeMessages("refusal", "")
    rewriter = AnthropicRewriter("model-x", 5.0, client=SimpleNamespace(messages=messages))
    with pytest.raises(RewriteError):
        rewriter.rewrite(CAFFEINE_TL, "tl")
    assert finalize(CAFFEINE_TL, "tl", rewriter, CHECK).source == "fallback"
