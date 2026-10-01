"""Generator registry.

A generator turns a list of structured facts into validated QuestionDef objects.
Adding a new content shape = add a module here and register it. Nothing else changes.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Sequence

from app.content.generators import (
    balancing,
    competency,
    definitions,
    elements,
    facts,
    formulas,
    maths,
    physics_formulas,
    reactions,
    sequences,
)
from app.content.schema import FactFile, QuestionDef

GeneratorFn = Callable[[Sequence[dict[str, Any]], str, str, str], list[QuestionDef]]

#: Registered by generator name (the `generator` field in a fact file).
GENERATORS: dict[str, GeneratorFn] = {
    "element": elements.generate,
    "chem_formula": formulas.generate,
    "physics_formula": physics_formulas.generate,
    "definition": definitions.generate,
    "fact_attribute": facts.generate,
    "reaction": reactions.generate,
    "sequence": sequences.generate,
    "balancing": balancing.generate,
    "maths": maths.generate,
    "competency": competency.generate,
}

#: Used when a fact file does not name a generator explicitly.
KIND_TO_GENERATOR: dict[str, str] = {
    "element": "element",
    "formula": "chem_formula",
    "definition": "definition",
    "fact": "fact_attribute",
    "reaction": "reaction",
    "sequence": "sequence",
    "equation": "balancing",
    "maths": "maths",
    "competency": "competency",
    "assertion_reason": "competency",
    "case_study": "competency",
}


class UnknownGeneratorError(ValueError):
    pass


def resolve_generator(name: str | None, kind: str) -> GeneratorFn:
    key = name or KIND_TO_GENERATOR.get(kind)
    if not key or key not in GENERATORS:
        raise UnknownGeneratorError(f"No generator registered for kind={kind!r}, generator={name!r}")
    return GENERATORS[key]


def generate_from_fact_file(fact_file: FactFile, fallback_chapter: str | None = None) -> list[QuestionDef]:
    """Group a fact file's items by generator, then run each generator.

    Per-item `kind` overrides the file-level `kind`, so one file can mix
    definitions, facts and sequences (as the biology file does).
    """
    chapter = fact_file.chapter or fallback_chapter
    if not chapter:
        raise ValueError("Fact file has no chapter and none was supplied as a fallback")

    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in fact_file.items:
        kind = str(item.get("kind") or fact_file.kind)
        generator_name = str(item.get("generator") or fact_file.generator or "") or None
        key = generator_name or KIND_TO_GENERATOR.get(kind)
        if not key:
            raise UnknownGeneratorError(f"Item {item.get('name') or item.get('term') or item.get('subject')!r}: unknown kind {kind!r}")
        groups[key].append(item)

    generated: list[QuestionDef] = []
    for generator_name, group_items in groups.items():
        generator = resolve_generator(generator_name, generator_name)
        generated.extend(
            generator(
                group_items,
                chapter=chapter,
                topic=str(fact_file.topic or ""),
                source_ref=fact_file.source_ref,
            )
        )
    return generated


__all__ = [
    "GENERATORS",
    "KIND_TO_GENERATOR",
    "GeneratorFn",
    "UnknownGeneratorError",
    "generate_from_fact_file",
    "resolve_generator",
]
