"""Accounts: password hashing, signup, login and bearer tokens.

Security decisions, all deliberate:

  * PBKDF2-HMAC-SHA256 with 210,000 iterations and a 16-byte per-user salt,
    from the standard library. No new dependency and no hand-rolled crypto —
    hashlib.pbkdf2_hmac is the same primitive bcrypt-style schemes lean on,
    and 210k iterations is OWASP's current floor for PBKDF2-SHA256.
  * Passwords are never stored, logged, or returned by any function here.
    The stored form is `pbkdf2_sha256$iterations$salt$hash`.
  * Session tokens are 32 bytes from secrets.token_urlsafe. Only the SHA-256
    of the token is stored, so a database leak does not hand out live sessions.
  * Verification uses hmac.compare_digest to avoid leaking a password's
    correctness through response timing.
  * Usernames are case-insensitive: stored lowercase, matched lowercase, so
    "Sayan" and "sayan" cannot become two separate accounts.
"""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from app.db.connection import query_one

PBKDF2_ITERATIONS = 210_000
SALT_BYTES = 16
TOKEN_TTL_DAYS = 30
USERNAME_RE = re.compile(r"^[a-z0-9_]{3,24}$")
MIN_PASSWORD_LENGTH = 6


class AuthError(ValueError):
    """A user-facing authentication failure. The message is safe to show."""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(6)}"


# --------------------------------------------------------------------------
# Passwords
# --------------------------------------------------------------------------


def hash_password(password: str, *, iterations: int = PBKDF2_ITERATIONS) -> str:
    salt = secrets.token_bytes(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """Constant-time check against a stored hash. Returns False on any malformation."""
    try:
        scheme, iterations, salt_hex, hash_hex = stored.split("$")
        if scheme != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations)
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(digest.hex(), hash_hex)


# --------------------------------------------------------------------------
# Tokens
# --------------------------------------------------------------------------


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _issue_token(conn: Any, user_id: str) -> str:
    token = secrets.token_urlsafe(32)
    conn.execute(
        "INSERT INTO auth_tokens (token_hash, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
        (
            _hash_token(token),
            user_id,
            _iso(_now()),
            _iso(_now() + timedelta(days=TOKEN_TTL_DAYS)),
        ),
    )
    return token


def purge_expired_tokens(conn: Any) -> int:
    """Drop tokens past their expiry. Cheap enough to call on login."""
    cursor = conn.execute("DELETE FROM auth_tokens WHERE expires_at < ?", (_iso(_now()),))
    return cursor.rowcount or 0


# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------


def _is_configured_admin(username: str) -> bool:
    """True when this username is listed in ADMIN_USERNAMES.

    Checked at signup, not only at boot. Bootstrapping solely at startup would
    force an awkward sequence - deploy, sign up, then restart the service - and
    the person configuring the platform would have no way to discover that.
    """
    from app.config.settings import get_settings

    return username.strip().lower() in get_settings().admin_username_set


def validate_username(username: str) -> str:
    cleaned = (username or "").strip().lower()
    if not USERNAME_RE.match(cleaned):
        raise AuthError(
            "Username must be 3-24 characters using only letters, numbers and underscores."
        )
    return cleaned


def validate_password(password: str) -> str:
    if not password or len(password) < MIN_PASSWORD_LENGTH:
        raise AuthError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    if len(password) > 200:
        raise AuthError("Password must be under 200 characters.")
    return password


# --------------------------------------------------------------------------
# Service
# --------------------------------------------------------------------------


