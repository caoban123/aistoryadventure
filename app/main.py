from __future__ import annotations

import logging

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.admin_routes import router as admin_router
from app.api.story_routes import router as story_router
from app.api.rpg_routes import router as rpg_router
from app.auth.firebase_auth import get_current_user
from app.config import get_settings
from app.domain.models import AppSettingsState
from app.domain.schemas import ReadinessCheckItem
from app.domain.world_catalog import list_world_catalog
from app.services.admin_service import AdminControlService
from app.services.readiness import build_readiness_report

settings = get_settings()
admin_control = AdminControlService()
logger = logging.getLogger("ai_story.startup")

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(story_router)
app.include_router(rpg_router)
app.include_router(admin_router)


@app.on_event("startup")
async def startup_readiness_check() -> None:
    app_settings, settings_error = await safe_app_settings()
    report = build_readiness_report(
        settings=settings,
        app_settings=app_settings,
        firestore_active=bool(admin_control.store.db),
    )
    if settings_error:
        append_settings_error(report, settings_error)

    for item in report.checks:
        if item.status == "error":
            logger.error("Production readiness error: %s - %s", item.label, item.message)
        elif item.status == "warning":
            logger.warning("Production readiness warning: %s - %s", item.label, item.message)

    if settings.strict_startup_checks and report.overall_status == "error":
        failed = ", ".join(item.label for item in report.checks if item.status == "error")
        raise RuntimeError(f"Startup readiness checks failed: {failed}")


async def safe_app_settings() -> tuple[AppSettingsState, str | None]:
    if admin_control.store.db:
        return AppSettingsState(), "firestore_not_checked"

    try:
        return await admin_control.store.get_app_settings(), None
    except Exception as exc:
        logger.warning("Could not load app settings for status/readiness: %s", exc)
        return AppSettingsState(), exc.__class__.__name__


def append_settings_error(report, error_kind: str) -> None:
    is_nonblocking_skip = error_kind == "firestore_not_checked"
    report.checks.append(
        ReadinessCheckItem(
            check_id="settings.load",
            label="App settings",
            status="warning" if is_nonblocking_skip else "error",
            message=(
                "Public readiness skipped live Firestore app settings to stay non-blocking."
                if is_nonblocking_skip
                else "Could not load app settings from storage."
            ),
            hint=(
                "Use the admin dashboard for live maintenance, points, and rate-limit settings."
                if is_nonblocking_skip
                else f"Check backend storage connectivity. Error kind: {error_kind}."
            ),
        )
    )
    if is_nonblocking_skip and report.overall_status == "ok":
        report.overall_status = "warning"
        report.production_ready = False
    if not is_nonblocking_skip:
        report.overall_status = "error"
        report.production_ready = False


@app.get("/")
def root():
    return {"message": "AI Story Adventure API is running"}


@app.get("/status")
async def status():
    app_settings, settings_error = await safe_app_settings()
    readiness = build_readiness_report(
        settings=settings,
        app_settings=app_settings,
        firestore_active=bool(admin_control.store.db),
    )
    if settings_error:
        append_settings_error(readiness, settings_error)

    return {
        "app_name": settings.app_name,
        "app_env": settings.app_env,
        "text_provider": settings.text_provider,
        "text_model": settings.text_model,
        "embedding_provider": settings.embedding_provider,
        "storage_mode": readiness.storage_mode,
        "catalog_count": len(list_world_catalog()),
        "maintenance": {
            "enabled": app_settings.maintenance_enabled,
            "message": app_settings.maintenance_message,
        },
        "points": {
            "enabled": app_settings.points_enabled,
        },
        "rate_limit": {
            "enabled": app_settings.rate_limit_enabled,
            "daily_turn_limit": app_settings.daily_turn_limit,
            "daily_create_limit": app_settings.daily_create_limit,
        },
        "readiness": readiness.model_dump(),
    }


@app.get("/account/status")
async def account_status(user=Depends(get_current_user)):
    app_settings = await admin_control.store.get_app_settings()
    state = await admin_control.ensure_user_state(user)
    is_admin = bool(user.get("admin"))
    maintenance_active = bool(app_settings.maintenance_enabled and not is_admin)
    banned_active = bool(state.is_banned and not is_admin)

    return {
        "allowed": not maintenance_active and not banned_active,
        "is_admin": is_admin,
        "maintenance": {
            "enabled": maintenance_active,
            "message": app_settings.maintenance_message,
        },
        "ban": {
            "enabled": banned_active,
            "message": state.ban_reason or "This account is banned.",
        },
    }
