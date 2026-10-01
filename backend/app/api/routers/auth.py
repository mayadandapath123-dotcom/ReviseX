"""Authentication endpoints: signup, login, logout, me.

Tokens travel in `Authorization: Bearer <token>`. Nothing here ever returns a
password hash, and every failure message is deliberately vague enough that it
cannot be used to enumerate which usernames exist.
"""

from __future__ import annotations

import json

from typing import Annotated, Any

from urllib.parse import quote

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, ConfigDict, Field

from app.api.deps import Conn, get_auth_service, get_google_auth_service
from app.config.settings import get_settings
from app.services.auth_service import AuthError, AuthService
from app.services.google_auth_service import (
    GoogleAuthError,
    GoogleAuthService,
    GoogleNotConfigured,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class SignupRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=3, max_length=24)
    password: str = Field(min_length=6, max_length=200)
    display_name: str | None = Field(default=None, max_length=24)
    # Adopts an existing local (account-free) profile so its XP, streaks,
    # mistakes and SRS history survive the upgrade to a real account.
    claim_profile_id: str | None = Field(default=None, max_length=64)


class SetPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    new_password: str = Field(min_length=6, max_length=200)


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=200)


class ChangePasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_password: str = Field(min_length=1, max_length=200)
    new_password: str = Field(min_length=6, max_length=200)


def _failure(exc: AuthError) -> HTTPException:
    # 400 for validation (the caller can fix it), 401 for bad credentials.
    message = str(exc)
    status = 401 if "Incorrect username or password" in message or "already taken" not in message else 400
    if "already taken" in message or "must be" in message:
        status = 400
    return HTTPException(status_code=status, detail=message)


@router.post("/signup", status_code=201)
def signup(
    payload: SignupRequest,
    auth: Annotated[AuthService, Depends(get_auth_service)],
) -> dict[str, Any]:
    try:
        result = auth.signup(
            payload.username,
            payload.password,
            payload.display_name,
            payload.claim_profile_id,
        )
    except AuthError as exc:
        raise _failure(exc) from exc
    result["claimed_profile"] = bool(payload.claim_profile_id) and result.get("profile_id") == payload.claim_profile_id
    return result


@router.post("/login")
def login(
    payload: LoginRequest,
    auth: Annotated[AuthService, Depends(get_auth_service)],
) -> dict[str, Any]:
    try:
        result = auth.login(payload.username, payload.password)
    except AuthError as exc:
        raise _failure(exc) from exc
    return result


@router.post("/logout", status_code=204)
def logout(
    auth: Annotated[AuthService, Depends(get_auth_service)],
    authorization: Annotated[str | None, Header()] = None,
) -> Response:
    token = (authorization or "").removeprefix("Bearer ").strip() or None
    auth.logout(token)
    return Response(status_code=204)


