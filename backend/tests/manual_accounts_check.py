"""Checks for Google sign-in, profile claiming, friends search and admin.

Google's OAuth endpoints need real credentials and a browser, so the identity
resolution is exercised directly against the database with a synthetic identity
- that is where the security logic lives (which account a Google login maps to,
whether linking can collide, whether unlinking can strand someone). The HTTP
layer is covered for the parts that do not need Google: status reporting, and
the 503 when unconfigured.
"""
from __future__ import annotations

import json
import os
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
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read().decode()
            if not raw:
                return r.status, None
            try:
                return r.status, json.loads(raw)
            except json.JSONDecodeError:
                # The OAuth callback 303s to the SPA, and urllib follows it, so
                # the body is HTML. The status is what matters there.
                return r.status, raw[:120]
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw[:200]


def check(ok, label, detail=""):
    results.append((ok, label))
    print(f"{'PASS' if ok else 'FAIL'}  {label}" + (f"  -> {detail}" if detail else ""))


def signup(name, password="pw-test-1", claim=None):
    body = {"username": name, "password": password}
    if claim:
        body["claim_profile_id"] = claim
    st, r = call("POST", "/auth/signup", body)
    assert st == 201, (st, r)
    return r["token"], r["user"]["id"], r["profile_id"], r


# ── 1. claiming a local profile ────────────────────────────────────────────
# A student who played without an account has XP on an unclaimed profile.
st, local = call("POST", "/profiles", {"display_name": f"local{RUN}"})
check(st in (200, 201) and "profile" in local, "local account-free profile can be created", f"status={st}")
local_pid = local["profile"]["id"]
call("POST", f"/profiles/{local_pid}/activate")

