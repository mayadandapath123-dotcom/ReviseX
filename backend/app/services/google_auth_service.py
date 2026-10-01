"""Google sign-in: OAuth 2.0 authorisation code flow, plus link and unlink.

Deliberate choices:

  * The userinfo endpoint is called with the access token instead of decoding
    the id_token ourselves. Verifying an RS256 JWT means fetching Google's
    rotating certs and checking kid/iss/aud/exp by hand - real crypto work that
    is easy to get subtly wrong. Asking Google over TLS returns the same
    identity claims and cannot be forged, because the access token came
    directly from Google's token endpoint over our own back-channel call.
  * Only the standard library is used for HTTP, so no new dependency.
  * `state` is stored server side, single-use, with a short expiry. Without it
    an attacker could complete their own OAuth flow in a victim's browser and
    bind the victim's session to the attacker's Google account.
  * Google's `sub` is the identity, never the email. Emails change; `sub` does
    not.
  * A Google-only account stores an unusable password sentinel rather than
    NULL, because the column is NOT NULL and SQLite cannot drop that
    constraint. The sentinel cannot be verified, so it is not a back door.
"""

from __future__ import annotations

import json
import secrets
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any

from app.config.settings import get_settings
from app.db.connection import query_one
from app.services.auth_service import AuthError, AuthService, _new_id

AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"

STATE_TTL_MINUTES = 10
SCOPES = "openid email profile"

# Stored as password_hash for accounts created by Google sign-in. It has no
# `$` separators, so verify_password() rejects it unconditionally: nobody can
# log in with a password against a Google-only account.
NO_PASSWORD = "!oauth-google-no-password"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


class GoogleNotConfigured(RuntimeError):
    """Raised when the feature is used without credentials set."""


class GoogleAuthError(AuthError):
    """A user-facing OAuth failure."""


