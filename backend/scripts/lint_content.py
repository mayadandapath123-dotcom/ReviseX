#!/usr/bin/env python3
"""Dry-run content files exactly the way the seeder will.

Seeding is all-or-nothing: `_persist_questions` validates every generated
question and a single error aborts the whole seed with ContentSeedError. This
script reproduces that pipeline without touching the database, so a bad item can
be found and fixed before it costs a failed run.

It also checks prompt wording, because a grammatically broken stem passes
structural validation while still reading badly to a student. Two checks are
skipped for maths, where `x + 2y - 5 = 0` and "Find the roots of ..." are
correct and would otherwise be flagged.

Usage:
    python3 scripts/lint_content.py                 # the dense cluster files
    python3 scripts/lint_content.py --all           # every fact file in content/
    python3 scripts/lint_content.py content/sst/history_dense.json
    python3 scripts/lint_content.py --sample 5      # also print example prompts
"""

from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
from typing import Callable, NamedTuple
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app.content.generators import generate_from_fact_file
from app.content.schema import FactFile
from app.content.validators import CurriculumIndex, validate_question

CONTENT_DIR = pathlib.Path(__file__).resolve().parents[1] / "content"

#: Not fact files - they describe the syllabus and the available modes.
NOT_FACT_FILES = {"curriculum.json", "modes.json"}

#: The files carrying the hand-authored dense clusters.
DENSE_TARGETS = [
    "sst/history_dense.json",
    "sst/geography_dense.json",
    "sst/civics_dense.json",
    "sst/economics_dense.json",
    "science/biology_dense.json",
]

class CheckContext(NamedTuple):
    """What a check may need to know about the question it is reading.

    A wording fault is only a fault in context. Equation notation is correct in a
    maths file and wrong in a history fact, and a stem that stops on a function
    word proves a template was truncated in generated content but is the ordinary
    sentence-completion form in a hand-authored one.
    """

    is_equation: bool
    tags: tuple[str, ...]


def _never(prompt: str, ctx: CheckContext) -> bool:
    """A fault in every file, whatever it holds."""
    return False


def _skip_for_equations(prompt: str, ctx: CheckContext) -> bool:
    return ctx.is_equation


def _skip_for_equations_or_authored(prompt: str, ctx: CheckContext) -> bool:
    """Notation and completion-stem checks, both of which turn on provenance.

    Generated items are composed from templates, so a stem ending on "is" or "of"
    means the template stopped early. Authored competency items are prose, and
    half of them are completion stems - "The grass in this food chain is a" with
    Producer / Primary consumer / Decomposer / Secondary consumer as the options -
    which is the form CBSE's own papers use. No template produced them, so nothing
    was truncated.
    """
    return ctx.is_equation or "competency" in ctx.tags


#: Wording faults. The third element says when to skip the check.
CHECKS: list[tuple[str, re.Pattern, Callable[[str, CheckContext], bool]]] = [
    ("repeated word", re.compile(r"\b(\w+)\s+\1\b", re.I), _never),
    ("double 'of'", re.compile(r"\bof of\b", re.I), _never),
    ("double space", re.compile(r"  +"), _never),
    # The stem a bare-verb attribute used to degrade to, "The Silk Route -
    # connected?". A hyphen inside an equation is not this fault, so the pattern
    # is anchored to a stem that ends on it.
    ("stub dash", re.compile(r"\S\s+-\s+\S+\?$"), _skip_for_equations),
    # The stem the reverse-recall fallback produces when it cannot classify an
    # attribute: "Which of the following has X = Y?". A bare "=" scan also flags
    # every physics prompt that quotes a formula, which is correct content.
    ("fallback equals", re.compile(r"^Which of the following has .+ = .+\?$"), _never),
    # A stem that stops on a function word was truncated mid-template. Ending on
    # a colon, a closing quote or a noun is deliberate - "Hydrogen (H) is
    # classified as a:" and 'Which term is defined as: "..."' are both correct.
    ("dangling word", re.compile(
        r"\b(?:of|by|in|at|for|with|through|from|on|to|over|under|upon|into|"
        r"between|is|are|the|a|an|and|which|that)\s*$", re.I), _skip_for_equations_or_authored),
    ("repeated stem phrase", re.compile(
        r"(which of the following).*\1", re.I | re.S), _never),
    # A capitalised article or infinitive straight after a preposition means the
    # fragment was pasted into the sentence unmodified. That is how the live bank
    # ended up with "What is the year of The Act recognising Sinhala...?" and
    # "Which of the following resulted in An armed conflict...?" - 566 approved
    # questions, from facts whose own wording starts with a capital because it is
    # the beginning of a line. The generator now runs those fragments through
    # inline(), and this check is what notices if a new template forgets to.
    #
    # Only a short list of words is matched, so ordinary sentences that happen to
    # capitalise after a preposition ("a floor area of A square metres") are not
    # swept up with the real faults.
    # Case matters here, so this is the one check with no re.I: matching
    # case-insensitively would flag "an example of an international resource",
    # where every word is already correct.
    ("mid-sentence capital", re.compile(
        r"\b(?:of|at|in|for|with|to|by|from|on|as|into)\s+(?:The|A|An|To)\b"),
     _skip_for_equations_or_authored),
]


