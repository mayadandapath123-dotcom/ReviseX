"""Chemical formula facts -> recognition and category questions."""

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
    unique_preserving_order,
)
from app.content.schema import QuestionDef
from app.content.validators import content_hash

CATEGORY_LABEL = {
    "acid": "an acid",
    "base": "a base",
    "salt": "a salt",
    "oxide": "an oxide",
    "organic": "an organic compound",
    "element_gas": "a gaseous element",
}


def generate(items: Sequence[dict[str, Any]], chapter: str, topic: str, source_ref: str) -> list[QuestionDef]:
    questions: list[QuestionDef] = []

    formulas = unique_preserving_order(str(i["formula"]) for i in items)
    names = unique_preserving_order(str(i["name"]) for i in items)

    for item in items:
        formula = str(item["formula"])
        name = str(item["name"])
        item_chapter, item_topic = resolve_location(item, chapter, topic)
        common_name = item.get("common_name")
        category = str(item.get("category", "salt"))
        slug = slugify(f"{formula}-{item.get('dedupe_suffix', '')}".strip("-"))

        # 1. Name -> formula
        rng = stable_rng("formula-of", name, item_chapter)
        distractors = pick_distractors(formula, formulas, 3, rng)
        options, answer_key = build_options(formula, distractors, rng)
        questions.append(
            make_question(
                qid=question_id(item_chapter, item_topic, "formula_of_compound", slug),
                chapter=item_chapter,
                topic=item_topic,
                question_type="mcq_single",
                prompt=f"What is the chemical formula of {name}?",
                options=options,
                answer_key=answer_key,
                explanation=f"{name} is written as {formula}.",
                difficulty="easy",
                time_budget_ms=9000,
                source_ref=source_ref,
                tags=["formula", "recall"],
            )
        )

        # 2. Formula -> name
        rng = stable_rng("name-of-formula", formula, item_chapter)
        distractors = pick_distractors(name, names, 3, rng)
        options, answer_key = build_options(name, distractors, rng)
        questions.append(
            make_question(
                qid=question_id(item_chapter, item_topic, "compound_of_formula", slug),
                chapter=item_chapter,
                topic=item_topic,
                question_type="mcq_single",
                prompt=f"Identify the compound: {formula}",
                stimulus={"kind": "formula", "formula": formula},
                options=options,
                answer_key=answer_key,
                explanation=f"{formula} is {name}.",
                difficulty="easy",
                time_budget_ms=8000,
                source_ref=source_ref,
                tags=["formula", "recall"],
            )
        )

        # 3. Common name link (only where one exists)
        if common_name:
            rng = stable_rng("common-name", formula, item_chapter)
            distractors = pick_distractors(str(common_name), [str(i["common_name"]) for i in items if i.get("common_name")], 3, rng)
            options, answer_key = build_options(str(common_name), distractors, rng)
            questions.append(
                make_question(
                    qid=question_id(item_chapter, item_topic, "common_name_of_formula", slug),
                    chapter=item_chapter,
                    topic=item_topic,
                    question_type="mcq_single",
                    prompt=f"{formula} is commonly known as:",
                    stimulus={"kind": "formula", "formula": formula},
                    options=options,
                    answer_key=answer_key,
                    explanation=f"{formula} ({name}) is commonly called {common_name}.",
                    difficulty="medium",
                    time_budget_ms=10000,
                    source_ref=source_ref,
                    tags=["formula", "recall", "nomenclature"],
                )
            )

        # 4. Category classification
        if category in CATEGORY_LABEL and len({i.get("category") for i in items}) >= 4:
            rng = stable_rng("category", formula, item_chapter)
            pool = [CATEGORY_LABEL[str(i.get("category"))] for i in items if str(i.get("category")) in CATEGORY_LABEL]
            correct = CATEGORY_LABEL[category]
            distractors = pick_distractors(correct, pool, 3, rng)
            options, answer_key = build_options(correct, distractors, rng)
            questions.append(
                make_question(
                    qid=question_id(item_chapter, item_topic, "category_of_formula", slug),
                    chapter=item_chapter,
                    topic=item_topic,
                    question_type="mcq_single",
                    prompt=f"{formula} ({name}) is:",
                    stimulus={"kind": "formula", "formula": formula},
                    options=options,
                    answer_key=answer_key,
                    explanation=f"{formula} is {correct}.",
                    difficulty="medium",
                    time_budget_ms=9000,
                    source_ref=source_ref,
                    tags=["classification", "application"],
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
