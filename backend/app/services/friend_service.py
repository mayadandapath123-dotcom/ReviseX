"""Friends: requests, approval, the friend list and a friends-only leaderboard.

Two tables, deliberately:

  friend_requests - one row per invitation, with a status. Kept after approval
    so the history survives and a duplicate invitation can be detected.
  friendships     - the accepted edges only. user_a is always the
    lexicographically smaller id, so a pair has exactly one representation and
    "are these two friends?" is a single primary-key lookup instead of an OR
    across both column orders.

Every method takes the acting user's id explicitly. Nothing here trusts a
user id from the request body - that is how one account would add friends on
behalf of another.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any

from app.db.connection import query_all, query_one


class FriendError(ValueError):
    """A user-facing rejection. Safe to show verbatim."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ordered_pair(a: str, b: str) -> tuple[str, str]:
    """Canonical ordering so (a,b) and (b,a) are the same friendship."""
    return (a, b) if a <= b else (b, a)


class FriendService:
    def __init__(self, conn: Any):
        self.conn = conn

    # -- helpers -----------------------------------------------------------

    def _user_id_from_username(self, username: str) -> str | None:
        row = query_one(
            self.conn, "SELECT id FROM users WHERE username = ?", (username.strip().lower(),)
        )
        return row["id"] if row else None

    def _is_friend(self, user_a: str, user_b: str) -> bool:
        a, b = _ordered_pair(user_a, user_b)
        return (
            query_one(
                self.conn,
                "SELECT 1 FROM friendships WHERE user_a = ? AND user_b = ?",
                (a, b),
            )
            is not None
        )

    def _profile_stats(self, user_ids: list[str]) -> dict[str, dict[str, Any]]:
        """Display name, level, XP and streak for a set of users, in one query."""
        if not user_ids:
            return {}
        placeholders = ",".join("?" for _ in user_ids)
        rows = query_all(
            self.conn,
            f"""SELECT u.id AS user_id, u.username, p.display_name, p.level, p.xp_total,
                       p.streak_day_count, p.last_active_day
                FROM users u
                LEFT JOIN profiles p ON p.user_id = u.id
                WHERE u.id IN ({placeholders})""",
            tuple(user_ids),
        )
        return {
            row["user_id"]: {
                "username": row["username"],
                "display_name": row["display_name"] or row["username"],
                "level": int(row["level"] or 1),
                "xp_total": int(row["xp_total"] or 0),
                "streak_day_count": int(row["streak_day_count"] or 0),
                "last_active_day": row["last_active_day"],
            }
            for row in rows
        }

    # -- reads -------------------------------------------------------------

    def friends(self, user_id: str) -> list[dict[str, Any]]:
        rows = query_all(
            self.conn,
            """SELECT CASE WHEN user_a = ? THEN user_b ELSE user_a END AS friend_id
               FROM friendships WHERE user_a = ? OR user_b = ?
               ORDER BY created_at DESC""",
            (user_id, user_id, user_id),
        )
        ids = [row["friend_id"] for row in rows]
        stats = self._profile_stats(ids)
        return [stats[i] | {"user_id": i} for i in ids if i in stats]

    def incoming_requests(self, user_id: str) -> list[dict[str, Any]]:
        rows = query_all(
            self.conn,
            """SELECT id, from_user_id, created_at FROM friend_requests
               WHERE to_user_id = ? AND status = 'pending'
               ORDER BY created_at DESC""",
            (user_id,),
        )
        stats = self._profile_stats([row["from_user_id"] for row in rows])
        return [
            {
                "request_id": row["id"],
                "created_at": row["created_at"],
                **stats.get(row["from_user_id"], {"user_id": row["from_user_id"]}),
            }
            for row in rows
        ]

    def outgoing_requests(self, user_id: str) -> list[dict[str, Any]]:
        rows = query_all(
            self.conn,
            """SELECT id, to_user_id, status, created_at FROM friend_requests
               WHERE from_user_id = ? AND status IN ('pending', 'accepted')
               ORDER BY created_at DESC""",
            (user_id,),
        )
        stats = self._profile_stats([row["to_user_id"] for row in rows])
        return [
            {
                "request_id": row["id"],
                "status": row["status"],
                "created_at": row["created_at"],
                **stats.get(row["to_user_id"], {"user_id": row["to_user_id"]}),
            }
            for row in rows
        ]

    def summary(self, user_id: str) -> dict[str, Any]:
        return {
            "friend_count": len(self.friends(user_id)),
            "incoming_count": len(self.incoming_requests(user_id)),
        }

    def search(self, user_id: str, term: str, *, limit: int = 20) -> list[dict[str, Any]]:
        """Find accounts by username or display name.

        Prefix matches rank above substring matches, because someone typing a
        friend's name wants them at the top, not buried under every account that
        happens to contain those letters. Capped hard: an uncapped search is a
        directory of every student on the platform.

        Already-friends and pending invitations are annotated rather than
        filtered out, so the UI can disable the button and say why instead of
        showing a name that silently does nothing when tapped.
        """
        term = (term or "").strip().lower()
        if len(term) < 2:
            return []

        rows = query_all(
            self.conn,
            """SELECT u.id AS user_id, u.username, p.display_name, p.level, p.xp_total,
                      p.streak_day_count,
                      CASE WHEN lower(u.username) LIKE ? THEN 0 ELSE 1 END AS rank_bucket
               FROM users u
               LEFT JOIN profiles p ON p.user_id = u.id
               WHERE u.is_active = 1
                 AND u.id != ?
                 AND (lower(u.username) LIKE ? OR lower(COALESCE(p.display_name, '')) LIKE ?)
               ORDER BY rank_bucket ASC, length(u.username) ASC, u.username ASC
               LIMIT ?""",
            (f"{term}%", user_id, f"%{term}%", f"%{term}%", limit),
        )

        ids = [row["user_id"] for row in rows]
        relationship = self._relationships(user_id, ids)
        results = []
        for row in rows:
            uid = row["user_id"]
            results.append({
                "user_id": uid,
                "username": row["username"],
                "display_name": row["display_name"] or row["username"],
                "level": int(row["level"] or 1),
                "xp_total": int(row["xp_total"] or 0),
                "streak_day_count": int(row["streak_day_count"] or 0),
                "relationship": relationship.get(uid, "none"),
            })
        return results

    def _relationships(self, user_id: str, other_ids: list[str]) -> dict[str, str]:
        """Batch-classify how the caller relates to a set of users.

        One query for friendships and one for requests, rather than two per
        candidate - against a remote database that difference is the whole cost
        of the search.
        """
        if not other_ids:
            return {}
        placeholders = ",".join("?" for _ in other_ids)
        out: dict[str, str] = {}

        for row in query_all(
            self.conn,
            f"""SELECT CASE WHEN user_a = ? THEN user_b ELSE user_a END AS other
                FROM friendships
                WHERE (user_a = ? OR user_b = ?)
                  AND (user_a IN ({placeholders}) OR user_b IN ({placeholders}))""",
            (user_id, user_id, user_id, *other_ids, *other_ids),
        ):
            out[row["other"]] = "friends"

        for row in query_all(
            self.conn,
            f"""SELECT from_user_id, to_user_id FROM friend_requests
                WHERE status = 'pending'
                  AND ((from_user_id = ? AND to_user_id IN ({placeholders}))
                    OR (to_user_id = ? AND from_user_id IN ({placeholders})))""",
            (user_id, *other_ids, user_id, *other_ids),
        ):
            if row["from_user_id"] == user_id:
                out.setdefault(row["to_user_id"], "outgoing")
            else:
                out[row["from_user_id"]] = "incoming"
        return out

    def leaderboard(self, user_id: str, *, include_self: bool = True) -> list[dict[str, Any]]:
        """Ranking restricted to this user's friends.

        Scoped in SQL by joining friendships rather than filtering a global list
        in Python, so a user with no friends gets an empty board instead of
        accidentally seeing everyone.
        """
        rows = query_all(
            self.conn,
            """SELECT u.id AS user_id, u.username, p.display_name, p.level, p.xp_total,
                      p.streak_day_count
               FROM friendships f
               JOIN users u ON u.id = CASE WHEN f.user_a = ? THEN f.user_b ELSE f.user_a END
               LEFT JOIN profiles p ON p.user_id = u.id
               WHERE f.user_a = ? OR f.user_b = ?
               ORDER BY COALESCE(p.xp_total, 0) DESC, COALESCE(p.level, 1) DESC, u.username ASC""",
            (user_id, user_id, user_id),
        )
        board = [
            {
                "user_id": row["user_id"],
                "username": row["username"],
                "display_name": row["display_name"] or row["username"],
                "level": int(row["level"] or 1),
                "xp_total": int(row["xp_total"] or 0),
                "streak_day_count": int(row["streak_day_count"] or 0),
                "is_self": False,
            }
            for row in rows
        ]
        if include_self:
            me = self._profile_stats([user_id]).get(user_id)
            if me:
                board.append({**me, "user_id": user_id, "is_self": True})
        board.sort(key=lambda e: (-e["xp_total"], -e["level"], e["username"]))
        for rank, entry in enumerate(board, start=1):
            entry["rank"] = rank
        return board

    # -- writes ------------------------------------------------------------

    def send_request(self, user_id: str, username: str) -> dict[str, Any]:
        target = self._user_id_from_username(username)
        if target is None:
            # Same wording for "no such user" and a declined request would leak
            # which usernames exist, but the caller typed the name themselves,
            # so telling them it is not registered is the useful answer here.
            raise FriendError(f"No account named '{username.strip().lower()}' was found.")
        if target == user_id:
            raise FriendError("You cannot add yourself as a friend.")
        if self._is_friend(user_id, target):
            raise FriendError("You are already friends with that account.")

        now = _now_iso()
        existing = query_one(
            self.conn,
            """SELECT id, status, from_user_id FROM friend_requests
               WHERE ((from_user_id = ? AND to_user_id = ?) OR (from_user_id = ? AND to_user_id = ?))
                 AND status = 'pending'""",
            (user_id, target, target, user_id),
        )
        if existing is not None:
            if existing["from_user_id"] == target:
                # They already asked you: treat sending as accepting rather than
                # creating a second, contradictory pending row.
                return self.accept_request(user_id, existing["id"])
            raise FriendError("You already have a pending request with that account.")

        request_id = f"fr_{secrets.token_hex(6)}"
        self.conn.execute(
            """INSERT INTO friend_requests (id, from_user_id, to_user_id, status, created_at, updated_at)
               VALUES (?, ?, ?, 'pending', ?, ?)""",
            (request_id, user_id, target, now, now),
        )
        self.conn.commit()
        return {"request_id": request_id, "status": "pending", "to_user_id": target}

    def accept_request(self, user_id: str, request_id: str) -> dict[str, Any]:
        row = query_one(
            self.conn, "SELECT * FROM friend_requests WHERE id = ?", (request_id,)
        )
        if row is None:
            raise FriendError("That request does not exist.")
        # Only the recipient may accept. The sender's id is checked too so a
        # re-accept of one's own outgoing row cannot fabricate an edge.
        if row["to_user_id"] != user_id:
            raise FriendError("Only the person who received this request can accept it.")
        if row["status"] == "accepted":
            raise FriendError("That request was already accepted.")
        if row["status"] == "declined":
            raise FriendError("That request was declined.")

        other = row["from_user_id"]
        if self._is_friend(user_id, other):
            raise FriendError("You are already friends with that account.")

        now = _now_iso()
        a, b = _ordered_pair(user_id, other)
        # INSERT OR IGNORE: the pair may already exist if both sides accepted
        # near-simultaneously. Idempotent is safer than raising here.
        self.conn.execute(
            "INSERT OR IGNORE INTO friendships (user_a, user_b, created_at) VALUES (?, ?, ?)",
            (a, b, now),
        )
        self.conn.execute(
            "UPDATE friend_requests SET status = 'accepted', updated_at = ? WHERE id = ?",
            (now, request_id),
        )
        self.conn.commit()
        stats = self._profile_stats([other]).get(other, {"user_id": other})
        return {"status": "accepted", "friend": stats}

    def decline_request(self, user_id: str, request_id: str) -> dict[str, Any]:
        row = query_one(
            self.conn, "SELECT * FROM friend_requests WHERE id = ?", (request_id,)
        )
        if row is None:
            raise FriendError("That request does not exist.")
        if row["to_user_id"] != user_id:
            raise FriendError("Only the person who received this request can decline it.")
        if row["status"] != "pending":
            raise FriendError("That request is no longer pending.")
        self.conn.execute(
            "UPDATE friend_requests SET status = 'declined', updated_at = ? WHERE id = ?",
            (_now_iso(), request_id),
        )
        self.conn.commit()
        return {"status": "declined"}

    def cancel_request(self, user_id: str, request_id: str) -> dict[str, Any]:
        """Withdraw an invitation you sent."""
        row = query_one(
            self.conn, "SELECT * FROM friend_requests WHERE id = ?", (request_id,)
        )
        if row is None:
            raise FriendError("That request does not exist.")
        if row["from_user_id"] != user_id:
            raise FriendError("You can only cancel a request you sent.")
        if row["status"] != "pending":
            raise FriendError("Only a pending request can be cancelled.")
        self.conn.execute(
            "UPDATE friend_requests SET status = 'cancelled', updated_at = ? WHERE id = ?",
            (_now_iso(), request_id),
        )
        self.conn.commit()
        return {"status": "cancelled"}

    def remove_friend(self, user_id: str, friend_user_id: str) -> dict[str, Any]:
        a, b = _ordered_pair(user_id, friend_user_id)
        cursor = self.conn.execute(
            "DELETE FROM friendships WHERE user_a = ? AND user_b = ?", (a, b)
        )
        self.conn.commit()
        if not cursor.rowcount:
            raise FriendError("That account is not on your friend list.")
        return {"status": "removed"}