def _post_form(url: str, data: dict[str, str], timeout: int = 20) -> dict[str, Any]:
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(
        url, data=body, method="POST", headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def _get_json(url: str, token: str, timeout: int = 20) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


class GoogleAuthService:
    def __init__(self, conn: Any, auth: AuthService):
        self.conn = conn
        self.auth = auth
        self.settings = get_settings()

    # -- configuration -----------------------------------------------------

    def status(self) -> dict[str, Any]:
        """What the frontend needs to decide whether to show the button."""
        return {
            "enabled": self.settings.google_enabled,
            "redirect_uri": self.settings.resolved_redirect_uri if self.settings.google_enabled else None,
        }

    def _require_configured(self) -> None:
        if not self.settings.google_enabled:
            raise GoogleNotConfigured(
                "Google sign-in is not configured on this server. Set GOOGLE_CLIENT_ID and "
                "GOOGLE_CLIENT_SECRET to enable it."
            )

    # -- state (CSRF) ------------------------------------------------------

    def create_state(self, kind: str, user_id: str | None = None) -> str:
        self._purge_states()
        state = secrets.token_urlsafe(24)
        self.conn.execute(
            """INSERT INTO oauth_states (state, kind, user_id, created_at, expires_at)
               VALUES (?, ?, ?, ?, ?)""",
            (state, kind, user_id, _iso(_now()), _iso(_now() + timedelta(minutes=STATE_TTL_MINUTES))),
        )
        self.conn.commit()
        return state

    def consume_state(self, state: str) -> dict[str, Any]:
        """Validate and burn a state value. Single use, so a replay fails."""
        row = query_one(
            self.conn,
            "SELECT * FROM oauth_states WHERE state = ? AND consumed_at IS NULL AND expires_at >= ?",
            (state, _iso(_now())),
        )
        if row is None:
            raise GoogleAuthError(
                "This sign-in attempt expired or was already used. Please try again."
            )
        self.conn.execute(
            "UPDATE oauth_states SET consumed_at = ? WHERE state = ?", (_iso(_now()), state)
        )
        self.conn.commit()
        return dict(row)

    def _purge_states(self) -> None:
        self.conn.execute(
            "DELETE FROM oauth_states WHERE expires_at < ?",
            (_iso(_now() - timedelta(minutes=1)),),
        )

    # -- the flow ----------------------------------------------------------

    def build_auth_url(self, kind: str, user_id: str | None = None) -> str:
        self._require_configured()
        state = self.create_state(kind, user_id)
        params = {
            "client_id": self.settings.google_client_id,
            "redirect_uri": self.settings.resolved_redirect_uri,
            "response_type": "code",
            "scope": SCOPES,
            "state": state,
            # Forces a real account choice instead of silently reusing whatever
            # session the browser has, which is what a student sharing a family
            # device needs.
            "prompt": "select_account",
            "access_type": "online",
            "include_granted_scopes": "true",
        }
        return f"{AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"

    def exchange_code(self, code: str) -> dict[str, Any]:
        """Trade the authorisation code for tokens, then fetch identity claims."""
        self._require_configured()
        try:
            tokens = _post_form(
                TOKEN_URL,
                {
                    "code": code,
                    "client_id": self.settings.google_client_id,
                    "client_secret": self.settings.google_client_secret,
                    "redirect_uri": self.settings.resolved_redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:300]
            raise GoogleAuthError(f"Google rejected the sign-in ({exc.code}). {detail}") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise GoogleAuthError("Could not reach Google to complete the sign-in.") from exc

        access_token = tokens.get("access_token")
        if not access_token:
            raise GoogleAuthError("Google did not return an access token.")

        try:
            info = _get_json(USERINFO_URL, access_token)
        except urllib.error.HTTPError as exc:
            raise GoogleAuthError(f"Google rejected the identity lookup ({exc.code}).") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise GoogleAuthError("Could not reach Google to confirm your identity.") from exc

        sub = info.get("sub")
        if not sub:
            raise GoogleAuthError("Google returned an identity without a subject id.")
        return {
            "sub": str(sub),
            "email": (info.get("email") or "").lower() or None,
            "email_verified": bool(info.get("email_verified")),
            "name": info.get("name") or None,
            "picture": info.get("picture") or None,
        }

    # -- account resolution ------------------------------------------------

    def user_by_google_sub(self, sub: str) -> dict[str, Any] | None:
        row = query_one(self.conn, "SELECT * FROM users WHERE google_sub = ?", (sub,))
        return dict(row) if row else None

    def _unique_username(self, email: str | None, name: str | None) -> str:
        """Derive an unused username from the Google identity.

        Google accounts still need a username here: it is what friends search
        for and what the leaderboard shows. Digits are appended until free,
        because a whole class may share a school email pattern.
        """
        base = ""
        if email and "@" in email:
            base = email.split("@")[0]
        elif name:
            base = "".join(ch for ch in name.lower() if ch.isalnum())
        base = "".join(ch for ch in base.lower() if ch.isalnum() or ch == "_").strip("_")[:20]
        if len(base) < 3:
            base = (base + "user")[:20]
        candidate = base
        for _ in range(50):
            if self.auth.user_by_username(candidate) is None:
                return candidate
            candidate = f"{base}{secrets.randbelow(9000) + 1000}"[:24]
        return f"{base}{secrets.token_hex(3)}"[:24]

    def sign_in_or_register(self, identity: dict[str, Any]) -> dict[str, Any]:
        """Google sign-in: existing linked account, or create one.

        Never merges into an account by matching email alone. Auto-merging on
        email would let anyone who controls a Google account with a colliding
        address walk into an existing student's progress. Linking is always an
        explicit act performed while signed in.
        """
        existing = self.user_by_google_sub(identity["sub"])
        if existing is not None:
            if not int(existing.get("is_active") or 0):
                raise GoogleAuthError("This account has been disabled.")
            return self._session(existing)

        username = self._unique_username(identity.get("email"), identity.get("name"))
        user_id = _new_id("u")
        now = _iso(_now())
        self.conn.execute(
            """INSERT INTO users
                 (id, username, password_hash, created_at, last_login_at, is_active,
                  google_sub, google_email, provider, last_seen_at, is_admin)
               VALUES (?, ?, ?, ?, ?, 1, ?, ?, 'google', ?, ?)""",
            (
                user_id,
                username,
                NO_PASSWORD,
                now,
                now,
                identity["sub"],
                identity.get("email"),
                now,
                int(username in self.settings.admin_username_set),
            ),
        )
        self._create_profile(user_id, identity.get("name") or username)
        self.conn.commit()
        user = self.auth.user_by_id(user_id)
        assert user is not None
        return self._session(user)

    def link_to_account(self, user_id: str, identity: dict[str, Any]) -> dict[str, Any]:
        """Attach a Google identity to the account that is already signed in."""
        current = self.auth.user_by_id(user_id)
        if current is None:
            raise GoogleAuthError("You are not signed in.")
        if current.get("google_sub"):
            if current["google_sub"] == identity["sub"]:
                raise GoogleAuthError("That Google account is already linked.")
            raise GoogleAuthError(
                "This account is already linked to a different Google account. "
                "Disconnect it first."
            )

        owner = self.user_by_google_sub(identity["sub"])
        if owner is not None:
            # The Google identity already belongs to another account. Merging
            # two progress histories is a decision for a human, not something to
            # do silently during an OAuth callback.
            raise GoogleAuthError(
                f"That Google account is already linked to the username '{owner['username']}'. "
                "Sign in with Google and use that account instead."
            )

        self.conn.execute(
            "UPDATE users SET google_sub = ?, google_email = ? WHERE id = ?",
            (identity["sub"], identity.get("email"), user_id),
        )
        self.conn.commit()
        return {"linked": True, "google_email": identity.get("email")}

    def unlink(self, user_id: str) -> dict[str, Any]:
        """Detach Google. Refuses if that would leave no way to sign in."""
        user = self.auth.user_by_id(user_id)
        if user is None:
            raise GoogleAuthError("You are not signed in.")
        if not user.get("google_sub"):
            raise GoogleAuthError("No Google account is linked.")
        if (user.get("password_hash") or "") == NO_PASSWORD:
            # Without this guard, unlinking would strand the account: no
            # password to fall back on and no Google identity to return with.
            raise GoogleAuthError(
                "Set a password first. This account was created with Google sign-in, so "
                "disconnecting it now would leave you no way to get back in."
            )
        self.conn.execute(
            "UPDATE users SET google_sub = NULL, google_email = NULL WHERE id = ?", (user_id,)
        )
        self.conn.commit()
        return {"linked": False}

    def set_password_for_oauth_account(self, user_id: str, new_password: str) -> None:
        """Give a Google-only account a password, so it can also be used directly."""
        from app.services.auth_service import hash_password, validate_password

        user = self.auth.user_by_id(user_id)
        if user is None:
            raise GoogleAuthError("You are not signed in.")
        self.conn.execute(
            "UPDATE users SET password_hash = ?, provider = 'both' WHERE id = ?",
            (hash_password(validate_password(new_password)), user_id),
        )
        self.conn.commit()

    # -- helpers -----------------------------------------------------------

    def _create_profile(self, user_id: str, display_name: str) -> str:
        profile_id = _new_id("p")
        now = _iso(_now())
        self.conn.execute(
            """INSERT INTO profiles
                 (id, display_name, avatar, is_active, xp_total, level, streak_day_count,
                  user_id, created_at, updated_at)
               VALUES (?, ?, ?, 1, 0, 1, 0, ?, ?, ?)""",
            (profile_id, str(display_name)[:24], None, user_id, now, now),
        )
        return profile_id

    def _session(self, user: dict[str, Any]) -> dict[str, Any]:
        now = _iso(_now())
        self.conn.execute(
            "UPDATE users SET last_login_at = ?, last_seen_at = ? WHERE id = ?",
            (now, now, user["id"]),
        )
        from app.services.auth_service import _issue_token, purge_expired_tokens

        purge_expired_tokens(self.conn)
        token = _issue_token(self.conn, user["id"])
        self.conn.commit()
        profile = self.auth.profile_for_user(user["id"])
        return {
            "token": token,
            "user": AuthService._public_user(user["id"], user["username"], user.get("created_at")),
            "profile_id": profile["id"] if profile else None,
        }
