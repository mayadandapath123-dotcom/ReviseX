"""OptionalFreeAPIProvider — opt-in remote inference with a free-tier endpoint.

Disabled unless FREE_AI_API_URL is set. Keys live server-side only and are never
included in any response body. Falls back to LocalAIProvider on any failure.
"""

from __future__ import annotations

import logging
from typing import Any, Sequence

import httpx

from app.ai.base import Capability, FactInput, GeneratedItem, GenerationSpec, Insights
from app.ai.local import LocalAIProvider
from app.ai.ollama import SYSTEM_PROMPT, _build_prompt, _parse_items
from app.config.settings import get_settings

logger = logging.getLogger("leap.ai.free")


class FreeAPIProvider:
    name = "free_api"

    def __init__(self, fallback: LocalAIProvider | None = None):
        self.settings = get_settings()
        self.fallback = fallback or LocalAIProvider()

    def available(self) -> bool:
        return bool(self.settings.free_api_url)

    def capabilities(self) -> set[Capability]:
        return {"generate_items", "generate_explanation", "generate_hints", "analyse_session"}

    def generate_items(self, facts: Sequence[FactInput], spec: GenerationSpec) -> list[GeneratedItem]:
        if not self.available():
            return self.fallback.generate_items(facts, spec)

        headers = {"Content-Type": "application/json"}
        if self.settings.free_api_key:
            headers["Authorization"] = f"Bearer {self.settings.free_api_key}"

        try:
            response = httpx.post(
                str(self.settings.free_api_url),
                headers=headers,
                json={
                    "system": SYSTEM_PROMPT,
                    "prompt": _build_prompt(facts, spec),
                    "max_tokens": 1200,
                    "temperature": 0.3,
                },
                timeout=25.0,
            )
            response.raise_for_status()
            payload: Any = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("Free AI API failed: %s", exc)
            return self.fallback.generate_items(facts, spec)

        content = _extract_text(payload)
        parsed = _parse_items(content) if content else None
        if not parsed:
            return self.fallback.generate_items(facts, spec)

        items: list[GeneratedItem] = []
        for entry in parsed[: spec.count]:
            try:
                items.append(
                    GeneratedItem(
                        prompt=str(entry["prompt"]),
                        options=[str(o) for o in entry["options"]],
                        answer_index=int(entry["answer_index"]),
                        difficulty=str(entry.get("difficulty", spec.difficulty)),
                        explanation=entry.get("explanation"),
                        hint=entry.get("hint"),
                        fact_ids=[str(f) for f in entry.get("fact_ids", [])],
                        provider=self.name,
                        raw=entry,
                    )
                )
            except (KeyError, TypeError, ValueError):
                continue
        return items or self.fallback.generate_items(facts, spec)

    def generate_explanation(self, item: dict[str, Any], facts: Sequence[FactInput]) -> str | None:
        return self.fallback.generate_explanation(item, facts)

    def generate_hints(self, item: dict[str, Any], facts: Sequence[FactInput]) -> list[str]:
        return self.fallback.generate_hints(item, facts)

    def analyse_session(self, session: dict[str, Any]) -> Insights:
        return self.fallback.analyse_session(session)


def _extract_text(payload: Any) -> str | None:
    if isinstance(payload, str):
        return payload
    if isinstance(payload, dict):
        for key in ("response", "text", "content", "output"):
            value = payload.get(key)
            if isinstance(value, str):
                return value
        choices = payload.get("choices")
        if isinstance(choices, list) and choices:
            message = choices[0].get("message", {})
            if isinstance(message, dict):
                return message.get("content")
    return None
