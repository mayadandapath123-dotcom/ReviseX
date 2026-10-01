"""Friend endpoints. All require a signed-in account."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from app.api.deps import Conn, get_friend_service, require_user
from app.services.friend_service import FriendError, FriendService

router = APIRouter(prefix="/friends", tags=["friends"])

User = Annotated[dict[str, Any], Depends(require_user)]
Friends = Annotated[FriendService, Depends(get_friend_service)]


class SendRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=1, max_length=64)


class RequestAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: str = Field(min_length=1, max_length=64)


class RemoveFriend(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: str = Field(min_length=1, max_length=64)


def _guard(fn, *args) -> Any:
    try:
        return fn(*args)
    except FriendError as exc:
        # 409 for a conflict with existing state (already friends, duplicate
        # request), 404 when the named thing does not exist, 403 when the caller
        # is not the person allowed to act. Everything else is a bad request.
        message = str(exc)
        if "does not exist" in message or "was found" in message:
            status = 404
        elif "Only the person" in message or "You can only" in message:
            status = 403
        elif "already" in message:
            status = 409
        else:
            status = 400
        raise HTTPException(status_code=status, detail=message) from exc


@router.get("")
def list_friends(user: User, friends: Friends) -> dict[str, Any]:
    return {"friends": friends.friends(user["id"]), **friends.summary(user["id"])}


@router.get("/requests")
def list_requests(user: User, friends: Friends) -> dict[str, Any]:
    return {
        "incoming": friends.incoming_requests(user["id"]),
        "outgoing": friends.outgoing_requests(user["id"]),
    }


@router.get("/search")
def search_users(
    user: User,
    friends: Friends,
    q: str = "",
    limit: int = 20,
) -> dict[str, Any]:
    """Search accounts by name. Capped at 20 regardless of what is asked for."""
    return {"results": friends.search(user["id"], q, limit=min(max(limit, 1), 20))}


@router.get("/leaderboard")
def friends_leaderboard(user: User, friends: Friends) -> dict[str, Any]:
    return {"entries": friends.leaderboard(user["id"])}


@router.post("/request")
def send_request(payload: SendRequest, user: User, friends: Friends) -> Any:
    """Send an invitation, or accept one that is already waiting.

    Replying to someone who already invited you is an acceptance, not a new
    invitation - otherwise both sides sit on a pending row forever. The status
    code follows what actually happened: 201 when a request was created, 200
    when an existing one was accepted.
    """
    result = _guard(friends.send_request, user["id"], payload.username)
    created = result.get("status") == "pending"
    return JSONResponse(status_code=201 if created else 200, content=result)


@router.post("/request/accept")
def accept_request(payload: RequestAction, user: User, friends: Friends) -> dict[str, Any]:
    return _guard(friends.accept_request, user["id"], payload.request_id)


@router.post("/request/decline")
def decline_request(payload: RequestAction, user: User, friends: Friends) -> dict[str, Any]:
    return _guard(friends.decline_request, user["id"], payload.request_id)


@router.post("/request/cancel")
def cancel_request(payload: RequestAction, user: User, friends: Friends) -> dict[str, Any]:
    return _guard(friends.cancel_request, user["id"], payload.request_id)


@router.post("/remove")
def remove_friend(payload: RemoveFriend, user: User, friends: Friends) -> dict[str, Any]:
    return _guard(friends.remove_friend, user["id"], payload.user_id)
