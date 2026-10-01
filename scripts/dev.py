#!/usr/bin/env python3
"""One command to run the whole app locally.

    python scripts/dev.py              # backend + frontend together
    python scripts/dev.py --backend    # backend only
    python scripts/dev.py --frontend   # frontend only
    python scripts/dev.py --reset      # wipe local DB, reseed, then run

Creates backend/.venv on first run and installs both dependency sets, so a fresh
clone needs nothing but Python 3.11+ and Node 18+.
"""

from __future__ import annotations

import argparse
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
VENV = BACKEND / ".venv"
DB_FILE = BACKEND / "data" / "revise.sqlite3"

BACKEND_PORT = int(os.environ.get("PORT", "8000"))
FRONTEND_PORT = int(os.environ.get("FRONTEND_PORT", "5173"))


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    print(f"$ {' '.join(cmd)}", flush=True)
    return subprocess.run(cmd, check=True, **kwargs)


def python_binary() -> str:
    if os.name == "nt":
        candidate = VENV / "Scripts" / "python.exe"
    else:
        candidate = VENV / "bin" / "python"
    return str(candidate) if candidate.exists() else sys.executable


def npm_command() -> list[str]:
    """Resolve npm to an absolute path before handing it to subprocess.

    On Windows npm is a batch file (npm.cmd). subprocess ultimately calls
    CreateProcess, which appends only .exe when a name has no extension — it does
    not consult PATHEXT. So passing the bare string "npm" raises
    FileNotFoundError [WinError 2] even when Node.js is installed correctly.

    shutil.which() does honour PATHEXT and returns the real path
    (e.g. C:\\Program Files\\nodejs\\npm.cmd), which CreateProcess can execute.
    """
    resolved = shutil.which("npm")
    if resolved is None:
        sys.exit(
            "npm was not found on PATH.\n"
            "  1. Install Node.js 18+ from https://nodejs.org/ (click the LTS button).\n"
            "  2. CLOSE this PowerShell window and open a new one, so it picks up the\n"
            "     updated PATH. Then run this script again."
        )

    # Microsoft documents that a batch file must be run through the command
    # interpreter. Launching npm.cmd directly happens to work in most Python
    # versions, but going via cmd.exe /c is the documented, version-proof way.
    if os.name == "nt" and resolved.lower().endswith((".cmd", ".bat")):
        comspec = os.environ.get("ComSpec", "cmd.exe")
        return [comspec, "/c", resolved]
    return [resolved]


def ensure_backend_deps() -> None:
    if not VENV.exists():
        print("Creating backend virtualenv…", flush=True)
        run([sys.executable, "-m", "venv", str(VENV)])
    requirements = BACKEND / "requirements.txt"
    marker = VENV / ".deps-installed"
    stamp = f"{requirements.stat().st_mtime_ns}"
    if marker.exists() and marker.read_text().strip() == stamp:
        return
    print("Installing backend dependencies…", flush=True)
    run([python_binary(), "-m", "pip", "install", "--quiet", "--upgrade", "pip"])
    run([python_binary(), "-m", "pip", "install", "--quiet", "-r", str(requirements)])
    marker.write_text(stamp)


def ensure_frontend_deps() -> None:
    if (FRONTEND / "node_modules").exists():
        return
    print("Installing frontend dependencies…", flush=True)
    run([*npm_command(), "install", "--no-audit", "--no-fund"], cwd=FRONTEND)


def wait_for_backend(timeout: int = 60) -> bool:
    import urllib.error
    import urllib.request

    deadline = time.time() + timeout
    url = f"http://127.0.0.1:{BACKEND_PORT}/api/health"
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    return True
        except (urllib.error.URLError, OSError, TimeoutError):
            time.sleep(0.5)
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Run ReviseX locally")
    parser.add_argument("--backend", action="store_true", help="Backend only")
    parser.add_argument("--frontend", action="store_true", help="Frontend only")
    parser.add_argument("--reset", action="store_true", help="Delete the local database before starting")
    parser.add_argument("--no-install", action="store_true", help="Skip dependency installation")
    args = parser.parse_args()

    want_backend = args.backend or not args.frontend
    want_frontend = args.frontend or not args.backend

    if args.reset:
        for suffix in ("", "-wal", "-shm"):
            path = Path(str(DB_FILE) + suffix)
            if path.exists():
                path.unlink()
                print(f"Removed {path}", flush=True)

    if not args.no_install:
        if want_backend:
            ensure_backend_deps()
        if want_frontend:
            ensure_frontend_deps()

    env = os.environ.copy()
    env["PORT"] = str(BACKEND_PORT)
    env["VITE_API_BASE_URL"] = f"http://127.0.0.1:{BACKEND_PORT}"

    processes: list[subprocess.Popen] = []

    def terminate_tree(process: subprocess.Popen) -> None:
        """Stop a child process and everything it spawned.

        On Windows `terminate()` only kills the direct child. Because npm is
        launched via cmd.exe and itself spawns node -> vite, that would leave the
        dev server orphaned and still holding the port, so the next run fails with
        "address already in use". taskkill /T walks the whole tree.
        """
        if process.poll() is not None:
            return
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        else:
            process.terminate()

    def shutdown(*_args) -> None:
        for process in processes:
            terminate_tree(process)
        deadline = time.time() + 5
        for process in processes:
            while process.poll() is None and time.time() < deadline:
                time.sleep(0.1)
            if process.poll() is None:
                try:
                    process.kill()
                except OSError:
                    pass  # already gone

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        if want_backend:
            print(f"\nStarting backend on http://localhost:{BACKEND_PORT} (docs at /docs)…", flush=True)
            processes.append(subprocess.Popen([python_binary(), "run.py"], cwd=BACKEND, env=env))
            if not wait_for_backend():
                print("Backend did not become healthy in time; check the output above.", file=sys.stderr)
                return 1
            print("Backend healthy.", flush=True)

        if want_frontend:
            print(f"\nStarting frontend on http://localhost:{FRONTEND_PORT}…", flush=True)
            processes.append(
                subprocess.Popen(
                    [*npm_command(), "run", "dev", "--", "--port", str(FRONTEND_PORT)],
                    cwd=FRONTEND,
                    env=env,
                )
            )

        print(f"\n  ➜  Open http://localhost:{FRONTEND_PORT if want_frontend else BACKEND_PORT}\n", flush=True)

        while all(process.poll() is None for process in processes):
            time.sleep(0.5)

        failed = [process for process in processes if process.poll() not in (None, 0)]
        return failed[0].returncode if failed else 0
    finally:
        shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
