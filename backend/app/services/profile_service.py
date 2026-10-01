"""ProfileService — local profiles only. No accounts, no email, no PII."""

from __future__ import annotations

import json
import re
import sqlite3
import unicodedata
import uuid
from typing import Any

from app.db.connection import query_all, query_one, transaction

NAME_RE = re.compile(r"^[\w\s\u0900-\u097F.\-']{1,24}$", re.UNICODE)
MAX_NAME_LENGTH = 24
# Read from configuration rather than a constant: on a public server the cap
# is a real ceiling on how many people can use the account-free path, and 12 is
# a sensible default for one family sharing a tablet, not for a whole class.
def _limits() -> tuple[bool, int]:
    from app.config.settings import get_settings

    s = get_settings()
    return s.allow_local_profiles, s.max_local_profiles


class ProfileError(ValueError):
    pass


def _clean_name(raw: str) -> str:
    name = unicodedata.normalize("NFKC", (raw or "").strip())
    name = re.sub(r"\s+", " ", name)
    if not name:
        raise ProfileError("Profile name cannot be empty")
    if len(name) > MAX_NAME_LENGTH:
        raise ProfileError(f"Profile name must be {MAX_NAME_LENGTH} characters or fewer")
    if not NAME_RE.match(name):
        raise ProfileError("Profile name may contain letters, numbers, spaces, . _ - and ' only")
    return name


