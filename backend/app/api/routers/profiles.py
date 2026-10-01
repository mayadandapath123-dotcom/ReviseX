"""Profile endpoints — local only, no accounts."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Response

from app.api.deps import Conn, get_profile_service
from app.api.schemas.requests import CreateProfileRequest, UpdateProfileRequest
from app.services.profile_service import ProfileError, ProfileService

router = APIRouter(prefix="/profiles", tags=["profiles"])

Profiles = Annotated[ProfileService, Depends(get_profile_service)]


@router.get("")
def list_profiles(profiles: Profiles) -> dict[str, Any]:
    return {"profiles": profiles.list()}


@router.post("", status_code=201)
def create_profile(payload: CreateProfileRequest, profiles: Profiles) -> dict[str, Any]:
    try:
        return {"profile": profiles.create(payload.display_name, payload.avatar)}
    except ProfileError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{profile_id}")
def get_profile(profile_id: str, profiles: Profiles) -> dict[str, Any]:
    profile = profiles.get(profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"profile": profile}


@router.patch("/{profile_id}")
def update_profile(profile_id: str, payload: UpdateProfileRequest, profiles: Profiles) -> dict[str, Any]:
    try:
        updated = profiles.update(
            profile_id,
            display_name=payload.display_name,
            avatar=payload.avatar,
            settings=payload.settings,
            online_enabled=payload.online_enabled,
            public_handle=payload.public_handle,
        )
    except ProfileError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if updated is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"profile": updated}


@router.post("/{profile_id}/activate")
def activate_profile(profile_id: str, profiles: Profiles) -> dict[str, Any]:
    profile = profiles.set_active(profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"profile": profile}


@router.delete("/{profile_id}", status_code=204)
def delete_profile(profile_id: str, profiles: Profiles) -> Response:
    if not profiles.delete(profile_id):
        raise HTTPException(status_code=404, detail="Profile not found")
    return Response(status_code=204)


@router.get("/{profile_id}/active-check")
def active_profile(conn: Conn, profiles: Profiles) -> dict[str, Any]:
    active = profiles.active()
    return {"profile": active}
