"""Wording providers behind the :class:`zeitgeber.output.wording.Rewriter` protocol.

Each provider gets one filled nudge template and its language. The schedule, the plan and any
personal detail never leave the process.
"""

from __future__ import annotations

from typing import Any

from zeitgeber.output.copy import Lang
from zeitgeber.output.wording import Rewriter
from zeitgeber.settings import Settings

_VOICE = {
    "en": "Write in plain English.",
    "tl": "Write in Taglish, the mix of Tagalog and English spoken in Metro Manila.",
}
SYSTEM = (
    "You reword short reminders for people who work night shifts. Keep the meaning. Keep every "
    "time and number exactly as written and add no new ones. Add no facts, advice or health "
    "claims. Use short sentences, no dashes, no emoji. Reply with the reworded reminder only. "
)


class RewriteError(RuntimeError):
    """The provider returned no usable text."""


class AnthropicRewriter:
    """Rewording through the Anthropic Messages API (install ``zeitgeber-core[llm]``)."""

    def __init__(self, model: str, timeout_s: float, client: Any = None) -> None:
        if client is None:
            try:
                import anthropic
            except ImportError as err:
                raise RuntimeError(
                    "LLM wording is on but the anthropic package is missing; "
                    "install zeitgeber-core[llm]"
                ) from err
            client = anthropic.Anthropic(timeout=timeout_s, max_retries=1)
        self.client = client
        self.model = model

    def rewrite(self, text: str, lang: Lang) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            system=SYSTEM + _VOICE[lang],
            output_config={"effort": "low"},
            messages=[{"role": "user", "content": text}],
        )
        if response.stop_reason != "end_turn":
            raise RewriteError(f"stopped: {response.stop_reason}")
        words = "".join(b.text for b in response.content if b.type == "text").strip()
        if not words:
            raise RewriteError("no text")
        return words


def rewriter_from_settings(settings: Settings | None = None) -> Rewriter | None:
    """The configured provider, or None when rewording is off (templates are used)."""
    settings = settings or Settings.from_env()
    if not settings.llm_wording:
        return None
    if settings.llm_provider == "anthropic":
        return AnthropicRewriter(settings.llm_model, settings.llm_timeout_s)
    raise ValueError(f"unknown wording provider {settings.llm_provider!r}")
