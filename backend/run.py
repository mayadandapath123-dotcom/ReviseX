#!/usr/bin/env python3
"""Backend entrypoint.

    python run.py            # serve API (auto-migrates and seeds on startup)
    python run.py --seed     # seed only, print a report, exit
    python run.py --reseed   # wipe content tables and re-import from content/
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import uvicorn  # noqa: E402

from app.config.settings import get_settings  # noqa: E402
from app.db.connection import connect  # noqa: E402
from app.db.migrate import migrate  # noqa: E402
from app.db.seed import seed_all  # noqa: E402


def do_seed(reset: bool) -> int:
    conn = connect()
    try:
        applied = migrate(conn)
        report = seed_all(conn, reset_content=reset)
    finally:
        conn.close()

    print(json.dumps({"migrations_applied": applied, **report.as_dict()}, indent=2, ensure_ascii=False))
    return 0 if not report.errors else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="ReviseX backend")
    parser.add_argument("--seed", action="store_true", help="Seed the database and exit")
    parser.add_argument("--reseed", action="store_true", help="Clear content tables, re-import, exit")
    parser.add_argument("--reload", action="store_true", help="Uvicorn auto-reload (development)")
    args = parser.parse_args()

    settings = get_settings()

    if args.seed or args.reseed:
        return do_seed(reset=args.reseed)

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=args.reload,
        log_level="info",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