class ProfileService:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def list(self) -> list[dict[str, Any]]:
        rows = query_all(
            self.conn,
            """SELECT p.*, 
                      (SELECT COUNT(*) FROM attempts a WHERE a.profile_id = p.id) AS answered,
                      (SELECT COALESCE(SUM(a.is_correct),0) FROM attempts a WHERE a.profile_id = p.id) AS correct,
                      (SELECT COUNT(*) FROM sessions s WHERE s.profile_id = p.id AND s.finished_at IS NOT NULL) AS sessions
               FROM profiles p ORDER BY p.is_active DESC, p.xp_total DESC, p.created_at ASC"""
        )
        out = []
        for row in rows:
            answered = int(row["answered"] or 0)
            correct = int(row["correct"] or 0)
            out.append(
                {
                    "id": row["id"],
                    "display_name": row["display_name"],
                    "avatar": row["avatar"],
                    "is_active": bool(row["is_active"]),
                    "xp_total": row["xp_total"],
                    "level": row["level"],
                    "day_streak": row["streak_day_count"],
                    "questions_answered": answered,
                    "accuracy": (correct / answered) if answered else 0.0,
                    "sessions": int(row["sessions"] or 0),
                    "settings": json.loads(row["settings_json"] or "{}"),
                    "online_enabled": bool(row["online_enabled"]),
                    "public_handle": row["public_handle"],
                    "created_at": row["created_at"],
                }
            )
        return out

    def get(self, profile_id: str) -> dict[str, Any] | None:
        row = query_one(self.conn, "SELECT * FROM profiles WHERE id = ?", (profile_id,))
        if row is None:
            return None
        return {
            "id": row["id"],
            "display_name": row["display_name"],
            "avatar": row["avatar"],
            "is_active": bool(row["is_active"]),
            "xp_total": row["xp_total"],
            "level": row["level"],
            "day_streak": row["streak_day_count"],
            "last_active_day": row["last_active_day"],
            "settings": json.loads(row["settings_json"] or "{}"),
            "online_enabled": bool(row["online_enabled"]),
            "public_handle": row["public_handle"],
        }

    def create(self, display_name: str, avatar: str | None = None) -> dict[str, Any]:
        name = _clean_name(display_name)
        allowed, cap = _limits()
        if not allowed:
            raise ProfileError(
                "Account-free profiles are disabled on this server. Create an account to save your progress."
            )
        # The cap counts only UNCLAIMED profiles. Ones already attached to an
        # account are that person's data and must not consume a stranger's
        # allowance - otherwise a popular server would lock out anonymous
        # visitors because of how many people had signed up.
        total = query_one(self.conn, "SELECT COUNT(*) AS n FROM profiles")
        unclaimed = query_one(
            self.conn, "SELECT COUNT(*) AS n FROM profiles WHERE user_id IS NULL"
        )
        if unclaimed and int(unclaimed["n"]) >= cap:
            raise ProfileError(f"At most {cap} account-free profiles on this server")

        profile_id = f"p_{uuid.uuid4().hex[:12]}"
        is_first = int(total["n"]) == 0 if total else True

        with transaction(self.conn):
            if is_first:
                self.conn.execute("UPDATE profiles SET is_active = 0")
            self.conn.execute(
                """INSERT INTO profiles (id, display_name, avatar, is_active, settings_json)
                   VALUES (?, ?, ?, ?, ?)""",
                (profile_id, name, avatar or name[:1].upper(), int(is_first), json.dumps(_default_settings())),
            )

        return self.get(profile_id) or {"id": profile_id, "display_name": name}

    def update(self, profile_id: str, *, display_name: str | None = None, avatar: str | None = None,
               settings: dict[str, Any] | None = None, online_enabled: bool | None = None,
               public_handle: str | None = None) -> dict[str, Any] | None:
        existing = self.get(profile_id)
        if existing is None:
            return None

        assignments: list[str] = []
        params: list[Any] = []

        if display_name is not None:
            assignments.append("display_name = ?")
            params.append(_clean_name(display_name))
        if avatar is not None:
            assignments.append("avatar = ?")
            params.append(avatar[:4])
        if settings is not None:
            merged = {**existing["settings"], **_sanitise_settings(settings)}
            assignments.append("settings_json = ?")
            params.append(json.dumps(merged, ensure_ascii=False))
        if online_enabled is not None:
            # Opt-in only, and a handle is mandatory before anything leaves the machine.
            if online_enabled and not (public_handle or existing["public_handle"]):
                raise ProfileError("A public handle is required before enabling online features")
            assignments.append("online_enabled = ?")
            params.append(int(online_enabled))
        if public_handle is not None:
            assignments.append("public_handle = ?")
            params.append(_clean_name(public_handle))

        if not assignments:
            return existing

        assignments.append("updated_at = datetime('now')")
        params.append(profile_id)
        with transaction(self.conn):
            self.conn.execute(f"UPDATE profiles SET {', '.join(assignments)} WHERE id = ?", tuple(params))
        return self.get(profile_id)

    def set_active(self, profile_id: str) -> dict[str, Any] | None:
        if self.get(profile_id) is None:
            return None
        with transaction(self.conn):
            self.conn.execute("UPDATE profiles SET is_active = 0")
            self.conn.execute("UPDATE profiles SET is_active = 1, updated_at = datetime('now') WHERE id = ?", (profile_id,))
        return self.get(profile_id)

    def active(self) -> dict[str, Any] | None:
        row = query_one(self.conn, "SELECT id FROM profiles WHERE is_active = 1 ORDER BY updated_at DESC LIMIT 1")
        return self.get(row["id"]) if row else None

    def delete(self, profile_id: str) -> bool:
        with transaction(self.conn):
            cursor = self.conn.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
        return cursor.rowcount > 0


def _default_settings() -> dict[str, Any]:
    return {
        "theme": "dark",
        "sound": True,
        "haptics": True,
        "reduce_motion": False,
        "show_explanation": "on_wrong",
        "keyboard_first": True,
        "auto_next_ms": 700,
    }


_ALLOWED_SETTINGS = {"theme", "sound", "haptics", "reduce_motion", "show_explanation", "keyboard_first", "auto_next_ms"}


def _sanitise_settings(raw: dict[str, Any]) -> dict[str, Any]:
    """Whitelist keys and clamp values — settings come from the client."""
    clean: dict[str, Any] = {}
    for key, value in raw.items():
        if key not in _ALLOWED_SETTINGS:
            continue
        if key == "auto_next_ms":
            clean[key] = max(200, min(3000, int(value)))
        elif key == "theme":
            clean[key] = value if value in {"dark", "light", "system"} else "dark"
        elif key == "show_explanation":
            clean[key] = value if value in {"always", "on_wrong", "never"} else "on_wrong"
        elif isinstance(value, bool):
            clean[key] = value
    return clean
