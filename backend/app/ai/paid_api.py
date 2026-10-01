"""FuturePaidAPIProvider — placeholder for a paid inference backend.

Deliberately inert in the MVP: it reports unavailable unless explicitly
configured, and its key is read server-side only. The point of this module is to
prove the abstraction holds when a paid provider is eventually wired in.
"""

from __future__ import annotations

import logging
from typing import Any, Sequence

from app.ai.base import Capability, FactInput, GeneratedItem, GenerationSpec, Insights
from app.ai.local import LocalAIProvider
from app.config.settings import get_settings

logger = logging.getLogger("leap.ai.paid")


class PaidAPIProvider:
    name = "paid_api"

    def __init__(self, fallback: LocalAIProvider | None = None):
        self.settings = get_settings()
        self.fallback = fallback or LocalAIProvider()

    def available(self) -> bool:
        if not self.settings.paid_api_key:
            return False
        logger.warning("Paid API provider selected but no transport is implemented in this build")
        return False

    def capabilities(self) -> set[Capability]:
        return set()

    def generate_items(self, facts: Sequence[FactInput], spec: GenerationSpec) -> list[GeneratedItem]:
        return self.fallback.generate_items(facts, spec)

    def generate_explanation(self, item: dict[str, Any], facts: Sequence[FactInput]) -> str | None:
        return self.fallback.generate_explanation(item, facts)

    def generate_hints(self, item: dict[str, Any], facts: Sequence[FactInput]) -> list[str]:
        return self.fallback.generate_hints(item, facts)

    def analyse_session(self, session: dict[str, Any]) -> Insights:
        return self.fallback.analyse_session(session)
