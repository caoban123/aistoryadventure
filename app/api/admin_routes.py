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


from app.memory.firebase_store import FirebaseStore
db_store = FirebaseStore()

@router.get("/submissions")
async def admin_list_submissions(user=Depends(require_admin_user)):
    await admin_service.ensure_user_state(user)
    items = await db_store.list_community_worlds(approved_only=False, limit=100)
    pending = [item for item in items if not item.is_approved]
    return pending


@router.post("/submissions/{item_id}/approve")
async def admin_approve_submission(item_id: str, user=Depends(require_admin_user)):
    await admin_service.ensure_user_state(user)
    item = await db_store.get_community_world(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài xuất bản.")
        
    item.is_approved = True
    await db_store.update_community_world(item)
    
    await admin_service.audit(
        actor=user,
        action="approve_community_world",
        target_uid=item.author_uid,
        session_id=item.session_id,
        metadata={"item_id": item.id, "title": item.title},
    )
    return {"message": "Đã phê duyệt thế giới thành công.", "item": item}


@router.post("/submissions/{item_id}/reject")
async def admin_reject_submission(item_id: str, user=Depends(require_admin_user)):
    await admin_service.ensure_user_state(user)
    item = await db_store.get_community_world(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài xuất bản.")
        
    await db_store.delete_community_world(item_id)
    
    await admin_service.audit(
        actor=user,
        action="reject_community_world",
        target_uid=item.author_uid,
        session_id=item.session_id,
        metadata={"item_id": item_id, "title": item.title},
    )
    return {"message": "Đã từ chối và xóa bài xuất bản thành công."}


from pydantic import BaseModel, Field
from typing import Literal
import uuid
from app.domain.models import Announcement

class AnnouncementCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    content: str = Field(..., min_length=1, max_length=1000)
    type: Literal["fixed", "temporary"] = "temporary"


@router.post("/announcements", response_model=Announcement)
async def admin_create_announcement(
    request: AnnouncementCreateRequest,
    user=Depends(require_admin_user),
):
    await admin_service.ensure_user_state(user)
    
    item = Announcement(
        id=str(uuid.uuid4()),
        title=request.title.strip(),
        content=request.content.strip(),
        type=request.type,
        created_by=user.get("email") or user["uid"],
    )
    await db_store.create_announcement(item)
    
    await admin_service.audit(
        actor=user,
        action="announcement.create",
        target_uid=item.id,
        metadata={"title": item.title, "type": item.type},
    )
    return item


@router.get("/announcements", response_model=list[Announcement])
async def admin_list_announcements(user=Depends(require_admin_user)):
    await admin_service.ensure_user_state(user)
    return await db_store.list_announcements(limit=100)


@router.delete("/announcements/{item_id}")
async def admin_delete_announcement(
    item_id: str,
    user=Depends(require_admin_user),
):
    await admin_service.ensure_user_state(user)
    await db_store.delete_announcement(item_id)
    
    await admin_service.audit(
        actor=user,
        action="announcement.delete",
        target_uid=item_id,
    )
    return {"message": "Đã xóa thông báo thành công."}


class SafetyTestRequest(BaseModel):
    text: str


@router.get("/safety/rules")
async def admin_get_safety_rules(user=Depends(require_admin_user)):
    await admin_service.ensure_user_state(user)
    from app.services.safety_service import SafetyFilterService
    sf = SafetyFilterService()
    return sf.categories


@router.post("/safety/test")
async def admin_test_safety(
    request: SafetyTestRequest,
    user=Depends(require_admin_user)
):
    await admin_service.ensure_user_state(user)
    from app.services.safety_service import SafetyFilterService
    sf = SafetyFilterService()
    try:
        sf.validate_input(request.text, "Văn bản kiểm thử")
        censored = sf.censor_output(request.text)
        is_censored = censored != request.text
        return {
            "safe": True,
            "censored_result": censored,
            "was_censored": is_censored,
            "message": "Văn bản hợp lệ và an toàn."
        }
    except ValueError as exc:
        censored = sf.censor_output(request.text)
        return {
            "safe": False,
            "error_detail": str(exc),
            "censored_result": censored,
            "was_censored": True,
            "message": "Văn bản vi phạm quy chuẩn nội dung."
        }



