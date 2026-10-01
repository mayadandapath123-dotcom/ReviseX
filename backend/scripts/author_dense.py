"""Author dense fact clusters and emit them as content files.

Why clusters, and why four or more
----------------------------------
The fact generator builds three question forms out of one stored fact, but only
when the fact has company:

  1. forward recall  - "What is the year of the Dandi March?"
  2. reverse recall  - "Which event has year = 1930?"  (needs four or more
                        distinct subjects sharing the attribute)
  3. negative recall - "Which statement is NOT correct?" (needs three or more
                        siblings to build the other options from)

A fact sitting alone produces one question and two of the three forms are
unavailable. So content is authored here as CLUSTERS: several subjects sharing
one attribute, with values distinct enough to be plausible distractors for each
other. That is also what makes the questions good - the wrong options come from
real sibling facts rather than from unrelated text, so a student who has not
learnt the material cannot eliminate them.

Every value below is a fact from the CBSE/NCERT Class 10 Social Science
syllabus for 2025-26, stated in original wording. Nothing is copied from a
textbook passage; the questions the generator builds from these are composed,
not reproduced.

Usage:  python3 scripts/author_sst_dense.py
Writes: content/sst/{history,geography,civics,economics}_dense.json
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Sequence

BACKEND = Path(__file__).resolve().parents[1]
OUT_DIR = BACKEND / "content" / "sst"

#: Definitions are a second cluster shape: a term and a one-line definition, from
#: which the definition generator builds two question forms (term -> definition
#: and definition -> term). Useful for term-heavy chapters where several
#: definitions do not share an attribute.
Definition = tuple[str, Sequence[tuple[str, str]], str]
#   topic, [(term, definition), ...], difficulty

SOURCE_REF = (
    "CBSE/NCERT Class 10 Social Science (2025-26) syllabus facts, restated in "
    "original wording. Questions are composed from these facts by the "
    "fact-attribute generator; no text is reproduced from any textbook."
)

Cluster = tuple[str, str, Sequence[tuple[str, str]], str]
#   topic, attribute, [(subject, value), ...], difficulty
#
# A cluster may add a fifth element, `case_sensitive=True`, for values where case
# carries meaning: the genotypes TT, Tt and tt are three different answers, and in
# chemistry CO is carbon monoxide while Co is cobalt. Without the flag the
# generator folds case before comparing, which would collapse those into one.
CaseSensitiveCluster = tuple[str, str, Sequence[tuple[str, str]], str, bool]


#: Bare-verb attributes, rewritten as the noun or passive form that reads as a
#: question. "The cerebrum / controls" cannot be turned into a sentence by any
#: general rule; "The cerebrum / function of" becomes "What is the function of the
#: cerebrum?" Applied here so every branch file is repaired at once.
ATTRIBUTE_RENAMES: dict[str, str] = {
    "controls": "function of",
    "carries": "function of",
    "receives": "function of",
    "performs": "function of",
    "includes": "consists of",
    "means": "meaning of",
    "requires": "requirement of",
    "produces": "product of",
    "solves": "solved by",
    "affected": "affected by",
    "introduced": "introduced by",
    "contributes": "contribution of",
    "concluded that": "conclusion of",
    "recognition requires": "requirement for recognition of",
    "grew because": "reason for the growth of",
    "shifted in": "shift of",
    # These three are participles used bare, which no template can turn into a
    # question. Renamed to the prepositional form the data actually means.
    "described": "described as",
    "used": "used for",
    "distinguished itself by": "distinguished by",
}


def items_from_clusters(clusters: Iterable[Cluster]) -> list[dict]:
    """Expand clusters into fact items the generator can consume."""
    out: list[dict] = []
    for cluster in clusters:
        topic, attribute, rows, difficulty = cluster[:4]
        attribute = ATTRIBUTE_RENAMES.get(attribute.strip().lower(), attribute)
        case_sensitive = bool(cluster[4]) if len(cluster) > 4 else False
        chapter = topic.split(".")[0]
        values = [value for _, value in rows]
        # A cluster whose values repeat cannot support reverse recall, and its
        # distractors would be indistinguishable from the answer. Report it rather
        # than seeding items that silently degrade to one question each.
        folded = values if case_sensitive else [v.lower() for v in values]
        if len(set(folded)) != len(folded):
            counts: dict[str, int] = {}
            for v in folded:
                counts[v] = counts.get(v, 0) + 1
            dupes = sorted(v for v, n in counts.items() if n > 1)
            print(f"  WARNING duplicate values in {topic} / {attribute!r}: {dupes}", file=sys.stderr)
        for subject, value in rows:
            item = {
                "kind": "fact",
                "chapter": chapter,
                "topic": topic,
                "subject": subject,
                "attribute": attribute,
                "value": value,
                "difficulty": difficulty,
            }
            if case_sensitive:
                item["case_sensitive"] = True
            out.append(item)
    return out


def write_file(name: str, clusters: Iterable[Cluster]) -> int:
    items = items_from_clusters(clusters)
    by_chapter = defaultdict(int)
    for item in items:
        by_chapter[item["chapter"]] += 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / name
    path.write_text(
        json.dumps(
            {
                "chapter": next(iter(by_chapter)),
                "kind": "fact",
                "generator": "fact_attribute",
                "source_ref": SOURCE_REF,
                "generator_note": (
                    "Dense attribute clusters. Each item carries its own chapter and "
                    "topic, so one file can span a whole branch. Clusters of four or "
                    "more items sharing an attribute unlock the reverse and "
                    "negative-recall question forms, which is what makes these worth "
                    "three questions each rather than one."
                ),
                "items": items,
            },
            indent=1,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    total = len(items)
    print(f"{name}: {total} facts across {len(by_chapter)} chapters (up to ~{total * 3} questions)")
    for chapter, count in sorted(by_chapter.items()):
        print(f"    {chapter:36} {count:4} facts")
    return total


if __name__ == "__main__":
    raise SystemExit("import one of the branch modules and call write_file()")


def fact_key(item: dict) -> str:
    """The identity a fact's question id is derived from.

    `question_id` slugs the topic, subject and attribute, so two items sharing
    those three produce the same id regardless of the value they carry.
    """
    return "|".join(
        str(item.get(field) or "").strip().lower()
        for field in ("topic", "subject", "attribute")
    )


def existing_item_keys(content_dir: Path, *, exclude: Iterable[str] = ()) -> tuple[set[str], set[str]]:
    """Fact keys and definition terms already authored by other content files.

    A generated question's id derives from its source item, so the same item
    authored in two files collides: both emit
    `sci-bio-control.hormones.fact_attribute.insulin-secreted-by`, the seeder
    keeps whichever file it reads last, and the stored hash flip-flops on every
    run - the seeder reports those rows as updated forever. The pre-existing
    files already carry NCERT-worded content, so a new branch drops its
    duplicates instead of silently overwriting them.
    """
    skip = {Path(name).name for name in exclude} | {"curriculum.json", "modes.json"}
    keys: set[str] = set()
    terms: set[str] = set()
    for path in sorted(content_dir.rglob("*.json")):
        if path.name in skip:
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for item in data.get("items", []):
            if not isinstance(item, dict):
                continue
            term = item.get("term")
            if isinstance(term, str) and term.strip():
                terms.add(term.strip().lower())
            elif item.get("subject"):
                keys.add(fact_key(item))
    return keys, terms


def items_from_definitions(
    clusters: Iterable[Definition], exclude_terms: set[str] | None = None
) -> list[dict]:
    """Expand definition clusters into fact-file items."""
    out: list[dict] = []
    skipped = 0
    for topic, rows, difficulty in clusters:
        chapter = topic.split(".")[0]
        seen: set[str] = set()
        for term, definition in rows:
            if term.lower() in seen:
                print(f"  WARNING duplicate term in {topic}: {term!r}", file=sys.stderr)
            seen.add(term.lower())
            if exclude_terms and term.strip().lower() in exclude_terms:
                # Already defined in an earlier content file; keeping both would
                # collide on the question id.
                skipped += 1
                continue
            out.append({
                "kind": "definition",
                "chapter": chapter,
                "topic": topic,
                "term": term,
                "definition": definition,
                "difficulty": difficulty,
            })
    if skipped:
        print(f"  dropped {skipped} definition(s) already authored in another content file")
    return out


def write_mixed(
    filename: str,
    directory: Path,
    fact_clusters: Iterable[Cluster] = (),
    definition_clusters: Iterable[Definition] = (),
    source_ref: str = SOURCE_REF,
    exclude_terms: set[str] | None = None,
    exclude_fact_keys: set[str] | None = None,
) -> int:
    """Write one content file carrying both fact and definition items.

    `generate_from_fact_file` groups items by their own `kind`, so a single file
    can mix the two shapes; that keeps one branch's content in one place rather
    than spreading it across two files that must stay in step.
    """
    from collections import defaultdict

    items = items_from_clusters(fact_clusters) + items_from_definitions(
        definition_clusters, exclude_terms=exclude_terms
    )
    if exclude_fact_keys:
        before = len(items)
        items = [
            item for item in items
            if item.get("kind") != "fact" or fact_key(item) not in exclude_fact_keys
        ]
        dropped = before - len(items)
        if dropped:
            print(f"  dropped {dropped} fact(s) already authored in another content file")
    by_chapter: dict[str, int] = defaultdict(int)
    for item in items:
        by_chapter[item["chapter"]] += 1

    directory.mkdir(parents=True, exist_ok=True)
    path = directory / filename
    path.write_text(
        json.dumps(
            {
                "chapter": next(iter(by_chapter)),
                "kind": "fact",
                "source_ref": source_ref,
                "generator_note": (
                    "Mixed fact and definition clusters. Facts are grouped by shared "
                    "attribute so the reverse and negative-recall forms unlock; "
                    "definitions carry their own term and meaning."
                ),
                "items": items,
            },
            indent=1,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    facts = sum(1 for i in items if i["kind"] == "fact")
    definitions = sum(1 for i in items if i["kind"] == "definition")
    print(
        f"{filename}: {len(items)} items ({facts} facts, {definitions} definitions) "
        f"across {len(by_chapter)} chapters"
    )
    for chapter, count in sorted(by_chapter.items()):
        print(f"    {chapter:26} {count:4} items")
    return len(items)
