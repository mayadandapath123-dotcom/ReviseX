"""Admin: platform usage, per-student stats, and supervised account access.

Two rules shaped this module.

First, nothing here is reachable without `users.is_admin`. The dependency that
guards the router checks that flag on every request rather than once per
session, so demoting an admin takes effect immediately instead of at their next
login.

Second, entering another person's account is treated as the sensitive act it
is. It writes an audit row that application code never deletes, issues a
short-lived token instead of a normal 30-day one, and is surfaced in the UI as
a persistent banner. An owner supporting students is a legitimate reason to
have this; an unlogged, unlabelled, permanent back door is not.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from app.db.connection import query_all, query_one

IMPERSONATION_TTL_MINUTES = 120
ONLINE_WINDOW_MINUTES = 5

# Presence writes are throttled per process. A single UPDATE per request would
# add a network round trip to everything, which on a remote database costs more
# than the request itself. One worker per container on the free tier makes an
# in-process cache adequate; it degrades to "slightly stale last_seen", never
# to incorrect data.
_last_seen_written: dict[str, float] = {}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(6)}"


def touch_presence(conn: Any, user_id: str) -> None:
    """Record that a user was seen, at most once a minute."""
    import time

    now = time.monotonic()
    if now - _last_seen_written.get(user_id, 0.0) < 60.0:
        return
    _last_seen_written[user_id] = now
    conn.execute(
        "UPDATE users SET last_seen_at = ? WHERE id = ?", (_iso(_now()), user_id)
    )
    conn.commit()


class AdminService:
    def __init__(self, conn: Any):
        self.conn = conn

    # -- authorisation -----------------------------------------------------

    def is_admin(self, user_id: str) -> bool:
        row = query_one(self.conn, "SELECT is_admin FROM users WHERE id = ?", (user_id,))
        return bool(row and int(row["is_admin"] or 0))

    def bootstrap_admins(self, usernames: set[str]) -> list[str]:
        """Promote the usernames listed in ADMIN_USERNAMES.

        Idempotent and safe to run on every boot: the first admin cannot be
        promoted by an existing admin, so it has to come from configuration.
        """
        promoted = []
        for username in usernames:
            row = query_one(
                self.conn, "SELECT id, is_admin FROM users WHERE username = ?", (username,)
            )
            if row and not int(row["is_admin"] or 0):
                self.conn.execute("UPDATE users SET is_admin = 1 WHERE id = ?", (row["id"],))
                promoted.append(username)
        if promoted:
            self.conn.commit()
        return promoted

    # -- platform overview -------------------------------------------------

    def overview(self) -> dict[str, Any]:
        online_cutoff = _iso(_now() - timedelta(minutes=ONLINE_WINDOW_MINUTES))
        today = _now().strftime("%Y-%m-%d")

        users = query_one(self.conn, "SELECT COUNT(*) AS n FROM users") or {"n": 0}
        online = query_one(
            self.conn,
            "SELECT COUNT(*) AS n FROM users WHERE last_seen_at IS NOT NULL AND last_seen_at >= ?",
            (online_cutoff,),
        ) or {"n": 0}
        admins = query_one(
            self.conn, "SELECT COUNT(*) AS n FROM users WHERE is_admin = 1"
        ) or {"n": 0}
        google_linked = query_one(
            self.conn, "SELECT COUNT(*) AS n FROM users WHERE google_sub IS NOT NULL"
        ) or {"n": 0}

        # Attempts are timestamped as 'YYYY-MM-DD HH:MM:SS' by the adapter, so a
        # string prefix comparison is a valid and index-friendly day filter on
        # both backends.
        answered_today = query_one(
            self.conn, "SELECT COUNT(*) AS n FROM attempts WHERE created_at LIKE ?", (f"{today}%",)
        ) or {"n": 0}
        answered_total = query_one(self.conn, "SELECT COUNT(*) AS n FROM attempts") or {"n": 0}
        active_today = query_one(
            self.conn,
            "SELECT COUNT(DISTINCT profile_id) AS n FROM attempts WHERE created_at LIKE ?",
            (f"{today}%",),
        ) or {"n": 0}
        seen_today = query_one(
            self.conn,
            "SELECT COUNT(*) AS n FROM users WHERE last_seen_at LIKE ?",
            (f"{today}%",),
        ) or {"n": 0}
        questions = query_one(
            self.conn, "SELECT COUNT(*) AS n FROM questions WHERE status='approved'"
        ) or {"n": 0}

        return {
            "users_total": int(users["n"]),
            "users_online_now": int(online["n"]),
            "users_seen_today": int(seen_today["n"]),
            "users_active_today": int(active_today["n"]),
            "admins": int(admins["n"]),
            "google_linked": int(google_linked["n"]),
            "answers_today": int(answered_today["n"]),
            "answers_total": int(answered_total["n"]),
            "questions_available": int(questions["n"]),
            "online_window_minutes": ONLINE_WINDOW_MINUTES,
            "server_time": _iso(_now()),
        }

    # -- student list ------------------------------------------------------

    def list_users(
        self, search: str = "", sort: str = "last_seen", limit: int = 50, offset: int = 0
    ) -> dict[str, Any]:
        """Every account with the numbers an owner actually asks for."""
        allowed_sorts = {
            "last_seen": "COALESCE(u.last_seen_at, '') DESC",
            "xp": "COALESCE(p.xp_total, 0) DESC",
            "streak": "COALESCE(p.streak_day_count, 0) DESC",
            "answered": "COALESCE(stats.answered, 0) DESC",
            "username": "u.username ASC",
            "created": "u.created_at DESC",
        }
        order = allowed_sorts.get(sort, allowed_sorts["last_seen"])
        limit = min(max(limit, 1), 200)
        offset = max(offset, 0)

        where = "WHERE u.is_active = 1"
        params: list[Any] = []
        term = (search or "").strip().lower()
        if term:
            where += " AND (lower(u.username) LIKE ? OR lower(COALESCE(p.display_name,'')) LIKE ? OR lower(COALESCE(u.google_email,'')) LIKE ?)"
            params += [f"%{term}%", f"%{term}%", f"%{term}%"]

        rows = query_all(
            self.conn,
            f"""SELECT u.id AS user_id, u.username, u.google_email, u.provider, u.is_admin,
                       u.created_at, u.last_login_at, u.last_seen_at,
                       p.id AS profile_id, p.display_name, p.level, p.xp_total,
                       p.streak_day_count, p.last_active_day,
                       COALESCE(stats.answered, 0) AS answered,
                       COALESCE(stats.correct, 0) AS correct,
                       COALESCE(sess.sessions, 0) AS sessions
                FROM users u
                LEFT JOIN profiles p ON p.user_id = u.id
                LEFT JOIN (
                    SELECT profile_id,
                           COUNT(id) AS answered,
                           SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) AS correct
                    FROM attempts GROUP BY profile_id
                ) stats ON stats.profile_id = p.id
                LEFT JOIN (
                    SELECT profile_id, COUNT(id) AS sessions
                    FROM sessions GROUP BY profile_id
                ) sess ON sess.profile_id = p.id
                {where}
                ORDER BY {order}
                LIMIT ? OFFSET ?""",
            (*params, limit, offset),
        )
        total = query_one(self.conn, f"SELECT COUNT(*) AS n FROM users u LEFT JOIN profiles p ON p.user_id = u.id {where}", tuple(params))

        online_cutoff = _iso(_now() - timedelta(minutes=ONLINE_WINDOW_MINUTES))
        out = []
        for row in rows:
            answered = int(row["answered"] or 0)
            correct = int(row["correct"] or 0)
            last_seen = row["last_seen_at"]
            out.append({
                "user_id": row["user_id"],
                "username": row["username"],
                "display_name": row["display_name"] or row["username"],
                "google_email": row["google_email"],
                "provider": row["provider"] or "password",
                "is_admin": bool(int(row["is_admin"] or 0)),
                "profile_id": row["profile_id"],
                "level": int(row["level"] or 1),
                "xp_total": int(row["xp_total"] or 0),
                "streak_day_count": int(row["streak_day_count"] or 0),

                "answers": answered,
                "accuracy": round(correct / answered, 4) if answered else None,
                "sessions": int(row["sessions"] or 0),
                "created_at": row["created_at"],
                "last_login_at": row["last_login_at"],
                "last_seen_at": last_seen,
                "online_now": bool(last_seen and last_seen >= online_cutoff),
            })
        return {"users": out, "total": int(total["n"]) if total else 0, "limit": limit, "offset": offset}

    def user_detail(self, user_id: str) -> dict[str, Any] | None:
        listing = self.list_users(limit=200)
        for entry in listing["users"]:
            if entry["user_id"] == user_id:
                recent = query_all(
                    self.conn,
                    """SELECT s.mode_key, s.started_at, s.score, s.accuracy,
                              s.questions_answered, s.correct_count
                       FROM sessions s JOIN profiles p ON p.id = s.profile_id
                       WHERE p.user_id = ? ORDER BY s.started_at DESC LIMIT 10""",
                    (user_id,),
                )
                entry["recent_sessions"] = [dict(r) for r in recent]
                return entry
        return None

    # -- supervised account access ----------------------------------------

    def impersonate(self, admin_user_id: str, target_user_id: str) -> dict[str, Any]:
        """Issue a short-lived token for another account, and record it.

        The target's own tokens are untouched and their password is never
        revealed - this mints a new session rather than recovering an old one.
        """
        if not self.is_admin(admin_user_id):
            raise PermissionError("Admin access required.")
        target = query_one(
            self.conn, "SELECT id, username FROM users WHERE id = ? AND is_active = 1",
            (target_user_id,),
        )
        if target is None:
            raise LookupError("That account does not exist.")

        admin = query_one(self.conn, "SELECT username FROM users WHERE id = ?", (admin_user_id,))
        token = secrets.token_urlsafe(32)
        self.conn.execute(
            "INSERT INTO auth_tokens (token_hash, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (
                hashlib.sha256(token.encode()).hexdigest(),
                target_user_id,
                _iso(_now()),
                _iso(_now() + timedelta(minutes=IMPERSONATION_TTL_MINUTES)),
            ),
        )
        self.conn.execute(
            """INSERT INTO admin_audit (id, admin_user_id, action, target_user_id, detail, created_at)
               VALUES (?, ?, 'impersonate', ?, ?, ?)""",
            (
                _new_id("aud"),
                admin_user_id,
                target_user_id,
                f"{admin['username'] if admin else admin_user_id} entered {target['username']}'s account",
                _iso(_now()),
            ),
        )
        self.conn.commit()
        return {
            "token": token,
            "user_id": target_user_id,
            "username": target["username"],
            "expires_in_minutes": IMPERSONATION_TTL_MINUTES,
        }

    def audit_log(self, limit: int = 100) -> list[dict[str, Any]]:
        rows = query_all(
            self.conn,
            """SELECT a.id, a.action, a.detail, a.created_at,
                      ad.username AS admin_username, tu.username AS target_username
               FROM admin_audit a
               LEFT JOIN users ad ON ad.id = a.admin_user_id
               LEFT JOIN users tu ON tu.id = a.target_user_id
               ORDER BY a.created_at DESC LIMIT ?""",
            (min(max(limit, 1), 500),),
        )
        return [dict(r) for r in rows]
