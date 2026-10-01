"""Balancing equations -> interactive balancing items.

Coefficients are solved here (atom conservation) and stored with the item so the
UI can render an atom table, but grading always re-verifies the student's input
through BalancingEngine.verify() — never by comparing to a stored string.
"""

from __future__ import annotations

from typing import Any, Sequence

from app.content.generators.base import make_question, question_id, resolve_location, slugify, stable_rng
from app.content.schema import QuestionDef
from app.services.balancing_engine import FormulaError, parse_formula, solve_equation
from app.content.validators import content_hash

TIME_BUDGET = {"easy": 45000, "medium": 60000, "hard": 90000}


def generate(items: Sequence[dict[str, Any]], chapter: str, topic: str, source_ref: str) -> list[QuestionDef]:
    questions: list[QuestionDef] = []
    skipped: list[str] = []

    for item in items:
        name = str(item.get("name", "equation"))
        reactants = [str(r) for r in item.get("reactants", [])]
        products = [str(p) for p in item.get("products", [])]
        item_chapter, item_topic = resolve_location(item, chapter, topic)
        difficulty = str(item.get("difficulty", "medium"))

        try:
            equation = solve_equation(reactants, products)
        except FormulaError as exc:
            skipped.append(f"{name}: {exc}")
            continue

        # Atom table so the UI can show live counts while the student adjusts coefficients.
        atom_table = []
        for element in equation.elements:
            left = sum(parse_formula(f).get(element, 0) for f in equation.reactants)
            right = sum(parse_formula(f).get(element, 0) for f in equation.products)
            atom_table.append({"element": element, "in_reactants_formula": left, "in_products_formula": right})

        rng = stable_rng("balancing", name, item_chapter)
        questions.append(
            make_question(
                qid=question_id(item_chapter, item_topic, "balance_equation", slugify(name)),
                chapter=item_chapter,
                topic=item_topic,
                question_type="balancing",
                prompt=f"Balance the chemical equation{f' ({name.lower()})' if name != 'equation' else ''}:",
                options=[],
                answer_key="balanced",
                explanation=f"Balanced form: {equation.as_text()}",
                hint=_hint_for(equation),
                difficulty=difficulty,
                time_budget_ms=TIME_BUDGET.get(difficulty, 60000),
                source_ref=source_ref,
                tags=["balancing", "reaction", "interactive"],
                stimulus={
                    "kind": "equation",
                    "name": name,
                    "reactants": list(equation.reactants),
                    "products": list(equation.products),
                    "solution": list(equation.coefficients),
                    "elements": list(equation.elements),
                    "atom_table": atom_table,
                    "display": equation.as_text(with_coefficients=False),
                    "max_coefficient": 8,
                },
            )
        )

    if skipped:
        # Surfaced by the seeder as a warning so content authors can fix the equation.
        raise BalancingSeedWarning("; ".join(skipped))

    return _dedupe(questions)


def _hint_for(equation) -> str:
    coeffs = list(equation.coefficients)
    # Reveal only the first non-unity coefficient's position, not its value.
    positions = [i + 1 for i, c in enumerate(coeffs) if c != 1]
    if not positions:
        return "Every coefficient is already 1 — check the atom count on both sides."
    start = positions[0]
    return f"You will need a coefficient greater than 1 for substance number {start}. Start by balancing the element that appears in the fewest substances."


class BalancingSeedWarning(RuntimeError):
    """Raised when one or more equations could not be balanced (content bug)."""


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
