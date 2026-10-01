"""Reaction facts -> type identification, observation, product and heat-effect questions.

Equations shown in these items are balanced by BalancingEngine at generation time,
so a reaction item can never display an unbalanced equation.
"""

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
from app.services.balancing_engine import FormulaError, solve_equation

TYPE_LABEL = {
    "combination": "Combination reaction",
    "decomposition": "Decomposition reaction",
    "photodecomposition": "Photochemical decomposition reaction",
    "electrolytic_decomposition": "Electrolytic decomposition reaction",
    "displacement": "Displacement reaction",
    "double_displacement": "Double displacement reaction",
    "combustion": "Combustion (oxidation) reaction",
    "oxidation": "Oxidation / corrosion-type reaction",
}

HEAT_LABEL = {"exothermic": "Exothermic (releases heat)", "endothermic": "Endothermic (absorbs heat)"}


def generate(items: Sequence[dict[str, Any]], chapter: str, topic: str, source_ref: str) -> list[QuestionDef]:
    questions: list[QuestionDef] = []

    types = unique_preserving_order(TYPE_LABEL[str(i["type"])] for i in items if str(i.get("type")) in TYPE_LABEL)
    observations = [str(i["observation"]) for i in items if i.get("observation")]
    heat_items = [i for i in items if i.get("heat") in HEAT_LABEL]

    for item in items:
        name = str(item["name"])
        item_chapter, item_topic = resolve_location(item, chapter, topic)
        difficulty = str(item.get("difficulty", "medium"))
        reaction_type = TYPE_LABEL.get(str(item.get("type")), "Chemical reaction")
        slug = slugify(name)

        balanced_text: str | None = None
        try:
            equation = solve_equation(item["reactants"], item["products"])
            balanced_text = equation.as_text()
        except FormulaError:
            balanced_text = None

        display = balanced_text or f"{' + '.join(map(str, item['reactants']))} \u2192 {' + '.join(map(str, item['products']))}"
        stimulus = {"kind": "equation", "text": display, "balanced": balanced_text is not None, "name": name}

        # 1. Reaction type identification
        if len(types) >= 4:
            rng = stable_rng("reaction-type", name, item_chapter)
            distractors = pick_distractors(reaction_type, types, 3, rng)
            options, answer_key = build_options(reaction_type, distractors, rng)
            questions.append(
                make_question(
                    qid=question_id(item_chapter, item_topic, "reaction_type", slug),
                    chapter=item_chapter,
                    topic=item_topic,
                    question_type="mcq_single",
                    prompt=f"Identify the type of reaction:\n{display}",
                    stimulus=stimulus,
                    options=options,
                    answer_key=answer_key,
                    explanation=f"{name} is a {reaction_type.lower()}.",
                    difficulty=difficulty,
                    time_budget_ms=14000,
                    source_ref=source_ref,
                    tags=["reaction", "classification"],
                )
            )

        # 2. Observation recall
        observation = item.get("observation")
        if observation and len(observations) >= 4:
            rng = stable_rng("reaction-obs", name, item_chapter)
            distractors = pick_distractors(str(observation), observations, 3, rng)
            options, answer_key = build_options(str(observation), distractors, rng)
            questions.append(
                make_question(
                    qid=question_id(item_chapter, item_topic, "reaction_observation", slug),
                    chapter=item_chapter,
                    topic=item_topic,
                    question_type="mcq_single",
                    prompt=f"What is observed when: {name.lower()}?",
                    stimulus=stimulus,
                    options=options,
                    answer_key=answer_key,
                    explanation=f"{display} — {observation}.",
                    difficulty=difficulty,
                    time_budget_ms=16000,
                    source_ref=source_ref,
                    tags=["reaction", "observation", "practical"],
                )
            )

        # 3. Product identification
        products = [str(p) for p in item.get("products", [])]
        all_products = unique_preserving_order(str(p) for i in items for p in i.get("products", []))
        if products and len(all_products) >= 4:
            rng = stable_rng("reaction-product", name, item_chapter)
            for product in products[:1]:
                distractors = pick_distractors(product, all_products, 3, rng)
                options, answer_key = build_options(product, distractors, rng)
                questions.append(
                    make_question(
                        qid=question_id(item_chapter, item_topic, "reaction_product", slug),
                        chapter=item_chapter,
                        topic=item_topic,
                        question_type="mcq_single",
                        prompt=f"Which of the following is a product of: {name.lower()}?",
                        stimulus=stimulus,
                        options=options,
                        answer_key=answer_key,
                        explanation=f"{display}",
                        difficulty="medium",
                        time_budget_ms=12000,
                        source_ref=source_ref,
                        tags=["reaction", "recall"],
                    )
                )

        # 4. Heat effect
        if item.get("heat") in HEAT_LABEL and len(heat_items) >= 2:
            correct = HEAT_LABEL[str(item["heat"])]
            other = HEAT_LABEL["endothermic" if item["heat"] == "exothermic" else "exothermic"]
            rng = stable_rng("reaction-heat", name, item_chapter)
            fillers = [
                "Neither — no heat change is involved",
                "Depends only on the amount of reactant used",
            ]
            options, answer_key = build_options(correct, [other, *fillers], rng)
            questions.append(
                make_question(
                    qid=question_id(item_chapter, item_topic, "reaction_heat", slug),
                    chapter=item_chapter,
                    topic=item_topic,
                    question_type="mcq_single",
                    prompt=f"Which statement about the heat change is correct?\n{display}",
                    stimulus=stimulus,
                    options=options,
                    answer_key=answer_key,
                    explanation=f"{name} is {correct.lower()}.",
                    difficulty="medium",
                    time_budget_ms=13000,
                    source_ref=source_ref,
                    tags=["reaction", "thermochemistry"],
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
