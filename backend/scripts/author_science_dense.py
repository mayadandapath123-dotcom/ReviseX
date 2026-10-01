"""Write the dense Science fact files from the branch cluster tables.

Usage:  python3 scripts/author_science_dense.py
Writes: content/science/{biology,physics,chemistry}_dense.json
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "scripts"))

from author_dense import existing_item_keys, write_mixed  # noqa: E402

CONTENT_DIR = BACKEND / "content"
OUT_DIR = CONTENT_DIR / "science"

SOURCE_REF = (
    "CBSE/NCERT Class 10 Science (2025-26) syllabus facts and one-line "
    "definitions, restated in original wording. Questions are composed from "
    "these facts by the generators; no textbook passage is reproduced."
)

BRANCHES = [
    ("biology_dense.json", "biology"),
    ("physics_dense.json", "physics"),
    ("chemistry_dense.json", "chemistry"),
]


def main() -> int:
    total = 0
    # Terms already defined by the older science files. Excluding the dense
    # outputs matters: they are rewritten every run, so counting them would
    # suppress a branch's own definitions on the second run onwards.
    exclude_keys, exclude_terms = existing_item_keys(
        CONTENT_DIR, exclude=[name for name, _ in BRANCHES]
    )
    print(
        f"{len(exclude_keys)} facts and {len(exclude_terms)} definitions already "
        f"authored elsewhere; duplicates will be dropped\n"
    )
    for filename, module_name in BRANCHES:
        try:
            module = __import__(f"sci_clusters.{module_name}", fromlist=["FACTS"])
        except ImportError as exc:
            print(f"skip {filename}: {exc}")
            continue
        count = write_mixed(
            filename,
            OUT_DIR,
            fact_clusters=getattr(module, "FACTS", ()),
            definition_clusters=getattr(module, "DEFINITIONS", ()),
            source_ref=SOURCE_REF,
            exclude_terms=exclude_terms,
            exclude_fact_keys=exclude_keys,
        )
        total += count
        print()
    print(f"TOTAL {total} Science items authored")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
