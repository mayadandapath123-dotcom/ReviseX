"""Element facts -> valency / symbol / atomic number / configuration questions.

Distractors are always drawn from the element table itself, so wrong options are
real elements and real valencies rather than nonsense.
"""

from __future__ import annotations

from typing import Any, Sequence

from app.content.generators.base import (
    build_options,
    make_question,
    numeric_distractors,
    pick_distractors,
    question_id,
    slugify,
    stable_rng,
)
from app.content.schema import QuestionDef
from app.content.validators import content_hash

CATEGORIES = {
    "metal": "Metal",
    "nonmetal": "Non-metal",
    "metalloid": "Metalloid",
    "noble_gas": "Noble gas",
}

TIME_BUDGET = {"valency": 8000, "symbol": 6000, "atomic": 8000, "config": 12000, "category": 7000}


def _primary_valency(item: dict[str, Any]) -> int:
    valencies = item.get("valencies") or []
    if not valencies:
        raise ValueError(f"Element {item.get('symbol')} has no valencies")
    return int(valencies[0])


def generate(items: Sequence[dict[str, Any]], chapter: str, topic: str, source_ref: str) -> list[QuestionDef]:
    questions: list[QuestionDef] = []

    symbols = [str(i["symbol"]) for i in items]
    names = [str(i["name"]) for i in items]
    valencies = sorted({str(_primary_valency(i)) for i in items})
    configurations = [str(i["configuration"]) for i in items]

    for item in items:
        symbol = str(item["symbol"])
        name = str(item["name"])
        atomic = int(item["atomic_number"])
        valency = _primary_valency(item)
        config = str(item["configuration"])
        category = CATEGORIES[str(item.get("category", "metal"))]
        all_valencies = [str(v) for v in item.get("valencies", [valency])]

        questions.append(_valency_of_element(chapter, topic, source_ref, symbol, name, all_valencies, valencies, item))
        questions.append(_symbol_of_element(chapter, topic, source_ref, symbol, name, symbols))
        questions.append(_name_of_symbol(chapter, topic, source_ref, symbol, name, names))
        questions.append(_atomic_number(chapter, topic, source_ref, symbol, name, atomic))
        questions.append(_configuration(chapter, topic, source_ref, symbol, name, config, configurations))
        questions.append(_category(chapter, topic, source_ref, symbol, name, category))

    questions.extend(_reverse_valency(chapter, topic, source_ref, items))
    questions.extend(_which_is_not(chapter, topic, source_ref, items))

    return _dedupe(questions)


# ─────────────────────────── item builders ───────────────────────────


def _valency_of_element(chapter, topic, source_ref, symbol, name, all_valencies, valency_pool, item) -> QuestionDef:
    rng = stable_rng("valency", symbol)
    correct = all_valencies[0]
    distractors = pick_distractors(correct, valency_pool, 3, rng)
    options, answer_key = build_options(correct, distractors, rng)
    extra = ""
    if len(all_valencies) > 1:
        extra = f" {name} can also show valency {', '.join(all_valencies[1:])}."
    return make_question(
        qid=question_id(chapter, "valency", "valency_of_element", slugify(symbol)),
        chapter=chapter,
        topic=f"{chapter}.valency" if topic.endswith(".symbols") else topic,
        question_type="mcq_single",
        prompt=f"What is the valency of {name} ({symbol})?",
        stimulus={"kind": "element_symbol", "symbol": symbol, "name": name},
        options=options,
        answer_key=answer_key,
        explanation=f"{name} has {item['configuration'].split(',')[-1].strip()} electron(s) in its outermost shell, giving it a combining capacity of {correct}.{extra}".strip(),
        difficulty="easy" if correct in ("1", "2") else "medium",
        time_budget_ms=TIME_BUDGET["valency"],
        source_ref=source_ref,
        tags=["valency", "element", "recall", "fundamentals"],
    )


def _symbol_of_element(chapter, topic, source_ref, symbol, name, symbol_pool) -> QuestionDef:
    rng = stable_rng("symbol-of", name)
    distractors = pick_distractors(symbol, symbol_pool, 3, rng)
    options, answer_key = build_options(symbol, distractors, rng)
    return make_question(
        qid=question_id(chapter, "symbols", "symbol_of_element", slugify(name)),
        chapter=chapter,
        topic=topic,
        question_type="mcq_single",
        prompt=f"What is the chemical symbol of {name}?",
        options=options,
        answer_key=answer_key,
        explanation=f"The symbol of {name} is {symbol}.",
        difficulty="easy",
        time_budget_ms=TIME_BUDGET["symbol"],
        source_ref=source_ref,
        tags=["symbol", "element", "recall", "fundamentals"],
    )


def _name_of_symbol(chapter, topic, source_ref, symbol, name, name_pool) -> QuestionDef:
    rng = stable_rng("name-of", symbol)
    distractors = pick_distractors(name, name_pool, 3, rng)
    options, answer_key = build_options(name, distractors, rng)
    return make_question(
        qid=question_id(chapter, "symbols", "element_of_symbol", slugify(symbol)),
        chapter=chapter,
        topic=topic,
        question_type="mcq_single",
        prompt=f"Which element has the symbol {symbol}?",
        stimulus={"kind": "element_symbol", "symbol": symbol},
        options=options,
        answer_key=answer_key,
        explanation=f"{symbol} stands for {name}.",
        difficulty="easy",
        time_budget_ms=TIME_BUDGET["symbol"],
        source_ref=source_ref,
        tags=["symbol", "element", "recall", "fundamentals"],
    )


