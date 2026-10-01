"""Physics formula facts -> recognition, variable, unit and numerical speed drills.

Numerical items generate distractors from *classic calculation mistakes*
(wrong operation, cm/m conversion slip, dropping one resistor) rather than
random numbers, as required by the anti-guessing rule.
"""

from __future__ import annotations

import hashlib

from typing import Any, Sequence

from app.content.generators.base import (
    resolve_location,
    build_options,
    make_question,
    numeric_distractors,
    pick_distractors,
    question_id,
    slugify,
    stable_rng,
    unique_preserving_order,
)
from app.content.schema import QuestionDef
from app.content.validators import content_hash

NUMERIC_VARIANTS = 6


def generate(items: Sequence[dict[str, Any]], chapter: str, topic: str, source_ref: str) -> list[QuestionDef]:
    questions: list[QuestionDef] = []

    formulas = unique_preserving_order(str(i["formula"]) for i in items)
    units = unique_preserving_order(str(i["si_unit"]).split(",")[0].strip() for i in items if i.get("si_unit"))

    for item in items:
        quantity = str(item["quantity"])
        formula = str(item["formula"])
        item_chapter, item_topic = resolve_location(item, chapter, topic)
        difficulty = str(item.get("difficulty", "medium"))
        slug = slugify(quantity)
        variables: dict[str, str] = item.get("variables") or {}
        si_unit = str(item.get("si_unit") or "").split(",")[0].strip()

        # 1. Quantity -> formula
        if len(formulas) >= 4:
            rng = stable_rng("formula-of", quantity, item_chapter)
            distractors = pick_distractors(formula, formulas, 3, rng)
            options, answer_key = build_options(formula, distractors, rng)
            questions.append(
                make_question(
                    qid=question_id(item_chapter, item_topic, "formula_of_quantity", slug),
                    chapter=item_chapter,
                    topic=item_topic,
                    question_type="mcq_single",
                    prompt=f"Which relation is used to calculate {quantity.lower()}?",
                    stimulus={"kind": "formula", "formula": formula},
                    options=options,
                    answer_key=answer_key,
                    explanation=f"{quantity}: {formula}",
                    difficulty=difficulty,
                    time_budget_ms=12000,
                    source_ref=source_ref,
                    tags=["formula", "recall", "physics"],
                )
            )

        # 2. Formula -> quantity
        if len(formulas) >= 4:
            quantities = unique_preserving_order(str(i["quantity"]) for i in items)
            rng = stable_rng("quantity-of", formula, item_chapter)
            distractors = pick_distractors(quantity, quantities, 3, rng)
            options, answer_key = build_options(quantity, distractors, rng)
            questions.append(
                make_question(
                    qid=question_id(item_chapter, item_topic, "quantity_of_formula", slug),
                    chapter=item_chapter,
                    topic=item_topic,
                    question_type="mcq_single",
                    prompt=f"The relation {formula} is used to find:",
                    stimulus={"kind": "formula", "formula": formula},
                    options=options,
                    answer_key=answer_key,
                    explanation=f"{formula} gives {quantity.lower()}.",
                    difficulty=difficulty,
                    time_budget_ms=11000,
                    source_ref=source_ref,
                    tags=["formula", "recall", "physics"],
                )
            )

        # 3. Variable identification
        for symbol, meaning in list(variables.items())[:2]:
            meanings = unique_preserving_order(str(v) for i in items for v in (i.get("variables") or {}).values())
            if len(meanings) < 4:
                continue
            # "h'" and "h" are different quantities in the same formula, but
            # slugify strips the prime, so both minted the id "...-h" and one of
            # the two questions was silently dropped. Digest the raw symbol
            # whenever it carries punctuation the slug cannot represent.
            symbol_tag = slugify(symbol, 12)
            if not symbol.replace(" ", "").isalnum():
                symbol_tag = f"{symbol_tag}-{hashlib.sha1(symbol.encode('utf-8')).hexdigest()[:4]}"
            rng = stable_rng("variable", quantity, symbol, item_chapter)
            distractors = pick_distractors(str(meaning), meanings, 3, rng)
            options, answer_key = build_options(str(meaning), distractors, rng)
            questions.append(
                make_question(
                    qid=question_id(item_chapter, item_topic, "variable_in_formula", f"{slug}-{symbol_tag}"),
                    chapter=item_chapter,
                    topic=item_topic,
                    question_type="mcq_single",
                    prompt=f'In {formula}, what does "{symbol}" represent?',
                    stimulus={"kind": "formula", "formula": formula},
                    options=options,
                    answer_key=answer_key,
                    explanation=f"In {formula}, {symbol} is the {meaning}.",
                    difficulty="medium",
                    time_budget_ms=12000,
                    source_ref=source_ref,
                    tags=["formula", "variable", "physics"],
                )
            )

        # 4. SI unit
        if si_unit and len(units) >= 4:
            rng = stable_rng("unit", quantity, item_chapter)
            distractors = pick_distractors(si_unit, units, 3, rng)
            options, answer_key = build_options(si_unit, distractors, rng)
            questions.append(
                make_question(
                    qid=question_id(item_chapter, item_topic, "si_unit_of_quantity", slug),
                    chapter=item_chapter,
                    topic=item_topic,
                    question_type="mcq_single",
                    prompt=f"What is the SI unit of {quantity.lower()}?",
                    options=options,
                    answer_key=answer_key,
                    explanation=f"{quantity} is measured in {si_unit}.",
                    difficulty="easy",
                    time_budget_ms=8000,
                    source_ref=source_ref,
                    tags=["unit", "recall", "physics"],
                )
            )

        # 5. Numerical speed drills
        if item.get("numeric"):
            questions.extend(_numerical_variants(item, item_chapter, item_topic, source_ref))

    return _dedupe(questions)


