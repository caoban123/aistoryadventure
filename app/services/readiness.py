from __future__ import annotations

import os
from pathlib import Path

from app.config import Settings
from app.domain.models import AppSettingsState, utc_now_iso
from app.domain.schemas import ReadinessCheckItem, ReadinessReport
from app.domain.world_catalog import list_world_catalog


PROVIDER_KEYS = {
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "groq": "GROQ_API_KEY",
}

SUPPORTED_PROVIDERS = {"mock", "openai", "gemini", "ollama", "groq"}


def build_readiness_report(
    *,
    settings: Settings,
    app_settings: AppSettingsState,
    firestore_active: bool,
) -> ReadinessReport:
    checks: list[ReadinessCheckItem] = []
    provider = settings.text_provider.lower().strip()
    production = settings.is_production
    storage_mode = _storage_mode(settings=settings, firestore_active=firestore_active)

    _add_provider_checks(checks, settings, provider, production)
    _add_cors_check(checks, settings, production)
    _add_storage_checks(checks, settings, storage_mode, firestore_active, production)
    _add_path_checks(checks, settings, storage_mode, production)
    _add_catalog_check(checks)
    _add_control_checks(checks, app_settings, production)

    if any(item.status == "error" for item in checks):
        overall_status = "error"
    elif any(item.status == "warning" for item in checks):
        overall_status = "warning"
    else:
        overall_status = "ok"

    return ReadinessReport(
        app_env=settings.app_env,
        storage_mode=storage_mode,
        overall_status=overall_status,
        production_ready=bool(production and overall_status == "ok"),
        generated_at=utc_now_iso(),
        checks=checks,
    )


def _add_provider_checks(
    checks: list[ReadinessCheckItem],
    settings: Settings,
    provider: str,
    production: bool,
) -> None:
    if provider not in SUPPORTED_PROVIDERS:
        checks.append(
            ReadinessCheckItem(
                check_id="provider.supported",
                label="AI provider",
                status="error",
                message=f"Unsupported provider '{settings.text_provider}'.",
                hint="Use mock, openai, gemini, ollama, or groq.",
            )
        )
        return

    if provider == "mock":
        checks.append(
            ReadinessCheckItem(
                check_id="provider.mock",
                label="AI provider",
                status="error" if production else "warning",
                message="Mock provider is active.",
                hint="Use a real provider before public launch.",
            )
        )
        return

    key_name = PROVIDER_KEYS.get(provider)
    key_value = getattr(settings, f"{provider}_api_key", None) if key_name else None
    if key_name and not key_value:
        checks.append(
            ReadinessCheckItem(
                check_id="provider.secret",
                label="AI provider secret",
                status="error",
                message=f"{key_name} is not configured.",
                hint="Set the provider key in the server environment only.",
            )
        )
        return

    if provider == "ollama" and not settings.ollama_base_url:
        checks.append(
            ReadinessCheckItem(
                check_id="provider.ollama",
                label="AI provider",
                status="error",
                message="Ollama provider is active but OLLAMA_BASE_URL is empty.",
                hint="Set OLLAMA_BASE_URL to the local/private Ollama service.",
            )
        )
        return

    checks.append(
        ReadinessCheckItem(
            check_id="provider.ready",
            label="AI provider",
            status="ok",
            message=f"{settings.text_provider} / {settings.text_model} is configured.",
        )
    )


def _add_cors_check(
    checks: list[ReadinessCheckItem],
    settings: Settings,
    production: bool,
) -> None:
    wildcard = settings.cors_origins.strip() == "*"
    if wildcard:
        checks.append(
            ReadinessCheckItem(
                check_id="cors.wildcard",
                label="CORS",
                status="error" if production else "warning",
                message="CORS allows every origin.",
                hint="Set CORS_ORIGINS to the player and admin domains before production.",
            )
        )
        return

    origins = settings.cors_origin_list
    status = "ok" if len(origins) >= 1 else "error"
    checks.append(
        ReadinessCheckItem(
            check_id="cors.origins",
            label="CORS",
            status=status,
            message=f"{len(origins)} allowed origin(s) configured.",
            hint="Include both player and admin origins.",
        )
    )


def _add_storage_checks(
    checks: list[ReadinessCheckItem],
    settings: Settings,
    storage_mode: str,
    firestore_active: bool,
    production: bool,
) -> None:
    admin_credentials_configured = bool(
        settings.firebase_credentials_path or settings.firebase_service_account_json
    )

    if firestore_active:
        checks.append(
            ReadinessCheckItem(
                check_id="storage.firestore",
                label="Storage",
                status="ok",
                message="Firestore is active.",
            )
        )
    elif admin_credentials_configured:
        checks.append(
            ReadinessCheckItem(
                check_id="storage.firestore_init",
                label="Storage",
                status="error",
                message="Firebase credentials are configured, but Firestore is not active.",
                hint="Check the server Firebase Admin SDK credentials and project access.",
            )
        )
    elif production:
        checks.append(
            ReadinessCheckItem(
                check_id="storage.production_firestore",
                label="Storage",
                status="error",
                message="Production is not connected to Firestore.",
                hint="Set FIREBASE_CREDENTIALS_PATH or FIREBASE_SERVICE_ACCOUNT_JSON on the server.",
            )
        )
    else:
        checks.append(
            ReadinessCheckItem(
                check_id="storage.local_fallback",
                label="Storage",
                status="warning",
                message=f"Using {storage_mode}.",
                hint="This is acceptable for local testing, not public launch.",
            )
        )

    if production and settings.use_local_store_if_firebase_missing:
        checks.append(
            ReadinessCheckItem(
                check_id="storage.local_fallback_enabled",
                label="Storage fallback",
                status="error",
                message="Local fallback is enabled in production.",
                hint="Set USE_LOCAL_STORE_IF_FIREBASE_MISSING=false.",
            )
        )