class AuthService:
    def __init__(self, conn: Any):
        self.conn = conn

    # -- reads -------------------------------------------------------------

    def user_by_username(self, username: str) -> dict[str, Any] | None:
        row = query_one(
            self.conn, "SELECT * FROM users WHERE username = ?", (username.strip().lower(),)
        )
        return dict(row) if row else None

    def user_by_id(self, user_id: str) -> dict[str, Any] | None:
        row = query_one(self.conn, "SELECT * FROM users WHERE id = ?", (user_id,))
        return dict(row) if row else None

    def user_from_token(self, token: str | None) -> dict[str, Any] | None:
        """Resolve a bearer token to its user, or None if absent/expired/unknown."""
        if not token:
            return None
        row = query_one(
            self.conn,
            """SELECT u.* FROM auth_tokens t
               JOIN users u ON u.id = t.user_id
               WHERE t.token_hash = ? AND t.expires_at >= ? AND u.is_active = 1""",
            (_hash_token(token), _iso(_now())),
        )
        if row is None:
            return None
        # Touching last_seen_at on every request would be a write per call;
        # it is only worth updating when the row is already being read.
        return dict(row)

    def profile_for_user(self, user_id: str) -> dict[str, Any] | None:
        row = query_one(self.conn, "SELECT * FROM profiles WHERE user_id = ?", (user_id,))
        return dict(row) if row else None

    # -- writes ------------------------------------------------------------

    def signup(
        self,
        username: str,
        password: str,
        display_name: str | None = None,
        claim_profile_id: str | None = None,
    ) -> dict[str, Any]:
        """Create an account and its profile in one step. Returns user + token.

        `claim_profile_id` adopts an existing profile that has no account yet.
        This is the upgrade path from local, account-free mode: a student who
        has been playing anonymously already has XP, streaks, mistakes and SRS
        history attached to that profile id, and creating a fresh profile on
        signup would strand all of it. Adopting keeps the history intact.

        The profile id acts as a capability - it is a 48-bit random secret the
        browser holds in localStorage - and only unclaimed profiles can be
        adopted, so this cannot be used to take over someone else's account.
        """
        clean_username = validate_username(username)
        clean_password = validate_password(password)

        if self.user_by_username(clean_username) is not None:
            raise AuthError("That username is already taken.")

        user_id = _new_id("u")
        now = _iso(_now())
        self.conn.execute(
            """INSERT INTO users (id, username, password_hash, created_at, last_login_at, is_active, is_admin)
               VALUES (?, ?, ?, ?, ?, 1, ?)""",
            (user_id, clean_username, hash_password(clean_password), now, now, int(_is_configured_admin(clean_username))),
        )

        # One user, one profile. The profile carries all learning data so the
        # rest of the app is unchanged; display_name defaults to the username.
        profile_id = self._claim_or_create_profile(user_id, clean_username, display_name, now, claim_profile_id)

        purge_expired_tokens(self.conn)
        token = _issue_token(self.conn, user_id)
        self.conn.commit()
        return {
            "token": token,
            "user": self._public_user(user_id, clean_username, now),
            "profile_id": profile_id,
        }

    def login(self, username: str, password: str) -> dict[str, Any]:
        user = self.user_by_username(username)
        # Verify against a dummy hash when the user is missing so a wrong
        # username and a wrong password take similar time.
        stored = user["password_hash"] if user else _DUMMY_HASH
        ok = verify_password(password, stored)
        if user is None or not ok or not int(user.get("is_active") or 0):
            raise AuthError("Incorrect username or password.")

        now = _iso(_now())
        self.conn.execute(
            "UPDATE users SET last_login_at = ? WHERE id = ?", (now, user["id"])
        )
        purge_expired_tokens(self.conn)
        token = _issue_token(self.conn, user["id"])
        self.conn.commit()

        profile = self.profile_for_user(user["id"])
        return {
            "token": token,
            "user": self._public_user(user["id"], user["username"], user.get("created_at")),
            "profile_id": profile["id"] if profile else None,
        }

    def logout(self, token: str | None) -> bool:
        if not token:
            return False
        cursor = self.conn.execute(
            "DELETE FROM auth_tokens WHERE token_hash = ?", (_hash_token(token),)
        )
        self.conn.commit()
        return bool(cursor.rowcount)

    def change_password(self, user_id: str, current: str, new: str) -> None:
        user = self.user_by_id(user_id)
        if user is None or not verify_password(current, user["password_hash"]):
            raise AuthError("Your current password is incorrect.")
        self.conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (hash_password(validate_password(new)), user_id),
        )
        # Invalidate every existing session: a password change is how someone
        # recovers an account, so old tokens must stop working.
        self.conn.execute("DELETE FROM auth_tokens WHERE user_id = ?", (user_id,))
        self.conn.commit()

    def _claim_or_create_profile(
        self,
        user_id: str,
        username: str,
        display_name: str | None,
        now: str,
        claim_profile_id: str | None,
    ) -> str:
        """Adopt an unclaimed local profile, or create a new one.

        A claim is validated strictly and then ignored rather than fatal: if the
        id is stale (database was reset) or already belongs to an account, the
        signup still succeeds with a fresh profile. Failing the whole signup
        over a localStorage id the student cannot inspect would be worse than
        quietly starting clean.
        """
        if claim_profile_id:
            row = query_one(
                self.conn, "SELECT id, user_id, display_name FROM profiles WHERE id = ?",
                (claim_profile_id,),
            )
            if row is not None and not row["user_id"]:
                self.conn.execute(
                    "UPDATE profiles SET user_id = ?, updated_at = ? WHERE id = ?",
                    (user_id, now, claim_profile_id),
                )
                return str(row["id"])

        profile_id = _new_id("p")
        self.conn.execute(
            """INSERT INTO profiles
                 (id, display_name, avatar, is_active, xp_total, level, streak_day_count,
                  user_id, created_at, updated_at)
               VALUES (?, ?, ?, 1, 0, 1, 0, ?, ?, ?)""",
            (profile_id, (display_name or username)[:24], None, user_id, now, now),
        )
        return profile_id

    @staticmethod
    def _public_user(user_id: str, username: str, created_at: Any) -> dict[str, Any]:
        """The only shape of a user that ever leaves the server. No hash, no token."""
        return {"id": user_id, "username": username, "created_at": created_at}


# Verifying against this costs the same as a real check, which keeps the
# username-enumeration timing signal out of the login endpoint.
_DUMMY_HASH = hash_password("timing-equaliser-not-a-real-password")
