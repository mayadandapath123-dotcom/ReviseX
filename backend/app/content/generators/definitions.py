"""Definition facts -> term/definition recall and negative-recall items."""

from __future__ import annotations

from typing import Any, Sequence

from app.content.generators.base import (
    resolve_location,
    build_options,
    make_question,
    pick_distractors,
    question_id,
    slugify,
    stable_rng,
)
from app.content.schema import QuestionDef
from app.content.validators import content_hash


def generate(items: Sequence[dict[str, Any]], chapter: str, topic: str, source_ref: str) -> list[QuestionDef]:
    questions: list[QuestionDef] = []

    terms = [str(i["term"]) for i in items]
    definitions = [str(i["definition"]) for i in items]

    for item in items:
        term = str(item["term"])
        definition = str(item["definition"])
        item_chapter, item_topic = resolve_location(item, chapter, topic)
        difficulty = str(item.get("difficulty", "easy"))
        slug = slugify(term)

        # 1. Term -> definition (distractors are other definitions from the same subject pool)
        rng = stable_rng("def-of", term, item_chapter)
        distractors = pick_distractors(definition, definitions, 3, rng)
        options, answer_key = build_options(definition, distractors, rng)
        questions.append(
            make_question(
                qid=question_id(item_chapter, item_topic, "definition_of_term", slug),
                chapter=item_chapter,
                topic=item_topic,
                question_type="mcq_single",
                prompt=f"What is meant by '{term}'?",
                options=options,
                answer_key=answer_key,
                explanation=f"{term}: {definition}",
                difficulty=difficulty,
                time_budget_ms=15000,
                source_ref=source_ref,
                tags=["definition", "recall"],
            )
        )

        # 2. Definition -> term (fast recall; short options keep the pace up)
        rng = stable_rng("term-of", definition[:40], item_chapter)
        distractors = pick_distractors(term, terms, 3, rng)
        options, answer_key = build_options(term, distractors, rng)
        questions.append(
            make_question(
                qid=question_id(item_chapter, item_topic, "term_of_definition", slug),
                chapter=item_chapter,
                topic=item_topic,
                question_type="mcq_single",
                prompt=f"Which term is defined as: \"{definition}\"",
                options=options,
                answer_key=answer_key,
                explanation=f"That definition belongs to '{term}'.",
                difficulty=difficulty,
                time_budget_ms=13000,
                source_ref=source_ref,
                tags=["definition", "recall"],
            )
        )

    return _dedupe(questions)


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
