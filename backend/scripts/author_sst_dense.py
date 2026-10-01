"""Write the dense SST fact files from the branch cluster tables.

Run this after editing any module in sst_clusters/. It rewrites the JSON content
files, which the seeder then turns into questions - so the authoring format stays
compact and readable while the shipped content stays plain data.

Usage:  python3 scripts/author_sst_dense.py
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "scripts"))

from author_dense import write_file  # noqa: E402

BRANCHES = [
    ("history_dense.json", "history"),
    ("geography_dense.json", "geography"),
    ("civics_dense.json", "civics"),
    ("economics_dense.json", "economics"),
]


def main() -> int:
    total = 0
    for filename, module_name in BRANCHES:
        try:
            module = __import__(f"sst_clusters.{module_name}", fromlist=["CLUSTERS"])
        except ImportError as exc:
            print(f"skip {filename}: {exc}")
            continue
        clusters = module.CLUSTERS
        count = write_file(filename, clusters)
        total += count
        print()
    print(f"TOTAL {total} SST facts authored (up to ~{total * 3} questions if every cluster unlocks all three forms)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
