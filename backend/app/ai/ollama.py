"""OllamaProvider — optional local LLM inference.

Completely optional: if Ollama is not installed or the model is missing, the
service silently falls back to LocalAIProvider. Never required for the quiz loop.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Sequence

import httpx

from app.ai.base import Capability, FactInput, GeneratedItem, GenerationSpec, Insights
from app.ai.local import LocalAIProvider
from app.config.settings import get_settings

logger = logging.getLogger("leap.ai.ollama")

SYSTEM_PROMPT = """You generate Class 10 exam-preparation multiple choice questions.

STRICT RULES
1. Use ONLY the facts provided. Never invent, infer or add any fact, number, symbol, name or date that is not in the input.
2. Produce exactly 4 options. Exactly one may be correct.
3. Distractors must be plausible and drawn from the same subject domain (common misconceptions or neighbouring values). Never use joke options.
4. Keep the prompt under 200 characters and the language at Class 10 level.
5. Reply with a JSON array only. No markdown, no commentary.

Each element must have this exact shape:
{"prompt": str, "options": [str, str, str, str], "answer_index": 0-3, "difficulty": "easy"|"medium"|"hard", "explanation": str, "hint": str, "fact_ids": [str]}
"""


class OllamaProvider:
    name = "ollama"

    def __init__(self, fallback: LocalAIProvider | None = None):
        self.settings = get_settings()
        self.fallback = fallback or LocalAIProvider()
        self._reachable: bool | None = None

    def available(self) -> bool:
        if self._reachable is False:
            return False
        try:
            response = httpx.get(f"{self.settings.ollama_url}/api/tags", timeout=2.0)
            self._reachable = response.status_code == 200
            if self._reachable:
                models = [m.get("name", "") for m in response.json().get("models", [])]
                if models and not any(self.settings.ollama_model.split(":")[0] in m for m in models):
                    logger.warning("Ollama is running but model %s is not pulled", self.settings.ollama_model)
        except (httpx.HTTPError, ValueError) as exc:
            logger.info("Ollama unavailable (%s); falling back to local provider", exc)
            self._reachable = False
        return bool(self._reachable)

    def capabilities(self) -> set[Capability]:
        return {"generate_items", "generate_explanation", "generate_hints", "analyse_session", "reword"}

    def _chat(self, messages: list[dict[str, str]], *, json_mode: bool = True) -> str | None:
        payload: dict[str, Any] = {
            "model": self.settings.ollama_model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": 1200},
        }
        if json_mode:
            payload["format"] = "json"
        try:
            response = httpx.post(
                f"{self.settings.ollama_url}/api/chat",
                json=payload,
                timeout=self.settings.ollama_timeout_s,
            )
            response.raise_for_status()
            return response.json()["message"]["content"]
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            logger.warning("Ollama request failed: %s", exc)
            self._reachable = False
            return None

    def generate_items(self, facts: Sequence[FactInput], spec: GenerationSpec) -> list[GeneratedItem]:
        if not self.available():
            return self.fallback.generate_items(facts, spec)

        user_prompt = _build_prompt(facts, spec)
        content = self._chat([{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_prompt}])
        if content is None:
            return self.fallback.generate_items(facts, spec)

        parsed = _parse_items(content)
        if parsed is None:
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
        if not self.available():
            return self.fallback.generate_explanation(item, facts)
        content = self._chat(
            [
                {"role": "system", "content": "Explain a Class 10 answer in at most two sentences. Use only the facts given. Reply in JSON: {\"explanation\": str}"},
                {"role": "user", "content": json.dumps({"item": item, "facts": [_fact_dict(f) for f in facts]}, ensure_ascii=False)},
            ]
        )
        if not content:
            return self.fallback.generate_explanation(item, facts)
        try:
            return json.loads(content).get("explanation")
        except (json.JSONDecodeError, AttributeError):
            return None

    def generate_hints(self, item: dict[str, Any], facts: Sequence[FactInput]) -> list[str]:
        if not self.available():
            return self.fallback.generate_hints(item, facts)
        content = self._chat(
            [
                {"role": "system", "content": "Write up to 3 short hints that guide a student without giving the answer. Reply in JSON: {\"hints\": [str]}"},
                {"role": "user", "content": json.dumps(item, ensure_ascii=False)},
            ]
        )
        if not content:
            return self.fallback.generate_hints(item, facts)
        try:
            hints = json.loads(content).get("hints", [])
            return [str(h) for h in hints][:3]
        except (json.JSONDecodeError, AttributeError):
            return []

    def analyse_session(self, session: dict[str, Any]) -> Insights:
        # Session insight is cheap and deterministic locally; no model call needed.
        return self.fallback.analyse_session(session)


def _fact_dict(fact: FactInput) -> dict[str, Any]:
    return {"id": fact.id, "kind": fact.kind, "label": fact.label, "payload": fact.payload}


def _build_prompt(facts: Sequence[FactInput], spec: GenerationSpec) -> str:
    return json.dumps(
        {
            "task": f"Generate {spec.count} {spec.difficulty} MCQ(s) for Class 10.",
            "chapter_id": spec.chapter_id,
            "topic_id": spec.topic_id,
            "extra_instructions": spec.extra_instructions,
            "approved_facts": [_fact_dict(f) for f in facts],
        },
        ensure_ascii=False,
    )


def _parse_items(content: str) -> list[dict[str, Any]] | None:
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        # Tolerate a wrapped object like {"items": [...]}
        try:
            start, end = content.index("["), content.rindex("]") + 1
            data = json.loads(content[start:end])
        except (ValueError, json.JSONDecodeError):
            return None

    if isinstance(data, dict):
        data = data.get("items") or data.get("questions") or []
    return data if isinstance(data, list) else None