def _numerical_variants(item: dict[str, Any], item_chapter: str, item_topic: str, source_ref: str) -> list[QuestionDef]:
    spec = item["numeric"]
    kind = str(spec["kind"])
    quantity = str(item["quantity"])
    formula = str(item["formula"])
    slug = slugify(quantity)
    out: list[QuestionDef] = []

    for index in range(NUMERIC_VARIANTS):
        rng = stable_rng("numeric", quantity, kind, str(index))
        built = _build_numeric(kind, spec, rng)
        if built is None:
            continue
        prompt, correct_value, fmt, explanation = built

        distractors = _mistake_distractors(kind, spec, correct_value, rng, fmt)
        options, answer_key = build_options(_fmt(correct_value, fmt), distractors, rng)
        out.append(
            make_question(
                qid=question_id(item_chapter, item_topic, "numerical", f"{slug}-{index}"),
                chapter=item_chapter,
                topic=item_topic,
                question_type="mcq_single",
                prompt=prompt,
                stimulus={"kind": "formula", "formula": formula},
                options=options,
                answer_key=answer_key,
                explanation=f"Using {formula}: {explanation}",
                difficulty="medium",
                time_budget_ms=25000,
                source_ref=source_ref,
                tags=["numerical", "calculation", "physics", "formula"],
            )
        )
    return out


def _build_numeric(kind: str, spec: dict[str, Any], rng) -> tuple[str, float, str, str] | None:
    a_unit = str(spec.get("a_unit", ""))
    b_unit = str(spec.get("b_unit", ""))
    target = str(spec.get("target", "?"))

    if kind == "divide":
        b = rng.choice([2, 4, 5, 10, 20, 25])
        result = rng.choice([2, 3, 4, 5, 6, 8, 10, 12])
        a = b * result
        return (
            f"If {spec.get('a', 'A')} = {a} {a_unit} and {spec.get('b', 'B')} = {b} {b_unit}, find {target}.",
            float(result),
            "{}" + (f" {spec.get('target_unit', '')}".strip() if spec.get("target_unit") else ""),
            f"{target} = {a} / {b} = {result}",
        )

    if kind == "multiply":
        a = rng.choice([2, 3, 4, 5, 6, 8, 10, 12])
        b = rng.choice([2, 3, 4, 5, 6, 8, 10, 15, 20])
        return (
            f"If {spec.get('a', 'A')} = {a} {a_unit} and {spec.get('b', 'B')} = {b} {b_unit}, find {target}.",
            float(a * b),
            "{}",
            f"{target} = {a} x {b} = {a * b}",
        )

    if kind == "multiply2":
        a = rng.choice([5, 10, 15, 20, 25, 30])
        return (
            f"A spherical mirror has focal length {a} cm. What is its radius of curvature?",
            float(a * 2),
            "{} cm",
            f"R = 2f = 2 x {a} = {a * 2} cm",
        )

    if kind == "reciprocal":
        focal_cm = rng.choice([10, 20, 25, 40, 50, 100, 200])
        focal_m = focal_cm / 100
        power = 1 / focal_m
        return (
            f"A lens has a focal length of {focal_cm} cm. What is its power?",
            float(power),
            "{} D",
            f"f = {focal_cm} cm = {focal_m} m, so P = 1/f = {power:g} D",
        )

    if kind == "series":
        values = rng.sample([2, 3, 4, 5, 6, 8, 10, 12, 15, 20], 3)
        total = sum(values)
        return (
            f"Three resistors of {values[0]} \u03a9, {values[1]} \u03a9 and {values[2]} \u03a9 are connected in series. What is the equivalent resistance?",
            float(total),
            "{} \u03a9",
            f"Rs = {values[0]} + {values[1]} + {values[2]} = {total} \u03a9",
        )

    return None


def _mistake_distractors(kind: str, spec: dict[str, Any], correct: float, rng, fmt: str) -> list[str]:
    """Distractors built from the mistakes students actually make."""
    mistakes: list[float] = []

    if kind == "divide":
        a_unit = str(spec.get("a_unit", ""))
        mistakes += [correct * 10, correct / 10 if correct else 1, correct + 1, correct - 1]
        # Reversed operation: b/a instead of a/b
        mistakes.append(1 / correct if correct else 1)
    elif kind == "multiply":
        mistakes += [correct + 10, correct - 10, correct * 10, correct / 10 if correct else 1]
    elif kind == "multiply2":
        mistakes += [correct / 2, correct * 2, correct + 10, correct - 10]
    elif kind == "reciprocal":
        # The classic cm/m slip: 1/f_cm instead of 1/f_m
        mistakes += [correct / 100, correct * 10, -correct, correct + 1]
    elif kind == "series":
        # Treating it as parallel, or forgetting one resistor
        mistakes += [correct * 2, round(correct / 2, 1), correct - rng.choice([2, 3, 4, 5]), correct + rng.choice([2, 3, 4, 5])]

    seen = {_fmt(correct, fmt)}
    out: list[str] = []
    for value in mistakes:
        text = _fmt(value, fmt)
        if text in seen:
            continue
        seen.add(text)
        out.append(text)

    if len(out) < 3:
        out.extend(numeric_distractors(correct, rng, fmt))

    rng.shuffle(out)
    return list(dict.fromkeys(out))[:3]


def _fmt(value: float, fmt: str) -> str:
    if abs(value - round(value)) < 1e-9:
        return fmt.format(int(round(value)))
    return fmt.format(round(value, 2))


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
