from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth.firebase_auth import require_admin_user
from app.domain.models import AdminUserState, AppSettingsState
from app.domain.schemas import (
    AdminAuditResponse,
    AdminBanRequest,
    AdminErrorsResponse,
    AdminLedgerResponse,
    AdminOverviewResponse,
    AdminPointsAdjustRequest,
    AdminSessionsResponse,
    AdminSettingsUpdateRequest,
    AdminUsageResponse,
    AdminUsageUsersResponse,
    AdminUsersResponse,
)
from app.services.admin_service import AdminControlService

router = APIRouter(prefix="/admin", tags=["Admin"])
admin_service = AdminControlService()


@router.get("/me")
async def admin_me(user=Depends(require_admin_user)):
    return {
        "uid": user["uid"],
        "email": user.get("email"),
        "name": user.get("name"),
        "provider": user.get("provider"),
        "email_verified": user.get("email_verified", False),
        "admin": True,
    }


@router.get("/overview", response_model=AdminOverviewResponse)
async def admin_overview(user=Depends(require_admin_user)):
    await admin_service.ensure_user_state(user)
    return await admin_service.get_overview()


@router.get("/sessions", response_model=AdminSessionsResponse)
async def admin_sessions(
    limit: int = Query(default=30, ge=1, le=100),
    before: str | None = Query(default=None),
    mode: str | None = Query(default=None, pattern="^(adventure|novel)$"),
    saved: bool | None = Query(default=None),
    user=Depends(require_admin_user),
):
    await admin_service.ensure_user_state(user)
    return await admin_service.list_sessions(
        limit=limit,
        before=before,
        mode=mode,
        saved=saved,
    )


@router.get("/users", response_model=AdminUsersResponse)
async def admin_users(
    limit: int = Query(default=100, ge=1, le=200),
    user=Depends(require_admin_user),
):
    await admin_service.ensure_user_state(user)
    return await admin_service.list_users(limit=limit)


@router.get("/usage", response_model=AdminUsageResponse)
async def admin_usage(
    uid: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
    user=Depends(require_admin_user),
):
    await admin_service.ensure_user_state(user)
    return await admin_service.get_usage(uid=uid, limit=limit)


@router.get("/usage/users", response_model=AdminUsageUsersResponse)
async def admin_usage_users(
    limit: int = Query(default=100, ge=1, le=200),
    user=Depends(require_admin_user),
):
    await admin_service.ensure_user_state(user)
    return await admin_service.list_usage_users(limit=limit)


@router.get("/errors", response_model=AdminErrorsResponse)
async def admin_errors(
    limit: int = Query(default=100, ge=1, le=200),
    user=Depends(require_admin_user),
):
    await admin_service.ensure_user_state(user)
    return await admin_service.list_ai_errors(limit=limit)


@router.post("/users/{uid}/points", response_model=AdminUserState)
async def admin_adjust_points(
    uid: str,
    request: AdminPointsAdjustRequest,
    user=Depends(require_admin_user),
):
    try:
        return await admin_service.adjust_points(
            target_uid=uid,
            delta=request.delta,
            reason=request.reason,
            actor=user,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/users/{uid}/ban", response_model=AdminUserState)
async def admin_ban_user(
    uid: str,
    request: AdminBanRequest,
    user=Depends(require_admin_user),
):
    return await admin_service.ban_user(
        target_uid=uid,
        reason=request.reason,
        actor=user,
    )


@router.post("/users/{uid}/unban", response_model=AdminUserState)
async def admin_unban_user(
    uid: str,
    user=Depends(require_admin_user),
):
    return await admin_service.unban_user(target_uid=uid, actor=user)


@router.get("/settings", response_model=AppSettingsState)
async def admin_get_settings(user=Depends(require_admin_user)):
    await admin_service.ensure_user_state(user)
    return await admin_service.store.get_app_settings()


@router.patch("/settings", response_model=AppSettingsState)
async def admin_update_settings(
    request: AdminSettingsUpdateRequest,
    user=Depends(require_admin_user),
):
    return await admin_service.update_settings(
        actor=user,
        **request.model_dump(),
    )


@router.get("/points/ledger", response_model=AdminLedgerResponse)
async def admin_points_ledger(
    uid: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
    user=Depends(require_admin_user),
):
    await admin_service.ensure_user_state(user)
    items = await admin_service.list_ledger(uid=uid, limit=limit)
    return AdminLedgerResponse(items=items, count=len(items))


@router.get("/audit", response_model=AdminAuditResponse)
async def admin_audit(
    limit: int = Query(default=100, ge=1, le=200),
    user=Depends(require_admin_user),
):
    await admin_service.ensure_user_state(user)
    items = await admin_service.list_audit_logs(limit=limit)
    return AdminAuditResponse(items=items, count=len(items))
