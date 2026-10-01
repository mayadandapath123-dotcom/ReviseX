"""Sequence facts -> 'correct order' questions with plausible permuted distractors."""

from __future__ import annotations

from typing import Any, Sequence

from app.content.generators.base import (
    build_options,
    make_question,
    question_id,
    resolve_location,
    slugify,
    stable_rng,
)
from app.content.schema import QuestionDef
from app.content.validators import content_hash

ARROW = " \u2192 "


def generate(items: Sequence[dict[str, Any]], chapter: str, topic: str, source_ref: str) -> list[QuestionDef]:
    questions: list[QuestionDef] = []

    for item in items:
        sequence = [str(step).strip() for step in item.get("sequence", [])]
        if len(sequence) < 3:
            continue

        name = str(item.get("name", "the process"))
        item_chapter, item_topic = resolve_location(item, chapter, topic)
        difficulty = str(item.get("difficulty", "medium"))
        slug = slugify(name)
        correct_text = ARROW.join(sequence)

        rng = stable_rng("sequence", name, item_chapter)
        distractor_texts = _permutations(sequence, rng)
        if len(distractor_texts) < 3:
            continue

        options, answer_key = build_options(correct_text, distractor_texts[:3], rng)
        questions.append(
            make_question(
                qid=question_id(item_chapter, item_topic, "correct_sequence", slug),
                chapter=item_chapter,
                topic=item_topic,
                question_type="mcq_single",
                prompt=f"Choose the correct order for: {name}",
                stimulus={"kind": "sequence", "steps": sequence},
                options=options,
                answer_key=answer_key,
                explanation=f"Correct order: {correct_text}",
                difficulty=difficulty,
                time_budget_ms=20000,
                source_ref=source_ref,
                tags=["sequence", "order", "recall"],
            )
        )

    return _dedupe(questions)


def _permutations(sequence: Sequence[str], rng) -> list[str]:
    """Three near-miss orders: adjacent swap, middle rotation, ends swapped."""
    variants: list[list[str]] = []

    if len(sequence) >= 2:
        swapped = list(sequence)
        index = rng.randrange(len(swapped) - 1)
        swapped[index], swapped[index + 1] = swapped[index + 1], swapped[index]
        variants.append(swapped)

    if len(sequence) >= 3:
        rotated = list(sequence)
        rotated[1], rotated[-1] = rotated[-1], rotated[1]
        variants.append(rotated)

    if len(sequence) >= 4:
        reversed_ends = list(sequence)
        reversed_ends[0], reversed_ends[-1] = reversed_ends[-1], reversed_ends[0]
        variants.append(reversed_ends)

    texts: list[str] = []
    seen = {ARROW.join(sequence)}
    for variant in variants:
        text = ARROW.join(variant)
        if text in seen:
            continue
        seen.add(text)
        texts.append(text)

    # Fill remaining slots with random shuffles that differ from the answer.
    attempts = 0
    while len(texts) < 3 and attempts < 20:
        attempts += 1
        shuffled = list(sequence)
        rng.shuffle(shuffled)
        text = ARROW.join(shuffled)
        if text in seen:
            continue
        seen.add(text)
        texts.append(text)

    return texts


def _dedupe(questions: list[QuestionDef]) -> list[QuestionDef]:
    seen: set[str] = set()
    out: list[QuestionDef] = []
    for question in questions:
        digest = content_hash(question)
        if digest in seen:
            continue
        seen.add(digest)
        out.append(question)
    return out
