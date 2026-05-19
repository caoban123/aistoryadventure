from __future__ import annotations

import json
from time import perf_counter

from fastapi import APIRouter, HTTPException, Depends

from app.domain.schemas import (
    SessionResponse,
    SessionRenameRequest,
    SessionSaveRequest,
    StartGameRequest,
    StoryResponse,
    TurnRequest,
    NovelStartRequest,
    NovelWorldResponse,
    NovelFoundationRequest,
    WorldCatalogItem,
)
from app.domain.models import SessionState
from app.domain.world_catalog import get_world_catalog_item, list_world_catalog
from app.services.story_service import StoryService
from app.auth.firebase_auth import get_current_user, require_admin_user
from app.services.admin_service import (
    AdminControlService,
    BannedUserError,
    DailyLimitExceededError,
    InsufficientPointsError,
    MaintenanceModeError,
)

router = APIRouter(prefix="/game", tags=["Story"])
service = StoryService()
admin_control = AdminControlService()


async def enforce_player_or_http(user: dict) -> None:
    try:
        await admin_control.enforce_player_access(user)
    except MaintenanceModeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except BannedUserError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


async def ensure_points_or_http(user: dict, action: str) -> None:
    try:
        await admin_control.ensure_points_available(user, action)
    except InsufficientPointsError as exc:
        raise HTTPException(status_code=402, detail=str(exc)) from exc


async def ensure_rate_limit_or_http(
    user: dict,
    action: str,
    operation: str,
    estimated_input_tokens: int,
) -> None:
    try:
        await admin_control.ensure_rate_limit_available(user, action)
    except DailyLimitExceededError as exc:
        await admin_control.log_ai_usage(
            user=user,
            action=action,
            operation=operation,
            status="blocked",
            error_kind="daily_limit",
            estimated_input_tokens=estimated_input_tokens,
        )
        raise HTTPException(status_code=429, detail=str(exc)) from exc


async def spend_points_or_http(
    user: dict,
    action: str,
    session_id: str | None = None,
):
    try:
        return await admin_control.spend_points_for_action(
            user,
            action,
            session_id=session_id,
        )
    except InsufficientPointsError as exc:
        raise HTTPException(status_code=402, detail=str(exc)) from exc


