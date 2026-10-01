#!/usr/bin/env python3
"""Remove content items whose questions another file already produces.

Two files can author the same fact, and because a question's id derives from the
item rather than the file, both mint the same id. The seeder upserts by id, so
whichever file it reads last wins and the other's version never reaches a
student - while the stored hash flip-flops, making every seed report those rows
as updated and never reaching a fixed point.

The `*_extra.json` files were written later to raise question counts, so they are
treated as the secondary copy: an item there is dropped when a primary file
already produces the same question id. Nothing is lost, because the surviving
copy is the same question.

Usage:
    python3 scripts/dedupe_content.py            # report only
    python3 scripts/dedupe_content.py --apply    # rewrite the extra files
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

BACKEND = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.content.generators import generate_from_fact_file  # noqa: E402
from app.content.schema import FactFile  # noqa: E402

CONTENT_DIR = BACKEND / "content"
NOT_FACT_FILES = {"curriculum.json", "modes.json"}

#: Secondary copies. An item here yields to the same id authored anywhere else.
SECONDARY_SUFFIX = "_extra.json"


def fact_files() -> list[pathlib.Path]:
    return [
        p for p in sorted(CONTENT_DIR.rglob("*.json"))
        if p.name not in NOT_FACT_FILES
    ]


#: Above this many items, leave-one-out attribution costs more than it is worth
#: and the cheaper per-item probe is used instead.
LEAVE_ONE_OUT_LIMIT = 400


def ids_of(items: list[dict], template: FactFile) -> set[str]:
    """Question ids a list of items produces, in the file's own context."""
    probe = template.model_copy(update={"items": items})
    try:
        return {q.id for q in generate_from_fact_file(probe)}
    except Exception:
        return set()


def culprits(items: list[dict], template: FactFile, primary_ids: set[str]) -> list[int]:
    """Indexes of the items responsible for a clash with a primary file.

    Fact and definition generators build their distractors from a pool of sibling
    items, so generating one item in isolation yields no questions at all and
    cannot be blamed for anything. For those files the clash is attributed by
    removal instead: take an item out, regenerate, and see whether the clash set
    shrinks. That is exact, and affordable while the files stay small.

    Larger files are mostly pool-independent - the maths handlers expand one
    parameter set into one question - so the direct per-item probe is used there.
    """
    clashes = ids_of(items, template) & primary_ids
    if not clashes:
        return []

    if len(items) > LEAVE_ONE_OUT_LIMIT:
        return [
            i for i, item in enumerate(items)
            if ids_of([item], template) & primary_ids
        ]

    blamed: list[int] = []
    for i in range(len(items)):
        without = items[:i] + items[i + 1:]
        if len(ids_of(without, template) & primary_ids) < len(clashes):
            blamed.append(i)
    return blamed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="rewrite the secondary files")
    args = parser.parse_args()

    paths = fact_files()
    primary = [p for p in paths if not p.name.endswith(SECONDARY_SUFFIX)]
    secondary = [p for p in paths if p.name.endswith(SECONDARY_SUFFIX)]

    # Ids the primary files own. Generated once, in full, so cluster-dependent
    # forms (reverse and negative recall) are included.
    primary_ids: set[str] = set()
    primary_files: dict[str, str] = {}
    for path in primary:
        try:
            template = FactFile.model_validate(json.loads(path.read_text()))
        except Exception as exc:
            print(f"skip {path.name}: {exc}")
            continue
        for question_id in ids_of(template.items, template):
            primary_ids.add(question_id)
            primary_files.setdefault(question_id, path.name)

    print(f"{len(primary_ids)} ids owned by {len(primary)} primary files")
    print(f"checking {len(secondary)} secondary files\n")

    total_dropped = 0
    for path in secondary:
        template = FactFile.model_validate(json.loads(path.read_text()))
        items = list(template.items)
        blamed = culprits(items, template, primary_ids)
        if not blamed:
            print(f"{path.name}: clean")
            continue

        blame_set = set(blamed)
        keep = [item for i, item in enumerate(items) if i not in blame_set]
        dropped = [( _label(items[i]), "") for i in blamed]

        print(f"{path.name}: {len(dropped)} of {len(items)} items duplicate a primary file")
        for label, _ in dropped[:8]:
            print(f"      {label}")
        if len(dropped) > 8:
            print(f"      ... and {len(dropped) - 8} more")

        remaining = ids_of(keep, template) & primary_ids
        if remaining:
            print(f"      still clashing after removal: {len(remaining)} id(s) - re-run to converge")

        if args.apply and dropped:
            backup = path.with_suffix(path.suffix + ".bak")
            if not backup.exists():
                backup.write_text(path.read_text())
            path.write_text(
                json.dumps(template.model_copy(update={"items": keep}).model_dump(),
                           ensure_ascii=False, indent=1) + "\n"
            )
            print(f"      rewrote {path.name}: {len(keep)} items kept (backup: {backup.name})")
        total_dropped += len(dropped)
        print()

    verb = "dropped" if args.apply else "would drop"
    print(f"TOTAL {verb}: {total_dropped} duplicate items")
    return 0


def _label(item: dict) -> str:
    for key in ("term", "subject", "name"):
        if item.get(key):
            attribute = item.get("attribute")
            return f"{item[key]}" + (f" / {attribute}" if attribute else "")
    if item.get("problem"):
        return f"{item['problem']} {json.dumps(item.get('params', {}), sort_keys=True)}"
    return json.dumps(item, ensure_ascii=False)[:70]


if __name__ == "__main__":
    raise SystemExit(main())