@router.get("/me")
def me(
    conn: Conn,
    auth: Annotated[AuthService, Depends(get_auth_service)],
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    token = (authorization or "").removeprefix("Bearer ").strip() or None
    user = auth.user_from_token(token)
    if user is None:
        raise HTTPException(status_code=401, detail="Not signed in, or the session expired.")
    profile = auth.profile_for_user(user["id"])
    return {
        "user": AuthService._public_user(user["id"], user["username"], user.get("created_at")),
        "profile": profile,
    }


@router.post("/change-password", status_code=204)
def change_password(
    payload: ChangePasswordRequest,
    auth: Annotated[AuthService, Depends(get_auth_service)],
    authorization: Annotated[str | None, Header()] = None,
) -> Response:
    token = (authorization or "").removeprefix("Bearer ").strip() or None
    user = auth.user_from_token(token)
    if user is None:
        raise HTTPException(status_code=401, detail="Not signed in, or the session expired.")
    try:
        auth.change_password(user["id"], payload.current_password, payload.new_password)
    except AuthError as exc:
        raise _failure(exc) from exc
    # Every token was invalidated, including this one, so the client must sign in again.
    return Response(status_code=204)

# ─────────────────────────── Google sign-in ───────────────────────────
#
# The browser cannot send an Authorization header on a plain navigation, so the
# SPA asks for the Google URL first (authenticated, for link mode) and then
# navigates to it. Google returns to /auth/google/callback, which finishes the
# flow server side and redirects back to the app with the result in the URL
# FRAGMENT. A fragment is never sent to a server, so the session token cannot
# end up in Render's access logs the way a query parameter would.


def _frontend_origin(request: Request) -> str:
    settings = get_settings()
    if settings.public_base_url:
        return settings.public_base_url.rstrip("/")
    return str(request.base_url).rstrip("/")


def _redirect_with_result(request: Request, payload: dict[str, Any]) -> RedirectResponse:
    return RedirectResponse(f"{_frontend_origin(request)}/#auth={quote(json.dumps(payload))}", status_code=303)


@router.get("/google/status")
def google_status(google: Annotated[GoogleAuthService, Depends(get_google_auth_service)]) -> dict[str, Any]:
    return google.status()


@router.get("/google/start")
def google_start(
    request: Request,
    google: Annotated[GoogleAuthService, Depends(get_google_auth_service)],
    auth: Annotated[AuthService, Depends(get_auth_service)],
    mode: str = "signin",
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    """Return the Google consent URL. mode=link requires a signed-in account."""
    if mode not in ("signin", "link"):
        raise HTTPException(status_code=400, detail="mode must be 'signin' or 'link'.")
    user_id = None
    if mode == "link":
        token = (authorization or "").removeprefix("Bearer ").strip() or None
        user = auth.user_from_token(token)
        if user is None:
            raise HTTPException(status_code=401, detail="Sign in before linking a Google account.")
        user_id = user["id"]
    try:
        url = google.build_auth_url(mode, user_id)
    except GoogleNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"url": url, "mode": mode}


@router.get("/google/callback")
def google_callback(
    request: Request,
    google: Annotated[GoogleAuthService, Depends(get_google_auth_service)],
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> RedirectResponse:
    """Google redirects here. Always ends as a redirect back to the app."""
    if error:
        # The user pressed Cancel, or Google refused the client.
        message = "Google sign-in was cancelled." if error in ("access_denied", "user_cancelled") else f"Google sign-in failed ({error})."
        return _redirect_with_result(request, {"ok": False, "error": message})
    if not code or not state:
        return _redirect_with_result(request, {"ok": False, "error": "Google returned an incomplete response."})

    try:
        record = google.consume_state(state)
        identity = google.exchange_code(code)
        if record["kind"] == "link":
            if not record["user_id"]:
                raise GoogleAuthError("This link attempt is no longer valid.")
            google.link_to_account(record["user_id"], identity)
            return _redirect_with_result(request, {
                "ok": True, "mode": "link", "google_email": identity.get("email"),
            })
        result = google.sign_in_or_register(identity)
        return _redirect_with_result(request, {
            "ok": True, "mode": "signin", "token": result["token"],
            "user": result["user"], "profile_id": result["profile_id"],
        })
    except (GoogleAuthError, GoogleNotConfigured) as exc:
        return _redirect_with_result(request, {"ok": False, "error": str(exc)})
    except Exception:
        # Never leak a stack trace through a redirect, and never lose the user:
        # they land back on the sign-in screen with a generic message.
        return _redirect_with_result(request, {
            "ok": False, "error": "Google sign-in failed unexpectedly. Please try again.",
        })


@router.post("/google/unlink")
def google_unlink(
    google: Annotated[GoogleAuthService, Depends(get_google_auth_service)],
    auth: Annotated[AuthService, Depends(get_auth_service)],
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    token = (authorization or "").removeprefix("Bearer ").strip() or None
    user = auth.user_from_token(token)
    if user is None:
        raise HTTPException(status_code=401, detail="Sign in to manage your Google connection.")
    try:
        return google.unlink(user["id"])
    except GoogleAuthError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/set-password", status_code=204)
def set_password(
    payload: SetPasswordRequest,
    google: Annotated[GoogleAuthService, Depends(get_google_auth_service)],
    auth: Annotated[AuthService, Depends(get_auth_service)],
    authorization: Annotated[str | None, Header()] = None,
) -> Response:
    """Set a first password on a Google-created account.

    Separate from change-password because there is no current password to prove.
    This is also the prerequisite for unlinking Google, and the reason unlinking
    can refuse: without it, detaching would leave no way back in.
    """
    token = (authorization or "").removeprefix("Bearer ").strip() or None
    user = auth.user_from_token(token)
    if user is None:
        raise HTTPException(status_code=401, detail="Sign in to set a password.")
    try:
        google.set_password_for_oauth_account(user["id"], payload.new_password)
    except (GoogleAuthError, AuthError) as exc:
        raise _failure(exc) from exc
    # Sessions were not invalidated: adding a password is additive, unlike
    # changing one, so there is no reason to sign the student out everywhere.
    return Response(status_code=204)


@router.get("/account")
def account_details(
    auth: Annotated[AuthService, Depends(get_auth_service)],
    conn: Conn,
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    """What the account settings screen needs: how you can sign in."""
    token = (authorization or "").removeprefix("Bearer ").strip() or None
    user = auth.user_from_token(token)
    if user is None:
        raise HTTPException(status_code=401, detail="Not signed in, or the session expired.")
    from app.services.google_auth_service import NO_PASSWORD

    return {
        "username": user["username"],
        "has_password": (user.get("password_hash") or "") != NO_PASSWORD,
        "google_linked": bool(user.get("google_sub")),
        "google_email": user.get("google_email"),
        "provider": user.get("provider") or "password",
        "is_admin": bool(int(user.get("is_admin") or 0)),
        "created_at": user.get("created_at"),
        "last_login_at": user.get("last_login_at"),
    }
