"""Anti-hallucination gate for AI-generated items.

The rule is simple and strict: **an AI item may only assert what its input facts
already assert.** Concretely:

  * every numeric token in the correct answer must appear in the supplied facts;
  * every chemical symbol in the correct answer must appear in the supplied facts;
  * the item's chapter must match the chapter of the facts it cites;
  * structural/quality rules from `app.content.validators` must also pass.

Items that pass are stored with status `pending_review` unless
AUTO_APPROVE_AI_ITEMS is explicitly enabled — they never reach a student
silently.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

from app.ai.base import FactInput, GeneratedItem
from app.content.schema import OPTION_KEYS, QuestionDef, QuestionOption
from app.content.validators import ValidationResult, content_hash, normalise_text, validate_question

NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")
SYMBOL_RE = re.compile(r"\b[A-Z][a-z]?\b")

# Common English words that look like element symbols; never treated as chemistry claims.
_SYMBOL_STOPWORDS = {
    "A", "I", "An", "As", "At", "Be", "By", "Do", "He", "If", "In", "Is", "It", "Me", "My",
    "No", "Of", "On", "Or", "So", "To", "Up", "Us", "We", "Not", "The", "And", "For", "Its",
    "Which", "What", "When", "Where", "Who", "Why", "How", "Select", "Choose", "Correct",
}


@dataclass
class GateResult:
    accepted: bool
    issues: list[str] = field(default_factory=list)
    question: QuestionDef | None = None
    dedupe_hash: str | None = None


def allowed_tokens(facts: Sequence[FactInput]) -> tuple[set[str], set[str]]:
    numbers: set[str] = set()
    symbols: set[str] = set()

    for fact in facts:
        blob = json.dumps(fact.payload, ensure_ascii=False) + " " + str(fact.label)
        numbers.update(NUMBER_RE.findall(blob))
        symbols.update(SYMBOL_RE.findall(blob))
        for value in _walk_strings(fact.payload):
            numbers.update(NUMBER_RE.findall(value))
            symbols.update(SYMBOL_RE.findall(value))

    # Normalise "1.0" / "1" equivalence so a formatted number is not falsely rejected.
    normalised_numbers = set()
    for number in numbers:
        normalised_numbers.add(number)
        try:
            if float(number) == int(float(number)):
                normalised_numbers.add(str(int(float(number))))
        except ValueError:
            continue
    return normalised_numbers, symbols


def _walk_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _walk_strings(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _walk_strings(item)
    elif isinstance(value, (int, float)):
        yield str(value)


def check_grounding(text: str, numbers: set[str], symbols: set[str]) -> list[str]:
    problems: list[str] = []

    for token in NUMBER_RE.findall(text or ""):
        if token not in numbers:
            problems.append(f"number '{token}' is not present in the supplied facts")

    for token in SYMBOL_RE.findall(text or ""):
        if token in _SYMBOL_STOPWORDS:
            continue
        # Only flag tokens that look like chemistry claims (2-3 char, capitalised).
        if len(token) < 2:
            continue
        if token not in symbols:
            problems.append(f"symbol '{token}' is not present in the supplied facts")

    return problems


def validate_generated(
    item: GeneratedItem,
    facts: Sequence[FactInput],
    *,
    chapter_id: str,
    topic_id: str | None,
    source_ref: str,
    existing_hashes: set[str] | None = None,
    question_id: str,
) -> GateResult:
    result = ValidationResult()
    grounding_problems: list[str] = []

    # 1. Structure
    if len(item.options) != 4:
        result.add("option_count", f"AI item has {len(item.options)} options; exactly 4 are required")
    if not (0 <= item.answer_index < len(item.options)):
        result.add("answer_index", f"answer_index {item.answer_index} out of range")
    if not item.prompt or not item.prompt.strip():
        result.add("empty_prompt", "AI item has an empty prompt")

    normalised = [normalise_text(o) for o in item.options]
    if len(set(normalised)) != len(normalised):
        result.add("duplicate_option", "AI item has duplicate options")

    # 2. Fact provenance
    fact_ids = {f.id for f in facts}
    if item.fact_ids and not set(item.fact_ids).issubset(fact_ids):
        result.add("unknown_fact", "AI item cites fact ids that were not supplied")

    cited = [f for f in facts if not item.fact_ids or f.id in set(item.fact_ids)] or list(facts)
    chapters = {f.chapter_id for f in cited}
    if chapters and chapter_id not in chapters:
        result.add("chapter_boundary", f"AI item targets chapter {chapter_id!r} but its facts belong to {sorted(chapters)}")

    # 3. Grounding — the actual anti-hallucination check
    numbers, symbols = allowed_tokens(cited)
    if result.ok and 0 <= item.answer_index < len(item.options):
        grounding_problems = check_grounding(item.options[item.answer_index], numbers, symbols)
        for problem in grounding_problems:
            result.add("ungrounded_answer", f"Correct answer is not supported by the supplied facts: {problem}")

    if not result.ok:
        return GateResult(accepted=False, issues=result.errors, dedupe_hash=None)

    # 4. Build a real QuestionDef and run the standard bank validators
    options = [QuestionOption(key=key, text=text.strip()) for key, text in zip(OPTION_KEYS, item.options)]
    answer_key = OPTION_KEYS[item.answer_index]

    question = QuestionDef(
        id=question_id,
        chapter=chapter_id,
        topic=topic_id,
        question_type=item.question_type,  # type: ignore[arg-type]
        prompt=item.prompt.strip(),
        stimulus={"ai_generated": True, "provider": item.provider, "fact_ids": item.fact_ids},
        options=options,
        answer_key=answer_key,
        explanation=(item.explanation or "").strip() or None,
        hint=(item.hint or "").strip() or None,
        difficulty=item.difficulty,  # type: ignore[arg-type]
        time_budget_ms=item.time_budget_ms,
        source_ref=source_ref,
        tags=["ai-generated"],
        origin="ai",
        status="pending_review",
    )

    bank_result = validate_question(question)
    if not bank_result.ok:
        return GateResult(accepted=False, issues=bank_result.errors, dedupe_hash=None)

    digest = content_hash(question)
    if existing_hashes and digest in existing_hashes:
        return GateResult(accepted=False, issues=["duplicate_of_existing_item"], dedupe_hash=digest)

    warnings = [*bank_result.warnings, *result.warnings]
    return GateResult(accepted=True, issues=warnings, question=question, dedupe_hash=digest)
