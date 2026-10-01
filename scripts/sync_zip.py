#!/usr/bin/env python3
"""Make a directory tree match a second one, without touching what must be kept.

Usage:  python3 scripts/sync_zip.py <source-dir> <target-dir> [--dry-run]

This exists so that deploying from a zip does not need `rsync`. The tree being
deployed is built from the repository root, so making the checkout match it means
two things at once: copy what is new, and *delete* what the zip no longer has.
Copying alone would leave removed files behind, and they would then be committed
again, so the deploy would silently undo a deletion.

Deleting is the part that needs care. A working checkout holds directories that
are deliberately absent from the zip — `.git` above all, and the local build and
data directories — so anything protected here is never removed and never
overwritten.

Exits 0 and prints a summary. With --dry-run it prints what it would do and
changes nothing.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

#: Directory names that never travel in the zip and must survive a sync, at any
#: depth. `.git` is the important one: removing it would destroy the checkout.
PROTECTED_DIRS = frozenset({
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".idea",
    ".vscode",
})

#: Paths relative to the target root that are local-only. The zip is built from
#: `git archive`, so these are exactly the things .gitignore excludes.
PROTECTED_PREFIXES = (
    "backend/data",
    "frontend/dist",
    "frontend/node_modules",
    ".render_deploy_hook",
)

#: Never sync these even if the zip somehow contains them.
PROTECTED_FILES = frozenset({".env", ".env.local", ".render_deploy_hook"})


def is_protected(rel: Path) -> bool:
    """True for a path this script must leave alone, given one relative to root."""
    if any(part in PROTECTED_DIRS for part in rel.parts):
        return True
    if rel.name in PROTECTED_FILES:
        return True
    posix = rel.as_posix()
    return any(posix == p or posix.startswith(p + "/") for p in PROTECTED_PREFIXES)


def walk_files(root: Path):
    """Every file under root, as paths relative to it, skipping protected names."""
    for dirpath, dirnames, filenames in os.walk(root):
        here = Path(dirpath).relative_to(root)
        # Prune as we descend rather than filtering afterwards, so a large
        # node_modules is never traversed at all.
        dirnames[:] = [d for d in dirnames if d not in PROTECTED_DIRS]
        for name in filenames:
            rel = here / name
            if is_protected(rel):
                continue
            yield rel


def sync(source: Path, target: Path, dry_run: bool = False) -> dict[str, list[str]]:
    if not source.is_dir():
        raise SystemExit(f"source is not a directory: {source}")
    if not target.is_dir():
        raise SystemExit(f"target is not a directory: {target}")

    added: list[str] = []
    changed: list[str] = []
    deleted: list[str] = []
    wanted: set[Path] = set()

    # 1. Copy in anything new or changed.
    for rel in walk_files(source):
        wanted.add(rel)
        src_file = source / rel
        dst_file = target / rel
        if dst_file.exists():
            # Compare content, not timestamps: a fresh unzip gives every file a
            # new mtime, so a timestamp check would rewrite the whole tree on
            # every run and make the diff look enormous.
            try:
                if src_file.read_bytes() == dst_file.read_bytes():
                    continue
            except OSError:
                pass
            changed.append(rel.as_posix())
            if not dry_run:
                shutil.copy2(src_file, dst_file)
        else:
            added.append(rel.as_posix())
            if not dry_run:
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file, dst_file)

    # 2. Delete anything the zip no longer carries.
    for rel in list(walk_files(target)):
        if rel in wanted:
            continue
        # A file the source dropped but which git still tracks in the target is
        # exactly the case this is for.
        deleted.append(rel.as_posix())
        if not dry_run:
            (target / rel).unlink()

    # 3. Clear out directories left empty by the removals.
    if not dry_run:
        for dirpath, dirnames, filenames in os.walk(target, topdown=False):
            here = Path(dirpath)
            if here == target or is_protected(here.relative_to(target)):
                continue
            if not any(here.iterdir()):
                here.rmdir()

    return {"added": sorted(added), "changed": sorted(changed), "deleted": sorted(deleted)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="the extracted zip")
    parser.add_argument("target", type=Path, help="the git checkout to update")
    parser.add_argument("--dry-run", action="store_true", help="report, change nothing")
    parser.add_argument(
        "--json",
        action="store_true",
        help="print the file lists as JSON, for a script to act on",
    )
    args = parser.parse_args()

    result = sync(args.source, args.target, dry_run=args.dry_run)

    if args.json:
        # deploy.sh reads this to decide whether the zip is older than the
        # checkout. A zip built before the latest commit would delete files that
        # are newer than it, which is almost never what was intended, so the
        # caller needs the names rather than a count.
        print(json.dumps(result, indent=1))
        return 0

    if not any(result.values()):
        print("    already up to date, nothing to change")
        return 0
    parts = []
    if result["added"]:
        parts.append(f"{len(result['added'])} added")
    if result["changed"]:
        parts.append(f"{len(result['changed'])} changed")
    if result["deleted"]:
        parts.append(f"{len(result['deleted'])} deleted")
    prefix = "would be " if args.dry_run else ""
    # "added"/"changed"/"deleted" are past participles, so this reads correctly
    # whether or not the run is a rehearsal.
    print(f"    {prefix}{', '.join(parts)}" if args.dry_run
          else f"    {', '.join(parts)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
