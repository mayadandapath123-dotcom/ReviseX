"""LocalAIProvider — zero-dependency, zero-cost, always available.

Deterministic templates over approved facts. It cannot hallucinate because it can
only ever emit values that already exist in the fact payload it was given.
"""

from __future__ import annotations

from typing import Any, Sequence

from app.ai.base import AIProvider, Capability, FactInput, GeneratedItem, GenerationSpec, Insights
from app.content.generators.base import slugify, stable_rng

PROMPT_TEMPLATES = {
    "element": [
        "What is the valency of {name} ({symbol})?",
        "Quick recall — valency of {symbol}?",
        "{name} combines with how many hydrogen atoms?",
    ],
    "formula": [
        "Which formula represents {name}?",
        "Pick the correct formula for {name}.",
        "{name} is written as:",
    ],
    "definition": [
        "What does '{term}' mean?",
        "Choose the correct definition of '{term}'.",
        "'{term}' refers to:",
    ],
    "fact": [
        "What is the {attribute} of {subject}?",
        "{subject} — {attribute}?",
        "Select the correct value: {subject}, {attribute}.",
    ],
    "reaction": [
        "Which type of reaction is '{name}'?",
        "Classify this reaction: {name}.",
        "'{name}' is an example of which reaction type?",
    ],
    "physics_formula": [
        "Which relation gives {quantity}?",
        "How is {quantity} calculated?",
        "Choose the formula for {quantity}.",
    ],
}


class LocalAIProvider:
    name = "local"

    def available(self) -> bool:
        return True

    def capabilities(self) -> set[Capability]:
        return {"generate_items", "generate_explanation", "generate_hints", "analyse_session", "reword"}

    def generate_items(self, facts: Sequence[FactInput], spec: GenerationSpec) -> list[GeneratedItem]:
        """Reword existing knowledge into alternative prompts + option sets.

        Distractors come from sibling facts of the same kind, never from invention.
        """
        out: list[GeneratedItem] = []
        if not facts:
            return out

        siblings = _group_siblings(facts)

        for fact in facts:
            if len(out) >= spec.count:
                break
            template_pool = PROMPT_TEMPLATES.get(fact.kind) or PROMPT_TEMPLATES["fact"]
            rng = stable_rng("local-ai", fact.id, spec.difficulty)

            values = _answer_and_pool(fact, siblings)
            if values is None:
                continue
            correct, pool = values

            template = rng.choice(template_pool)
            prompt = _render(template, fact)
            distractors = [p for p in pool if str(p).lower() != str(correct).lower()][:3]
            if len(distractors) < 3:
                continue

            options = [str(correct), *distractors]
            rng.shuffle(options)

            out.append(
                GeneratedItem(
                    prompt=prompt,
                    options=options,
                    answer_index=options.index(str(correct)),
                    question_type="mcq_single",
                    difficulty=spec.difficulty,
                    explanation=_render("{label}: " + str(correct), fact),
                    hint=None,
                    time_budget_ms=12000,
                    fact_ids=[fact.id],
                    provider=self.name,
                    raw={"template": template, "kind": fact.kind},
                )
            )

        return out

    def generate_explanation(self, item: dict[str, Any], facts: Sequence[FactInput]) -> str | None:
        correct = item.get("answer_text") or item.get("correct_answer")
        label = item.get("topic_name") or item.get("prompt", "")[:60]
        if not correct:
            return None
        return f"{label} — the correct value is {correct}."

    def generate_hints(self, item: dict[str, Any], facts: Sequence[FactInput]) -> list[str]:
        options = item.get("options") or []
        hints: list[str] = []
        answer = item.get("answer_text")
        if answer:
            hints.append(f"The answer starts with '{str(answer)[0]}'.")
        if len(options) >= 2:
            hints.append("Eliminate the two options you are sure about first.")
        topic = item.get("topic_name")
        if topic:
            hints.append(f"This is from the topic '{topic}'.")
        return hints[:3]

    def analyse_session(self, session: dict[str, Any]) -> Insights:
        weak = session.get("weak_areas") or []
        strong = session.get("strong_areas") or []

        if weak:
            names = ", ".join(str(w.get("name") or w.get("topic_id")) for w in weak[:3])
            narrative = f"You slipped most on {names}. Run a Topic Test on these before your next mix."
            suggested = ["topic_test", "weak_topics", "previous_mistakes"]
        elif strong:
            narrative = "Strong session. Raise the difficulty or switch to a new chapter to keep progressing."
            suggested = ["chapter_test", "rush_120s", "exam_simulation"]
        else:
            narrative = "Not enough data yet — answer a few more questions to unlock personalised suggestions."
            suggested = ["rush_60s"]

        return Insights(weak_topics=weak, narrative=narrative, suggested_modes=suggested, provider=self.name)


def _group_siblings(facts: Sequence[FactInput]) -> dict[str, dict[str, list[str]]]:
    """kind -> attribute/field -> list of values across sibling facts."""
    grouped: dict[str, dict[str, list[str]]] = {}
    for fact in facts:
        bucket = grouped.setdefault(fact.kind, {})
        for key, value in _candidate_fields(fact):
            bucket.setdefault(key, [])
            if str(value) not in bucket[key]:
                bucket[key].append(str(value))
    return grouped


def _candidate_fields(fact: FactInput) -> list[tuple[str, Any]]:
    payload = fact.payload or {}
    if fact.kind == "element":
        return [("valency", payload.get("valencies", [None])[0]), ("symbol", payload.get("symbol")), ("name", payload.get("name"))]
    if fact.kind == "formula":
        return [("formula", payload.get("formula")), ("name", payload.get("name"))]
    if fact.kind == "definition":
        return [("definition", payload.get("definition")), ("term", payload.get("term"))]
    if fact.kind == "fact":
        attribute = str(payload.get("attribute", "value"))
        return [(attribute, payload.get("value"))]
    if fact.kind == "physics_formula":
        return [("formula", payload.get("formula")), ("quantity", payload.get("quantity")), ("si_unit", payload.get("si_unit"))]
    return [("value", payload.get("value"))]


def _answer_and_pool(fact: FactInput, siblings: dict[str, dict[str, list[str]]]) -> tuple[Any, list[str]] | None:
    payload = fact.payload or {}
    bucket = siblings.get(fact.kind, {})

    if fact.kind == "element" and payload.get("valencies"):
        correct = str(payload["valencies"][0])
        return correct, bucket.get("valency", [])
    if fact.kind == "formula" and payload.get("formula"):
        return str(payload["formula"]), bucket.get("formula", [])
    if fact.kind == "definition" and payload.get("definition"):
        return str(payload["definition"]), bucket.get("definition", [])
    if fact.kind == "fact" and payload.get("value") is not None:
        attribute = str(payload.get("attribute", "value"))
        return str(payload["value"]), bucket.get(attribute, [])
    if fact.kind == "physics_formula" and payload.get("formula"):
        return str(payload["formula"]), bucket.get("formula", [])
    return None


def _render(template: str, fact: FactInput) -> str:
    payload = dict(fact.payload or {})
    payload.setdefault("label", fact.label)
    payload.setdefault("name", fact.label)
    payload.setdefault("term", fact.label)
    payload.setdefault("subject", fact.label)
    try:
        return template.format(**payload)
    except (KeyError, IndexError):
        return template


__all__ = ["LocalAIProvider", "slugify"]