def estimate_token_count(value) -> int:
    text = str(value or "")
    if not text:
        return 0
    return max(1, (len(text) + 3) // 4)


def request_token_estimate(request) -> int:
    try:
        return estimate_token_count(request.model_dump_json())
    except Exception:
        return estimate_token_count(json.dumps(getattr(request, "__dict__", {}), ensure_ascii=False))


def response_token_estimate(response) -> int:
    parts = [
        getattr(response, "message", ""),
        getattr(response, "foundation_text", ""),
        getattr(response, "world_draft", ""),
        json.dumps(getattr(response, "choices", []), ensure_ascii=False),
        json.dumps(getattr(response, "questions", []), ensure_ascii=False),
    ]
    return estimate_token_count("\n".join(part for part in parts if part))


def usage_error_kind(exc: Exception) -> str:
    text = str(exc).lower()
    if "daily" in text and "limit" in text:
        return "daily_limit"
    if "high demand" in text or "overloaded" in text or "busy" in text:
        return "high_demand"
    if "quota" in text:
        return "quota"
    if "rate limit" in text:
        return "provider_rate_limit"
    if "not found" in text:
        return "not_found"
    if "permission" in text or "forbidden" in text:
        return "permission"
    if "validation" in text:
        return "validation"
    return "provider_or_flow_error"


async def log_ai_flow(
    *,
    user: dict,
    action: str,
    operation: str,
    status: str,
    started_at: float,
    estimated_input_tokens: int,
    estimated_output_tokens: int = 0,
    session_id: str | None = None,
    error: Exception | None = None,
    points_delta: int = 0,
) -> None:
    await admin_control.log_ai_usage(
        user=user,
        action=action,
        operation=operation,
        status=status,
        session_id=session_id,
        error_kind=usage_error_kind(error) if error else None,
        estimated_input_tokens=estimated_input_tokens,
        estimated_output_tokens=estimated_output_tokens,
        latency_ms=round((perf_counter() - started_at) * 1000),
        points_delta=points_delta,
    )


@router.post("/start", response_model=StoryResponse)
async def start_game(
    request: StartGameRequest,
    user=Depends(get_current_user),
):
    await enforce_player_or_http(user)
    estimated_input_tokens = request_token_estimate(request)
    await ensure_rate_limit_or_http(
        user,
        "start_adventure",
        "game.start",
        estimated_input_tokens,
    )
    await ensure_points_or_http(user, "start_adventure")
    started_at = perf_counter()

    try:
        result = await service.start_game(request, user_id=user["uid"])
        points_entry = await spend_points_or_http(user, "start_adventure", result.session_id)
        await log_ai_flow(
            user=user,
            action="start_adventure",
            operation="game.start",
            status="success",
            started_at=started_at,
            session_id=result.session_id,
            estimated_input_tokens=estimated_input_tokens,
            estimated_output_tokens=response_token_estimate(result),
            points_delta=points_entry.delta if points_entry else 0,
        )
        return result
    except HTTPException:
        raise
    except Exception as exc:
        await log_ai_flow(
            user=user,
            action="start_adventure",
            operation="game.start",
            status="error",
            started_at=started_at,
            estimated_input_tokens=estimated_input_tokens,
            error=exc,
        )
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/turn", response_model=StoryResponse)
async def continue_story(
    request: TurnRequest,
    user=Depends(get_current_user),
):
    await enforce_player_or_http(user)
    estimated_input_tokens = request_token_estimate(request)
    await ensure_rate_limit_or_http(
        user,
        "turn",
        "game.turn",
        estimated_input_tokens,
    )
    await ensure_points_or_http(user, "turn")
    started_at = perf_counter()

    try:
        result = await service.continue_story(request, user_id=user["uid"])
        points_entry = await spend_points_or_http(user, "turn", result.session_id)
        await log_ai_flow(
            user=user,
            action="turn",
            operation="game.turn",
            status="success",
            started_at=started_at,
            session_id=result.session_id,
            estimated_input_tokens=estimated_input_tokens,
            estimated_output_tokens=response_token_estimate(result),
            points_delta=points_entry.delta if points_entry else 0,
        )
        return result
    except HTTPException:
        raise
    except ValueError as exc:
        await log_ai_flow(
            user=user,
            action="turn",
            operation="game.turn",
            status="error",
            started_at=started_at,
            session_id=request.session_id,
            estimated_input_tokens=estimated_input_tokens,
            error=exc,
        )
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        await log_ai_flow(
            user=user,
            action="turn",
            operation="game.turn",
            status="error",
            started_at=started_at,
            session_id=request.session_id,
            estimated_input_tokens=estimated_input_tokens,
            error=exc,
        )
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:
        await log_ai_flow(
            user=user,
            action="turn",
            operation="game.turn",
            status="error",
            started_at=started_at,
            session_id=request.session_id,
            estimated_input_tokens=estimated_input_tokens,
            error=exc,
        )
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/sessions")
async def list_sessions(
    user=Depends(get_current_user),
):
    await enforce_player_or_http(user)

    try:
        return await service.list_sessions(user_id=user["uid"])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    user=Depends(get_current_user),
):
    await enforce_player_or_http(user)

    try:
        return await service.delete_session(session_id, user_id=user["uid"])
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/sessions/{session_id}/save", response_model=SessionState)
async def save_session(
    session_id: str,
    request: SessionSaveRequest | None = None,
    user=Depends(get_current_user),
):
    await enforce_player_or_http(user)

    try:
        return await service.save_session(
            session_id,
            user_id=user["uid"],
            title=request.title if request else None,
        )
    except ValueError as exc:
        status_code = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.patch("/sessions/{session_id}", response_model=SessionState)
async def rename_session(
    session_id: str,
    request: SessionRenameRequest,
    user=Depends(get_current_user),
):
    await enforce_player_or_http(user)

    try:
        return await service.rename_session(
            session_id,
            user_id=user["uid"],
            title=request.title,
        )
    except ValueError as exc:
        status_code = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/worlds", response_model=list[WorldCatalogItem])