#: Files whose prompts are equations. `1/v - 1/u = 1/f` and "Find the roots of
#: x² + x - 6 = 0" are correct there, so the notation checks do not apply.
EQUATION_FILES = {"formulas.json", "problems.json", "problems_extra.json"}


def is_equation_file(path: pathlib.Path) -> bool:
    return path.parent.name == "maths" or path.name in EQUATION_FILES


def load_index() -> CurriculumIndex:
    """Build the referential-integrity index from curriculum.json.

    The seeder builds this same index as a side effect of writing chapters to the
    database. Linting must not need a database, so it is rebuilt here from the
    curriculum file alone - same ids, same membership, no writes.
    """
    curriculum = json.loads((CONTENT_DIR / "curriculum.json").read_text())
    chapter_ids: set[str] = set()
    topic_ids: set[str] = set()
    chapter_topics: dict[str, set[str]] = {}
    for subject in curriculum.get("subjects", []):
        for branch in subject.get("branches", []):
            for chapter in branch.get("chapters", []):
                chapter_ids.add(chapter["id"])
                topics = chapter_topics.setdefault(chapter["id"], set())
                for topic in chapter.get("topics", []):
                    topic_ids.add(topic["id"])
                    topics.add(topic["id"])
    return CurriculumIndex(chapter_ids, topic_ids, chapter_topics)


def check_collisions(reports: dict[pathlib.Path, dict]) -> list[str]:
    """Find question ids that more than one content file claims.

    Two faults produce a shared id, and both are silent: the same fact authored
    twice, or two different facts whose subjects agree for the first 40
    characters, which is where `slugify` truncates. Either way the seeder upserts
    by id, so one definition overwrites the other and the loser never reaches a
    student - while the stored hash flip-flops, making every seed report those
    rows as updated.
    """
    owner: dict[str, list[str]] = {}
    for path, report in reports.items():
        name = path.name
        for question in report["questions"]:
            owner.setdefault(question.id, []).append(name)

    problems: list[str] = []
    # Cross-file: two files each define the id, so the loser never reaches a
    # student and the stored hash flip-flops on every seed.
    cross = {qid: sorted(set(f)) for qid, f in owner.items() if len(set(f)) > 1}
    if cross:
        pairs = collections.Counter(tuple(f) for f in cross.values())
        for files, count in pairs.most_common():
            problems.append(f"CROSS-FILE {count} question id(s) claimed by both {' and '.join(files)}")
        for qid in sorted(cross)[:10]:
            problems.append(f"    {qid}  <- {cross[qid]}")

    # Within one file: the generator emits the id twice. The seeder collapses
    # these to the last definition, so content is lost but the hash stays stable.
    for path, report in reports.items():
        ids = collections.Counter(q.id for q in report["questions"])
        intra = [qid for qid, n in ids.items() if n > 1]
        if intra:
            problems.append(f"INTRA-FILE {path.name}: {len(intra)} duplicated id(s)")
            for qid in sorted(intra)[:5]:
                problems.append(f"    {qid}")
    return problems


