"""End-to-end auth check against a running server.

Reads the real question ids and option keys out of the session response rather
than guessing a payload shape, so a schema change surfaces as a failure here
instead of a misleading "0 XP".
"""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8001/api"
RUN = str(int(time.time()))[-6:]
results: list[tuple[bool, str]] = []


def call(method: str, path: str, body=None, token=None, headers=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            raw = r.read().decode()
            return r.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw[:200]


def check(ok: bool, label: str, detail: str = "") -> None:
    results.append((ok, label))
    print(f"{'PASS' if ok else 'FAIL'}  {label}" + (f"  -> {detail}" if detail else ""))


# --- account A -------------------------------------------------------------
user_a, pass_a = f"alpha{RUN}", "password-a1"
st, a = call("POST", "/auth/signup", {"username": user_a, "password": pass_a})
check(st == 201 and bool(a.get("token")), "signup returns 201 + token", f"status={st}")
tok_a, pid_a = a.get("token"), a.get("profile_id")

st, me = call("GET", "/auth/me", token=tok_a)
check(st == 200 and me["user"]["username"] == user_a, "GET /auth/me resolves the token",
      f"status={st}")

st, dup = call("POST", "/auth/signup", {"username": user_a.upper(), "password": "another-pw1"})
check(st == 400, "duplicate username rejected case-insensitively", f"status={st}")

st, bad = call("POST", "/auth/login", {"username": user_a, "password": "wrong-one-1"})
check(st == 401, "wrong password -> 401", f"status={st}")

st, nouser = call("POST", "/auth/login", {"username": f"ghost{RUN}", "password": "whatever1"})
check(st == 401, "unknown username -> 401 (same status, no enumeration)", f"status={st}")

# --- A earns real progress -------------------------------------------------
st, ses = call("POST", "/quiz/sessions", {"mode_key": "daily-mixed", "question_count": 5}, token=tok_a)
check(st == 200 and "session_id" in ses, "quiz session starts with token only", f"status={st}")
sid = ses["session_id"]

attempts = []
for seq, q in enumerate(ses["questions"]):
    correct = next(o["key"] for o in q["options"] if o.get("is_correct"))
    attempts.append({
        "seq": seq, "question_id": str(q["id"]), "selected_key": correct,
        "option_order": [o["key"] for o in q["options"]], "is_correct": True,
        "response_ms": 1800, "shown_ms": 1800, "coefficients": [],
    })
st, sub = call("POST", f"/quiz/sessions/{sid}/submit",
               {"elapsed_ms": 9000, "wrong_penalty": 0, "attempts": attempts, "client_version": "1.0"},
               token=tok_a)
summary = (sub or {}).get("summary", {}) if st == 200 else {}
check(st == 200 and summary.get("xp", 0) > 0, "submit awards XP to the token's owner",
      f"status={st} xp={summary.get("xp")} acc={summary.get('accuracy')}")

st, dash = call("GET", "/progress/dashboard", token=tok_a)
xp_a = dash["today"]["xp_today"] if st == 200 else 0
check(st == 200 and xp_a > 0, "dashboard shows A's XP", f"xp_today={xp_a}")

# --- account B is isolated -------------------------------------------------
user_b, pass_b = f"bravo{RUN}", "password-b1"
st, b = call("POST", "/auth/signup", {"username": user_b, "password": pass_b})
tok_b, pid_b = b.get("token"), b.get("profile_id")
check(st == 201 and pid_b != pid_a, "second account gets its own profile", f"status={st}")

st, dash_b = call("GET", "/progress/dashboard", token=tok_b)
check(st == 200 and dash_b["today"]["xp_today"] == 0, "B starts with zero XP", f"status={st}")

st, forged = call("GET", "/progress/dashboard", token=tok_b, headers={"X-Profile-Id": pid_a})
check(st == 200 and forged["today"]["xp_today"] == 0,
      "B cannot read A's data by forging X-Profile-Id (token wins)",
      f"xp={forged['today']['xp_today'] if st==200 else '?'}")

st, _ = call("GET", "/progress/dashboard", token="forged-token-value")
check(st == 401, "forged token -> 401", f"status={st}")

# --- A's own header cannot be overridden either ----------------------------
st, self_hdr = call("GET", "/progress/dashboard", token=tok_a, headers={"X-Profile-Id": pid_b})
check(st == 200 and self_hdr["today"]["xp_today"] == xp_a,
      "A's token overrides a spoofed header pointing at B", f"xp={self_hdr['today']['xp_today'] if st==200 else '?'}")

# --- logout ----------------------------------------------------------------
st, _ = call("POST", "/auth/logout", token=tok_b)
check(st == 204, "logout -> 204", f"status={st}")
st, _ = call("GET", "/auth/me", token=tok_b)
check(st == 401, "token is dead after logout", f"status={st}")
st, _ = call("GET", "/progress/dashboard", token=tok_b)
check(st == 401, "logged-out token cannot read data", f"status={st}")

# --- relogin restores the same profile & progress --------------------------
st, re = call("POST", "/auth/login", {"username": user_a, "password": pass_a})
check(st == 200 and re.get("profile_id") == pid_a, "relogin returns the SAME profile id", f"status={st}")
st, dash2 = call("GET", "/progress/dashboard", token=re.get("token"))
check(st == 200 and dash2["today"]["xp_today"] == xp_a, "progress persisted across relogin",
      f"xp={dash2['today']['xp_today'] if st==200 else '?'} (was {xp_a})")

passed = sum(1 for ok, _ in results if ok)
print(f"\n{passed}/{len(results)} checks passed")
sys.exit(0 if passed == len(results) else 1)