def _atomic_number(chapter, topic, source_ref, symbol, name, atomic) -> QuestionDef:
    rng = stable_rng("atomic", symbol)
    distractors = numeric_distractors(float(atomic), rng)
    options, answer_key = build_options(str(atomic), distractors, rng)
    return make_question(
        qid=question_id(chapter, "atomic-number", "atomic_number_of_element", slugify(symbol)),
        chapter=chapter,
        topic=f"{chapter}.atomic-number",
        question_type="mcq_single",
        prompt=f"What is the atomic number of {name} ({symbol})?",
        stimulus={"kind": "element_symbol", "symbol": symbol, "name": name},
        options=options,
        answer_key=answer_key,
        explanation=f"{name} has {atomic} proton(s), so its atomic number is {atomic}.",
        difficulty="medium",
        time_budget_ms=TIME_BUDGET["atomic"],
        source_ref=source_ref,
        tags=["atomic-number", "element", "recall"],
    )


def _configuration(chapter, topic, source_ref, symbol, name, config, config_pool) -> QuestionDef:
    rng = stable_rng("config", symbol)
    distractors = pick_distractors(config, config_pool, 3, rng)
    options, answer_key = build_options(config, distractors, rng)
    return make_question(
        qid=question_id(chapter, "configuration", "configuration_of_element", slugify(symbol)),
        chapter=chapter,
        topic=f"{chapter}.configuration",
        question_type="mcq_single",
        prompt=f"What is the shell-wise electronic configuration of {name} ({symbol})?",
        options=options,
        answer_key=answer_key,
        explanation=f"{name} distributes its electrons as {config} across the K, L, M... shells.",
        difficulty="medium",
        time_budget_ms=TIME_BUDGET["config"],
        source_ref=source_ref,
        tags=["configuration", "element", "recall"],
    )


def _category(chapter, topic, source_ref, symbol, name, category) -> QuestionDef:
    rng = stable_rng("category", symbol)
    distractors = pick_distractors(category, CATEGORIES.values(), 3, rng)
    options, answer_key = build_options(category, distractors, rng)
    return make_question(
        qid=question_id(chapter, "metals-nonmetals", "category_of_element", slugify(symbol)),
        chapter=chapter,
        topic=f"{chapter}.metals-nonmetals",
        question_type="mcq_single",
        prompt=f"{name} ({symbol}) is classified as a:",
        options=options,
        answer_key=answer_key,
        explanation=f"{name} is a {category.lower()}.",
        difficulty="easy",
        time_budget_ms=TIME_BUDGET["category"],
        source_ref=source_ref,
        tags=["metals", "element", "recall"],
    )


def _reverse_valency(chapter, topic, source_ref, items) -> list[QuestionDef]:
    """'Which of these elements has valency X?' — one correct, three with different valencies."""
    out: list[QuestionDef] = []
    by_valency: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        for value in item.get("valencies", []):
            by_valency.setdefault(str(value), []).append(item)

    for valency, group in sorted(by_valency.items()):
        others = [i for i in items if valency not in [str(v) for v in i.get("valencies", [])]]
        if len(others) < 3 or not group:
            continue
        for item in group[:4]:  # cap: keeps the bank varied without exploding
            rng = stable_rng("reverse-valency", item["symbol"], valency)
            distractor_names = [str(i["name"]) for i in rng.sample(others, 3)]
            options, answer_key = build_options(str(item["name"]), distractor_names, rng)
            out.append(
                make_question(
                    qid=question_id(chapter, "valency", "element_of_valency", f"{slugify(item['name'])}-{valency}"),
                    chapter=chapter,
                    topic=f"{chapter}.valency",
                    question_type="mcq_single",
                    prompt=f"Which of the following elements shows valency {valency}?",
                    options=options,
                    answer_key=answer_key,
                    explanation=f"{item['name']} ({item['symbol']}) shows valency {valency}; the others do not.",
                    difficulty="medium",
                    time_budget_ms=10000,
                    source_ref=source_ref,
                    tags=["valency", "element", "application"],
                )
            )
    return out


def _which_is_not(chapter, topic, source_ref, items) -> list[QuestionDef]:
    """'Which is NOT a metal?' style negative-recall items."""
    out: list[QuestionDef] = []
    for category, label in (("metal", "metal"), ("nonmetal", "non-metal")):
        in_group = [i for i in items if i.get("category") == category]
        out_group = [i for i in items if i.get("category") != category]
        if len(in_group) < 1 or len(out_group) < 3:
            continue
        for item in out_group[:6]:
            rng = stable_rng("which-is-not", label, item["symbol"])
            fillers = rng.sample(in_group, 3)
            options, answer_key = build_options(str(item["name"]), [str(i["name"]) for i in fillers], rng)
            out.append(
                make_question(
                    qid=question_id(chapter, "metals-nonmetals", f"which_is_not_{category}", slugify(item["name"])),
                    chapter=chapter,
                    topic=f"{chapter}.metals-nonmetals",
                    question_type="mcq_single",
                    prompt=f"Which of the following is NOT a {label}?",
                    options=options,
                    answer_key=answer_key,
                    explanation=f"{item['name']} is a {CATEGORIES[str(item['category'])].lower()}, so it is not a {label}.",
                    difficulty="medium",
                    time_budget_ms=9000,
                    source_ref=source_ref,
                    tags=["metals", "negative-recall", "application"],
                )
            )
    return out


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