async def list_worlds():
    return list_world_catalog()


@router.get("/worlds/{world_id}", response_model=WorldCatalogItem)
async def get_world(world_id: str):
    world = get_world_catalog_item(world_id)

    if not world:
        raise HTTPException(status_code=404, detail="World not found")

    return world


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    user=Depends(get_current_user),
):
    await enforce_player_or_http(user)

    try:
        session, messages = await service.get_session(session_id, user_id=user["uid"])
        return SessionResponse(session=session, messages=messages)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/{session_id}/admin/memory")
async def admin_memory(
    session_id: str,
    user=Depends(require_admin_user),
):
    try:
        await admin_control.ensure_user_state(user)
        return await service.debug_memory(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
@router.post("/novel/world", response_model=NovelWorldResponse)
async def start_novel_world(
    request: NovelStartRequest,
    user=Depends(get_current_user),
):
    await enforce_player_or_http(user)
    estimated_input_tokens = request_token_estimate(request)
    await ensure_rate_limit_or_http(
        user,
        "novel_world",
        "game.novel_world",
        estimated_input_tokens,
    )
    await ensure_points_or_http(user, "novel_world")
    started_at = perf_counter()

    try:
        result = await service.start_novel_world(
            request,
            user_id=user["uid"],
        )
        points_entry = await spend_points_or_http(user, "novel_world", result.session_id)
        await log_ai_flow(
            user=user,
            action="novel_world",
            operation="game.novel_world",
            status="success",
            started_at=started_at,
            session_id=result.session_id,
            estimated_input_tokens=estimated_input_tokens,
            estimated_output_tokens=response_token_estimate(result),
            points_delta=points_entry.delta if points_entry else 0,
        )
        return result
    except HTTPException:
        raise
    except Exception as exc:
        await log_ai_flow(
            user=user,
            action="novel_world",
            operation="game.novel_world",
            status="error",
            started_at=started_at,
            estimated_input_tokens=estimated_input_tokens,
            error=exc,
        )
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/novel/foundation", response_model=StoryResponse)
async def create_novel_foundation(
    request: NovelFoundationRequest,
    user=Depends(get_current_user),
):
    await enforce_player_or_http(user)
    estimated_input_tokens = request_token_estimate(request)
    await ensure_rate_limit_or_http(
        user,
        "novel_foundation",
        "game.novel_foundation",
        estimated_input_tokens,
    )
    await ensure_points_or_http(user, "novel_foundation")
    started_at = perf_counter()

    try:
        result = await service.create_novel_foundation(
            request,
            user_id=user["uid"],
        )
        points_entry = await spend_points_or_http(user, "novel_foundation", result.session_id)
        await log_ai_flow(
            user=user,
            action="novel_foundation",
            operation="game.novel_foundation",
            status="success",
            started_at=started_at,
            session_id=result.session_id,
            estimated_input_tokens=estimated_input_tokens,
            estimated_output_tokens=response_token_estimate(result),
            points_delta=points_entry.delta if points_entry else 0,
        )
        return result
    except HTTPException:
        raise
    except ValueError as exc:
        await log_ai_flow(
            user=user,
            action="novel_foundation",
            operation="game.novel_foundation",
            status="error",
            started_at=started_at,
            session_id=request.session_id,
            estimated_input_tokens=estimated_input_tokens,
            error=exc,
        )
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        await log_ai_flow(
            user=user,
            action="novel_foundation",
            operation="game.novel_foundation",
            status="error",
            started_at=started_at,
            session_id=request.session_id,
            estimated_input_tokens=estimated_input_tokens,
            error=exc,
        )
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:
        await log_ai_flow(
            user=user,
            action="novel_foundation",
            operation="game.novel_foundation",
            status="error",
            started_at=started_at,
            session_id=request.session_id,
            estimated_input_tokens=estimated_input_tokens,
            error=exc,
        )
        raise HTTPException(status_code=500, detail=str(exc)) from exc