def _check_qdrant_connection(host: str, port: int) -> tuple[str, str]:
    import socket
    try:
        with socket.create_connection((host, port), timeout=1.5):
            return "ok", f"Successfully connected to Qdrant at {host}:{port}."
    except Exception as exc:
        return "error", f"Could not connect to Qdrant at {host}:{port}: {exc}"


def _add_path_checks(
    checks: list[ReadinessCheckItem],
    settings: Settings,
    storage_mode: str,
    production: bool,
) -> None:
    if settings.vector_db.lower().strip() == "qdrant":
        qdrant_status, qdrant_message = _check_qdrant_connection(
            settings.qdrant_host, settings.qdrant_port
        )
        checks.append(
            ReadinessCheckItem(
                check_id="paths.qdrant",
                label="Qdrant DB",
                status=qdrant_status,
                message=qdrant_message,
                hint="Verify that the Qdrant container/service is running and accessible.",
            )
        )
    else:
        chroma_status, chroma_message = _path_status(Path(settings.chroma_persist_dir))
        checks.append(
            ReadinessCheckItem(
                check_id="paths.chroma",
                label="ChromaDB",
                status=chroma_status,
                message=chroma_message,
                hint="Use a persistent server directory and include it in backups.",
            )
        )

        if production and not Path(settings.chroma_persist_dir).is_absolute():
            checks.append(
                ReadinessCheckItem(
                    check_id="paths.chroma_absolute",
                    label="ChromaDB path",
                    status="warning",
                    message="ChromaDB path is relative.",
                    hint="Use an absolute persistent path on the VPS, such as /var/lib/ai-story/chroma_db.",
                )
            )

    if storage_mode != "firebase":
        data_status, data_message = _path_status(Path(settings.local_data_dir))
        checks.append(
            ReadinessCheckItem(
                check_id="paths.local_data",
                label="Local data",
                status=data_status,
                message=data_message,
                hint="Local data must be backed up if Firebase is not active.",
            )
        )

        if production and not Path(settings.local_data_dir).is_absolute():
            checks.append(
                ReadinessCheckItem(
                    check_id="paths.local_data_absolute",
                    label="Local data path",
                    status="warning",
                    message="Local data path is relative.",
                    hint="Use an absolute persistent path on the VPS.",
                )
            )


def _add_catalog_check(checks: list[ReadinessCheckItem]) -> None:
    count = len(list_world_catalog())
    checks.append(
        ReadinessCheckItem(
            check_id="catalog.count",
            label="World catalog",
            status="ok" if count > 0 else "error",
            message=f"{count} curated world(s) available.",
            hint="Discover needs at least one curated world.",
        )
    )


def _add_control_checks(
    checks: list[ReadinessCheckItem],
    app_settings: AppSettingsState,
    production: bool,
) -> None:
    checks.append(
        ReadinessCheckItem(
            check_id="controls.rate_limit",
            label="Rate limit",
            status="ok" if app_settings.rate_limit_enabled else ("warning" if production else "ok"),
            message=(
                f"Enabled: {app_settings.daily_turn_limit} turns/day, "
                f"{app_settings.daily_create_limit} creates/day."
                if app_settings.rate_limit_enabled
                else "Daily rate limit is disabled."
            ),
            hint="Keep rate limits enabled before public beta.",
        )
    )

    checks.append(
        ReadinessCheckItem(
            check_id="controls.usage_retention",
            label="Usage retention",
            status="ok",
            message=f"AI usage logs retain {app_settings.usage_log_retention_days} day(s).",
        )
    )

    checks.append(
        ReadinessCheckItem(
            check_id="controls.maintenance",
            label="Maintenance mode",
            status="warning" if app_settings.maintenance_enabled else "ok",
            message="Maintenance is enabled." if app_settings.maintenance_enabled else "Maintenance is off.",
        )
    )


def _path_status(path: Path) -> tuple[str, str]:
    target = path if path.exists() else path.parent
    if path.exists() and not path.is_dir():
        return "error", "Configured path exists but is not a directory."
    if not target.exists():
        return "warning", "Directory does not exist yet."
    if not os.access(target, os.W_OK):
        return "error", "Directory is not writable by the current process."
    return "ok", "Directory is present or can be created."


def _storage_mode(*, settings: Settings, firestore_active: bool) -> str:
    if firestore_active:
        return "firebase"
    if settings.use_local_store_if_firebase_missing:
        return "local-fallback"
    return "firebase-required"
