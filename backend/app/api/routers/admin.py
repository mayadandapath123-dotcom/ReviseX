"""Admin endpoints. Every route requires users.is_admin, checked per request.

`GET /admin/users` and impersonation return data about other people, so the
guard is a dependency on each route rather than a check inside a handler: a new
route added later cannot forget it.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.api.deps import Conn, get_admin_service, require_user
from app.services.admin_service import AdminService

router = APIRouter(prefix="/admin", tags=["admin"])

Admin = Annotated[AdminService, Depends(get_admin_service)]


def require_admin(
    admin: Admin,
    user: Annotated[dict[str, Any], Depends(require_user)],
) -> dict[str, Any]:
    """Resolve the signed-in user and confirm the admin flag on every request.

    Checking per request rather than at login means removing someone's admin
    flag takes effect on their next call, not their next session.
    """
    if not admin.is_admin(user["id"]):
        raise HTTPException(status_code=403, detail="Admin access required.")
    return user


AdminUser = Annotated[dict[str, Any], Depends(require_admin)]


class ImpersonateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: str = Field(min_length=1, max_length=64)
    reason: str | None = Field(default=None, max_length=300)


@router.get("/overview")
def overview(admin: Admin, user: AdminUser) -> dict[str, Any]:
    return admin.overview()


@router.get("/users")
def list_users(
    admin: Admin,
    user: AdminUser,
    q: str = "",
    sort: str = "last_seen",
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    return admin.list_users(search=q, sort=sort, limit=limit, offset=offset)


@router.get("/users/{user_id}")
def user_detail(user_id: str, admin: Admin, user: AdminUser) -> dict[str, Any]:
    detail = admin.user_detail(user_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="That account does not exist.")
    return detail


@router.post("/users/{user_id}/impersonate")
def impersonate(
    user_id: str,
    payload: ImpersonateRequest | None,
    admin: Admin,
    user: AdminUser,
) -> dict[str, Any]:
    """Enter another account. Audited, short-lived, and never reveals a password."""
    if payload and payload.user_id != user_id:
        # The path is what is authorised; a body that disagrees is a bug or a probe.
        raise HTTPException(status_code=400, detail="user_id in the body must match the path.")
    try:
        result = admin.impersonate(user["id"], user_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return result


@router.get("/audit")
def audit(admin: Admin, user: AdminUser, limit: int = 100) -> dict[str, Any]:
    return {"entries": admin.audit_log(limit=limit)}
