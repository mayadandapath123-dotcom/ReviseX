"""End-to-end friends check against a running server.

Covers the approval flow in both directions plus the ways it can be abused:
accepting your own outgoing request, adding yourself, re-adding an existing
friend, and reading the friends board without a token.
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


def call(method, path, body=None, token=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
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


def check(ok, label, detail=""):
    results.append((ok, label))
    print(f"{'PASS' if ok else 'FAIL'}  {label}" + (f"  -> {detail}" if detail else ""))


def signup(name):
    st, r = call("POST", "/auth/signup", {"username": name, "password": f"pw-{name}-1"})
    assert st == 201, (st, r)
    return r["token"], r["user"]["id"]


tok_a, id_a = signup(f"anna{RUN}")
tok_b, id_b = signup(f"ben{RUN}")
tok_c, id_c = signup(f"cat{RUN}")
name_a, name_b, name_c = f"anna{RUN}", f"ben{RUN}", f"cat{RUN}"
check(True, "three accounts created")

# --- request + approval ----------------------------------------------------
st, r = call("POST", "/friends/request", {"username": name_b}, tok_a)
check(st == 201 and r.get("status") == "pending", "A sends B a request", f"status={st}")
req_ab = r.get("request_id")

st, r = call("GET", "/friends/requests", token=tok_b)
incoming = r.get("incoming", [])
check(st == 200 and len(incoming) == 1 and incoming[0]["username"] == name_a,
      "B sees the incoming request from A", f"incoming={len(incoming)}")

st, r = call("GET", "/friends", token=tok_b)
check(st == 200 and r["friend_count"] == 0, "no friendship exists before approval",
      f"count={r.get('friend_count')}")

st, _ = call("POST", "/friends/request/accept", {"request_id": req_ab}, tok_a)
check(st == 403, "A cannot accept the request A sent", f"status={st}")

st, r = call("POST", "/friends/request/accept", {"request_id": req_ab}, tok_b)
check(st == 200 and r.get("status") == "accepted", "B accepts", f"status={st}")

st, r = call("GET", "/friends", token=tok_a)
check(st == 200 and r["friend_count"] == 1 and r["friends"][0]["username"] == name_b,
      "A's friend list now contains B", f"count={r.get('friend_count')}")
st, r = call("GET", "/friends", token=tok_b)
check(st == 200 and r["friend_count"] == 1 and r["friends"][0]["username"] == name_a,
      "B's friend list contains A (edge is bidirectional)", f"count={r.get('friend_count')}")

# --- abuse cases -----------------------------------------------------------
st, r = call("POST", "/friends/request", {"username": name_b}, tok_a)
check(st == 409, "re-adding an existing friend -> 409", f"status={st} {r.get('detail','')[:40]}")
st, _ = call("POST", "/friends/request", {"username": name_a}, tok_a)
check(st == 400, "adding yourself -> 400", f"status={st}")
st, _ = call("POST", "/friends/request", {"username": f"nobody{RUN}"}, tok_a)
check(st == 404, "unknown username -> 404", f"status={st}")
st, _ = call("POST", "/friends/request/accept", {"request_id": "fr_doesnotexist"}, tok_b)
check(st == 404, "accepting a nonexistent request -> 404", f"status={st}")
st, _ = call("GET", "/friends", None)
check(st == 401, "friends list without a token -> 401", f"status={st}")

# --- mutual pending auto-accepts ------------------------------------------
st, _ = call("POST", "/friends/request", {"username": name_c}, tok_a)
check(st == 201, "A sends C a request", f"status={st}")
st, r = call("POST", "/friends/request", {"username": name_a}, tok_c)
check(st == 200 and r.get("status") == "accepted",
      "C replying to A's pending request auto-accepts instead of deadlocking",
      f"status={st} -> {r.get('status')}")
st, r = call("GET", "/friends", token=tok_a)
check(st == 200 and r["friend_count"] == 2, "A now has 2 friends", f"count={r.get('friend_count')}")

# --- decline ---------------------------------------------------------------
st, _ = call("POST", "/friends/request", {"username": name_b}, tok_c)
check(st == 201, "C sends B a request", f"status={st}")
st, r = call("GET", "/friends/requests", token=tok_b)
rid = r["incoming"][0]["request_id"]
st, r = call("POST", "/friends/request/decline", {"request_id": rid}, tok_b)
check(st == 200 and r.get("status") == "declined", "B declines C", f"status={st}")
st, r = call("GET", "/friends", token=tok_c)
check(st == 200 and r["friend_count"] == 1, "declining did not create a friendship",
      f"count={r.get('friend_count')}")

# --- friends-only leaderboard ---------------------------------------------
st, board = call("GET", "/friends/leaderboard", token=tok_a)
names = sorted(e["username"] for e in board.get("entries", []))
check(st == 200 and names == sorted([name_a, name_b, name_c]),
      "A's board contains exactly A's friends plus A", f"{names}")
check(all(e.get("rank") for e in board.get("entries", [])), "board entries are ranked")

st, board_c = call("GET", "/friends/leaderboard", token=tok_c)
names_c = sorted(e["username"] for e in board_c.get("entries", []))
check(names_c == sorted([name_a, name_c]),
      "C's board excludes B (C is not friends with B)", f"{names_c}")

# --- removal ---------------------------------------------------------------
st, r = call("POST", "/friends/remove", {"user_id": id_c}, tok_a)
check(st == 200 and r.get("status") == "removed", "A removes C", f"status={st}")
st, r = call("GET", "/friends", token=tok_a)
check(st == 200 and r["friend_count"] == 1, "A is back to 1 friend", f"count={r.get('friend_count')}")
st, r = call("GET", "/friends", token=tok_c)
check(st == 200 and r["friend_count"] == 0, "removal is symmetric", f"count={r.get('friend_count')}")
st, _ = call("POST", "/friends/remove", {"user_id": id_c}, tok_a)
check(st == 409 or st == 400, "removing a non-friend is rejected", f"status={st}")

passed = sum(1 for ok, _ in results if ok)
print(f"\n{passed}/{len(results)} checks passed")
sys.exit(0 if passed == len(results) else 1)