# Put some progress on it via the legacy header path.
st, ses = call("POST", "/quiz/sessions", {"mode_key": "daily-mixed", "question_count": 3}, None)
hdr_token = None
if st == 200:
    attempts = []
    for seq, q in enumerate(ses["questions"]):
        correct = next(o["key"] for o in q["options"] if o.get("is_correct"))
        attempts.append({"seq": seq, "question_id": str(q["id"]), "selected_key": correct,
                         "option_order": [o["key"] for o in q["options"]], "is_correct": True,
                         "response_ms": 1500, "shown_ms": 1500, "coefficients": []})
    import urllib.request as _u
    req = _u.Request(BASE + f"/quiz/sessions/{ses['session_id']}/submit",
                     data=json.dumps({"elapsed_ms": 6000, "wrong_penalty": 0, "attempts": attempts,
                                      "client_version": "1.0"}).encode(), method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("X-Profile-Id", local_pid)
    try:
        _u.urlopen(req, timeout=60)
        earned_xp = True
    except Exception:
        earned_xp = False
else:
    earned_xp = False

tok, uid, pid, res = signup(f"claim{RUN}", claim=local_pid)
check(res.get("claimed_profile") is True and pid == local_pid,
      "signup adopts the existing local profile instead of creating a new one",
      f"claimed={res.get('claimed_profile')} pid={pid}")

st, dash = call("GET", "/progress/dashboard", token=tok)
xp_after = dash["today"]["xp_today"] if st == 200 else -1
check(st == 200 and ((xp_after > 0) if earned_xp else True),
      "progress earned before the account existed is still visible after",
      f"xp_today={xp_after}")

# A second account must not be able to steal it.
st, dup = call("POST", "/auth/signup", {"username": f"thief{RUN}", "password": "pw-thief-1",
                                        "claim_profile_id": local_pid})
check(st == 201 and dup.get("profile_id") != local_pid,
      "an already-claimed profile cannot be adopted by a second account",
      f"got={dup.get('profile_id')}")

st, ghost = call("POST", "/auth/signup", {"username": f"ghost{RUN}", "password": "pw-ghost-1",
                                          "claim_profile_id": "p_doesnotexist"})
check(st == 201 and ghost.get("profile_id"),
      "a stale claim id falls back to a fresh profile rather than failing signup")

# ── 2. Google identity resolution (direct, no network) ─────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.db.connection import connect  # noqa: E402
from app.services.auth_service import AuthService  # noqa: E402
from app.services.google_auth_service import NO_PASSWORD, GoogleAuthError, GoogleAuthService  # noqa: E402

conn = connect()
auth = AuthService(conn)
google = GoogleAuthService(conn, auth)

sub = f"google-sub-{RUN}"
identity = {"sub": sub, "email": f"g{RUN}@example.com", "email_verified": True,
            "name": "Google User", "picture": None}

sess1 = google.sign_in_or_register(identity)
check(bool(sess1.get("token")) and bool(sess1.get("profile_id")),
      "first Google sign-in creates an account and a profile")
gid = sess1["user"]["id"]

sess2 = google.sign_in_or_register(identity)
check(sess2["user"]["id"] == gid, "the same Google sub returns the SAME account (no duplicate)")

created = auth.user_by_id(gid)
check(created["password_hash"] == NO_PASSWORD and created["provider"] == "google",
      "Google-only account stores an unusable password sentinel")
from app.services.auth_service import verify_password  # noqa: E402
check(not verify_password("", NO_PASSWORD) and not verify_password("anything", NO_PASSWORD),
      "the sentinel can never verify, so it is not a back door")

# Linking a Google identity to an existing password account.
tok_l, uid_l, pid_l, _ = signup(f"link{RUN}")
res = google.link_to_account(uid_l, {"sub": f"other-{RUN}", "email": f"o{RUN}@example.com",
                                     "email_verified": True, "name": "Other"})
check(res.get("linked") is True, "a signed-in account can link a Google identity")

try:
    google.link_to_account(uid_l, {"sub": f"third-{RUN}", "email": "t@e.com",
                                   "email_verified": True, "name": "Third"})
    check(False, "linking a second Google identity is refused")
except GoogleAuthError:
    check(True, "linking a second Google identity is refused")

try:
    google.link_to_account(uid, identity)   # sub already belongs to gid
    check(False, "linking a Google identity already owned by another account is refused")
except GoogleAuthError as e:
    check("already linked" in str(e), "cannot hijack a Google identity belonging to another account",
          str(e)[:50])

# Unlink guards.
try:
    google.unlink(gid)
    check(False, "unlinking a Google-only account is refused (would strand it)")
except GoogleAuthError as e:
    check("password first" in str(e).lower(), "unlinking a Google-only account is refused until a password exists",
          str(e)[:60])

google.set_password_for_oauth_account(gid, "newpw-123")
after = auth.user_by_id(gid)
check(after["password_hash"] != NO_PASSWORD and verify_password("newpw-123", after["password_hash"]),
      "a Google account can be given a real password")
check(after["provider"] == "both", "provider becomes 'both' once a password is set")

res = google.unlink(gid)
check(res.get("linked") is False and auth.user_by_id(gid)["google_sub"] is None,
      "unlinking succeeds once a password exists")
check(verify_password("newpw-123", auth.user_by_id(gid)["password_hash"]),
      "after unlinking, the password still works")

# Email must never silently merge into an existing account.
tok_e, uid_e, _, _ = signup(f"email{RUN}")
before = auth.user_by_id(uid_e)["google_sub"]
sess_e = google.sign_in_or_register({"sub": f"fresh-{RUN}", "email": f"email{RUN}@example.com",
                                     "email_verified": True, "name": "Email"})
check(sess_e["user"]["id"] != uid_e, "a matching email does NOT auto-merge into an existing account")
check(before is None, "the existing account was left untouched")
conn.close()

# ── 3. Google HTTP surface ─────────────────────────────────────────────────
st, status = call("GET", "/auth/google/status")
check(st == 200 and "enabled" in status, "GET /auth/google/status reports configuration",
      f"enabled={status.get('enabled')}")
if not status.get("enabled"):
    st, r = call("GET", "/auth/google/start?mode=signin")
    check(st == 503, "start returns 503 when Google is not configured", f"status={st}")
st, r = call("GET", "/auth/google/start?mode=link")
check(st == 401, "link mode requires a signed-in account", f"status={st}")
st, r = call("GET", "/auth/google/callback?error=access_denied&state=x")
check(st == 303 or st == 200, "callback handles a cancelled flow without a 500", f"status={st}")

# ── 4. Friends search ──────────────────────────────────────────────────────
tok_s, uid_s, _, _ = signup(f"searcher{RUN}")
target_name = f"target{RUN}"
tok_t, uid_t, _, _ = signup(target_name)

st, r = call("GET", f"/friends/search?q={target_name[:12]}", token=tok_s)
found = [e["username"] for e in r.get("results", [])] if st == 200 else []
check(st == 200 and target_name in found, "search finds an account by username", f"{found[:3]}")

st, r = call("GET", f"/friends/search?q={target_name}", token=tok_s)
entry = next((e for e in r.get("results", []) if e["username"] == target_name), None)
check(entry is not None and entry["relationship"] == "none",
      "a stranger is annotated relationship=none")
check(entry is not None and "password_hash" not in entry and "google_sub" not in entry,
      "search results never expose password or google_sub")

st, r = call("GET", f"/friends/search?q=searcher{RUN}", token=tok_s)
check(st == 200 and all(e["user_id"] != uid_s for e in r.get("results", [])),
      "you cannot find yourself in search")

st, r = call("GET", "/friends/search?q=a", token=tok_s)
check(st == 200 and r.get("results") == [], "a 1-character query returns nothing (directory guard)")

st, r = call("GET", "/friends/search?q=target&limit=9999", token=tok_s)
check(st == 200 and len(r.get("results", [])) <= 20, "limit is capped at 20 server side",
      f"n={len(r.get('results', []))}")

call("POST", "/friends/request", {"username": target_name}, tok_s)
st, r = call("GET", f"/friends/search?q={target_name}", token=tok_s)
entry = next((e for e in r.get("results", []) if e["username"] == target_name), None)
check(entry is not None and entry["relationship"] == "outgoing",
      "a pending invitation is annotated outgoing", f"rel={entry and entry['relationship']}")
st, r = call("GET", "/friends/requests", token=tok_t)
rid = r["incoming"][0]["request_id"]
call("POST", "/friends/request/accept", {"request_id": rid}, tok_t)
st, r = call("GET", f"/friends/search?q={target_name}", token=tok_s)
entry = next((e for e in r.get("results", []) if e["username"] == target_name), None)
check(entry is not None and entry["relationship"] == "friends",
      "an accepted friend is annotated friends", f"rel={entry and entry['relationship']}")

st, r = call("GET", "/friends/search?q=anything")
check(st == 401, "search requires a token", f"status={st}")

# ── 5. Admin ───────────────────────────────────────────────────────────────
st, r = call("GET", "/admin/overview", token=tok_s)
check(st == 403, "a normal account cannot read the admin overview", f"status={st}")
st, r = call("GET", "/admin/overview")
check(st == 401, "admin overview requires a token at all", f"status={st}")
st, r = call("POST", f"/admin/users/{uid_t}/impersonate", {"user_id": uid_t}, tok_s)
check(st == 403, "a normal account cannot impersonate anyone", f"status={st}")

admin_name = os.environ.get("EXPECTED_ADMIN")
if admin_name:
    st, r = call("POST", "/auth/login", {"username": admin_name, "password": os.environ.get("EXPECTED_ADMIN_PW", "pw-test-1")})
    if st == 200:
        atok = r["token"]
        st, ov = call("GET", "/admin/overview", token=atok)
        check(st == 200 and ov.get("users_total", 0) > 0, "admin sees the overview",
              f"users={ov.get('users_total')} online={ov.get('users_online_now')}")
        st, lst = call("GET", "/admin/users?q=target", token=atok)
        check(st == 200 and lst.get("total", 0) >= 1, "admin can search accounts",
              f"total={lst.get('total')}")
        row = next((u for u in lst.get("users", []) if u["username"] == target_name), None)
        check(row is not None and "answers" in row and "last_seen_at" in row and "streak_day_count" in row,
              "admin user row carries answers, streak and last-seen")
        check(row is not None and "password_hash" not in row, "admin list never exposes password hashes")
        st, imp = call("POST", f"/admin/users/{uid_t}/impersonate", {"user_id": uid_t, "reason": "support"}, atok)
        check(st == 200 and bool(imp.get("token")), "admin can issue an impersonation token",
              f"ttl={imp.get('expires_in_minutes')}m")
        if st == 200:
            st2, me = call("GET", "/auth/me", token=imp["token"])
            check(st2 == 200 and me["user"]["id"] == uid_t,
                  "the impersonation token really acts as the target account")
            st2, d2 = call("GET", "/progress/dashboard", token=imp["token"])
            check(st2 == 200, "impersonation can read the target's progress")
        st, aud = call("GET", "/admin/audit", token=atok)
        entries = aud.get("entries", []) if st == 200 else []
        check(st == 200 and any(e["action"] == "impersonate" and e["target_username"] == target_name for e in entries),
              "impersonation is recorded in the audit log", f"entries={len(entries)}")
        st, _ = call("GET", "/admin/users", token=imp.get("token") if st == 200 else None)
        check(st == 403, "an impersonation session is NOT itself an admin", f"status={st}")
    else:
        check(False, "admin account could not be signed into", f"status={st}")
else:
    print("SKIP  admin checks (EXPECTED_ADMIN not set)")

passed = sum(1 for ok, _ in results if ok)
print(f"\n{passed}/{len(results)} checks passed")
sys.exit(0 if passed == len(results) else 1)