def lint(path: pathlib.Path, index: CurriculumIndex) -> dict:
    """Generate and validate one content file, returning a summary dict."""
    fact_file = FactFile.model_validate(json.loads(path.read_text()))
    questions = generate_from_fact_file(fact_file)
    maths = is_equation_file(path)

    errors: list[tuple[str, list[str]]] = []
    wording: collections.Counter = collections.Counter()
    wording_samples: dict[str, str] = {}
    by_difficulty: collections.Counter = collections.Counter()
    by_chapter: collections.Counter = collections.Counter()
    ids: collections.Counter = collections.Counter()
    warnings = 0

    for q in questions:
        result = validate_question(q, index)
        if result.errors:
            errors.append((q.id, result.errors))
        warnings += len(result.warnings)
        by_difficulty[q.difficulty] += 1
        by_chapter[q.chapter] += 1
        ids[q.id] += 1
        ctx = CheckContext(is_equation=maths, tags=tuple(q.tags or ()))
        for label, pattern, skip in CHECKS:
            if skip(q.prompt, ctx):
                continue
            if pattern.search(q.prompt):
                wording[label] += 1
                wording_samples.setdefault(label, f"{path.name}: {q.prompt}")

    # An authored item names its own chapter and topic, and resolve_location drops
    # the topic when the two disagree rather than failing, so that the question
    # still seeds. The question is then filed under its chapter with no topic at
    # all, which costs nothing at seed time and quietly removes it from topic
    # browsing. A declared pair that does not match is always a typo, so it is
    # reported instead of being absorbed.
    misplaced = [
        f"{item.get('chapter')!r} / {item.get('topic')!r}"
        for item in fact_file.items
        if item.get("topic") and not str(item["topic"]).startswith(str(item.get("chapter") or "") + ".")
    ]
    if misplaced:
        wording["topic chapter mismatch"] = len(misplaced)
        wording_samples.setdefault("topic chapter mismatch", f"{path.name}: {misplaced[0]}")

    return {
        "items": len(fact_file.items),
        "questions": questions,
        "errors": errors,
        "warnings": warnings,
        "wording": wording,
        "wording_samples": wording_samples,
        "duplicate_ids": [i for i, n in ids.items() if n > 1],
        "by_difficulty": by_difficulty,
        "by_chapter": by_chapter,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="*", help="content files to lint (default: the dense files)")
    parser.add_argument("--all", action="store_true", help="lint every fact file under content/")
    parser.add_argument("--sample", type=int, default=0, help="print N example prompts per file")
    args = parser.parse_args()

    index = load_index()
    if args.files:
        targets = [pathlib.Path(f) for f in args.files]
    elif args.all:
        targets = [p for p in sorted(CONTENT_DIR.rglob("*.json")) if p.name not in NOT_FACT_FILES]
    else:
        targets = [CONTENT_DIR / f for f in DENSE_TARGETS]

    grand = collections.Counter()
    reports: dict[pathlib.Path, dict] = {}
    for path in targets:
        if not path.exists():
            print(f"MISSING {path}")
            continue
        report = lint(path, index)
        reports[path] = report
        name = path.relative_to(CONTENT_DIR) if path.is_relative_to(CONTENT_DIR) else path
        count = len(report["questions"])
        print(
            f"{name}: {report['items']} items -> {count} questions "
            f"({count / max(report['items'], 1):.2f} per item), "
            f"{len(report['errors'])} errors, {report['warnings']} warnings"
        )
        grand["items"] += report["items"]
        grand["questions"] += count
        grand["errors"] += len(report["errors"])
        grand["warnings"] += report["warnings"]
        for label, n in report["wording"].items():
            grand[f"wording:{label}"] += n

        for chapter, n in sorted(report["by_chapter"].items()):
            print(f"      {chapter}: {n}")
        if report["duplicate_ids"]:
            print(f"      DUPLICATE IDS: {report['duplicate_ids'][:5]}")
        for qid, errs in report["errors"][:5]:
            print(f"      ERROR {qid}: {errs[:2]}")
        for label, sample in report["wording_samples"].items():
            print(f"      WORDING {label} ({report['wording'][label]}): {sample[:100]}")
        if args.sample:
            broken = dict(report["errors"])
            pool = [q for q in report["questions"] if q.id not in broken]
            for q in pool[: args.sample]:
                answer = next(o.text for o in q.options if o.key == q.answer_key)
                tag = next((t for t in q.tags if t not in ("fact", "recall")), "recall")
                print(f"      [{q.difficulty[:4]}|{tag[:14]:<14}] {q.prompt}")
                print(f"             -> {answer}")
        print()

    if len(reports) > 1:
        for line in check_collisions(reports):
            print(line)
            if not line.startswith("    "):
                grand["collisions"] += 1

    print(f"TOTAL: {grand['items']} items -> {grand['questions']} questions, "
          f"{grand['errors']} errors, {grand['warnings']} warnings")
    for key, n in sorted(grand.items()):
        if key.startswith("wording:") and n:
            print(f"       {key.split(':', 1)[1]}: {n}")
    if grand["collisions"]:
        print(f"       id collisions: {grand['collisions']}")
    bad = (grand["errors"] + grand["collisions"]
           + sum(v for k, v in grand.items() if k.startswith("wording:")))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
