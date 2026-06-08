from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.config import get_settings
from app.domain.models import (
    AIUsageLogEntry,
    AdminUserState,
    AppSettingsState,
    AuditLogEntry,
    PointsLedgerEntry,
    SessionState,
    utc_now_iso,
)
from app.domain.schemas import (
    AdminErrorsResponse,
    AdminOverviewResponse,
    AdminSessionListItem,
    AdminSessionsResponse,
    AdminUsageResponse,
    AdminUsageTotals,
    AdminUsageUserItem,
    AdminUsageUsersResponse,
    AdminUserListItem,
    AdminUsersResponse,
)
from app.domain.world_catalog import list_world_catalog
from app.memory.firebase_store import FirebaseStore
from app.services.readiness import build_readiness_report


AI_ACTIONS = {
    "start_adventure": "cost_start_adventure",
    "novel_world": "cost_novel_world",
    "novel_foundation": "cost_novel_foundation",
    "turn": "cost_turn",
}

CREATE_ACTIONS = {"start_adventure", "novel_world", "novel_foundation"}


class MaintenanceModeError(PermissionError):
    pass


class BannedUserError(PermissionError):
    pass


class InsufficientPointsError(ValueError):
    pass


class DailyLimitExceededError(ValueError):
    pass


class AdminControlService:
    def __init__(self) -> None:
        self.store = FirebaseStore()
        self.settings = get_settings()

    async def ensure_user_state(self, user: dict) -> AdminUserState:
        uid = user["uid"]
        now = utc_now_iso()
        state = await self.store.get_admin_user_state(uid)

        if state is None:
            state = AdminUserState(
                uid=uid,
                email=user.get("email"),
                name=user.get("name"),
                provider=user.get("provider"),
                created_at=now,
                updated_at=now,
                last_seen_at=now,
            )
        else:
            state.email = user.get("email") or state.email
            state.name = user.get("name") or state.name
            state.provider = user.get("provider") or state.provider
            state.last_seen_at = now
            state.updated_at = now

        await self.store.upsert_admin_user_state(state)
        return state

    async def enforce_player_access(self, user: dict) -> AdminUserState:
        state = await self.ensure_user_state(user)

        if user.get("admin"):
            return state

        app_settings = await self.store.get_app_settings()

        if app_settings.maintenance_enabled:
            raise MaintenanceModeError(app_settings.maintenance_message)

        if state.is_banned:
            message = state.ban_reason or "This account is banned."
            raise BannedUserError(message)

        return state

    async def ensure_points_available(self, user: dict, action: str) -> None:
        if user.get("admin"):
            return

        app_settings = await self.store.get_app_settings()
        if not app_settings.points_enabled:
            return

        cost = self._cost_for_action(app_settings, action)
        if cost <= 0:
            return

        state = await self.ensure_user_state(user)
        if state.points_balance < cost:
            raise InsufficientPointsError(
                f"Not enough points. This action costs {cost} points, "
                f"but your balance is {state.points_balance}."
            )

    async def ensure_rate_limit_available(self, user: dict, action: str) -> None:
        if user.get("admin"):
            return

        app_settings = await self.store.get_app_settings()
        if not app_settings.rate_limit_enabled:
            return

        await self.cleanup_old_usage_logs(app_settings)

        uid = user["uid"]
        today_start = self._today_start_iso()
        logs = await self.store.list_ai_usage_logs(
            uid=uid,
            since=today_start,
            limit=5000,
        )

        if action == "turn":
            used = sum(1 for log in logs if log.action == "turn" and log.status == "success")
            limit = int(app_settings.daily_turn_limit)
            label = "turn"
        elif action in CREATE_ACTIONS:
            used = sum(
                1
                for log in logs
                if log.action in CREATE_ACTIONS and log.status == "success"
            )
            limit = int(app_settings.daily_create_limit)
            label = "story creation"
        else:
            return

        if limit <= 0:
            raise DailyLimitExceededError(
                f"Daily {label} limit reached. This action is disabled today."
            )

        if used >= limit:
            raise DailyLimitExceededError(
                f"Daily {label} limit reached ({used}/{limit}). Please come back tomorrow."
            )

    async def spend_points_for_action(
        self,
        user: dict,
        action: str,
        session_id: str | None = None,
    ) -> PointsLedgerEntry | None:
        if user.get("admin"):
            return None

        app_settings = await self.store.get_app_settings()
        if not app_settings.points_enabled:
            return None

        cost = self._cost_for_action(app_settings, action)
        if cost <= 0:
            return None

        state = await self.ensure_user_state(user)
        if state.points_balance < cost:
            raise InsufficientPointsError(
                f"Not enough points. This action costs {cost} points, "
                f"but your balance is {state.points_balance}."
            )

        state.points_balance -= cost
        state.updated_at = utc_now_iso()
        await self.store.upsert_admin_user_state(state)

        entry = PointsLedgerEntry(
            entry_id=str(uuid4()),
            uid=state.uid,
            delta=-cost,
            balance_after=state.points_balance,
            reason=f"AI action: {action}",
            action=f"spend_{action}",
            actor_uid=state.uid,
            session_id=session_id,
        )
        await self.store.append_points_ledger(entry)
        return entry

    async def log_ai_usage(
        self,
        *,
        user: dict,
        action: str,
        operation: str,
        status: str,
        session_id: str | None = None,
        error_kind: str | None = None,
        estimated_input_tokens: int = 0,
        estimated_output_tokens: int = 0,
        actual_input_tokens: int | None = None,
        actual_output_tokens: int | None = None,
        latency_ms: int = 0,
        points_delta: int = 0,
    ) -> AIUsageLogEntry:
        entry = AIUsageLogEntry(
            entry_id=str(uuid4()),
            uid=user["uid"],
            session_id=session_id,
            action=action,
            operation=operation,
            provider=self.settings.text_provider,
            model=self.settings.text_model,
            status=status,
            error_kind=error_kind,
            estimated_input_tokens=max(0, int(estimated_input_tokens)),
            estimated_output_tokens=max(0, int(estimated_output_tokens)),
            actual_input_tokens=actual_input_tokens,
            actual_output_tokens=actual_output_tokens,
            latency_ms=max(0, int(latency_ms)),
            points_delta=int(points_delta or 0),
        )
        await self.store.append_ai_usage_log(entry)
        return entry

    async def adjust_points(
        self,
        target_uid: str,
        delta: int,
        reason: str,
        actor: dict,
    ) -> AdminUserState:
        state = await self._get_or_create_user_state(target_uid)
        new_balance = state.points_balance + delta

        if new_balance < 0:
            raise ValueError("Point balance cannot go below zero")

        state.points_balance = new_balance
        state.updated_at = utc_now_iso()
        await self.store.upsert_admin_user_state(state)

        entry = PointsLedgerEntry(
            entry_id=str(uuid4()),
            uid=target_uid,
            delta=delta,
            balance_after=state.points_balance,
            reason=reason,
            action="admin_adjust",
            actor_uid=actor["uid"],
        )
        await self.store.append_points_ledger(entry)

        await self.audit(
            actor,
            "points.adjust",
            target_uid=target_uid,
            metadata={
                "delta": delta,
                "balance_after": state.points_balance,
                "reason": reason,
            },
        )
        return state

    async def ban_user(self, target_uid: str, reason: str, actor: dict) -> AdminUserState:
        state = await self._get_or_create_user_state(target_uid)
        state.is_banned = True
        state.ban_reason = reason
        state.banned_at = utc_now_iso()
        state.banned_by = actor["uid"]
        state.updated_at = utc_now_iso()
        await self.store.upsert_admin_user_state(state)

        await self.audit(
            actor,
            "user.ban",
            target_uid=target_uid,
            metadata={"reason": reason},
        )
        return state

    async def unban_user(self, target_uid: str, actor: dict) -> AdminUserState:
        state = await self._get_or_create_user_state(target_uid)
        state.is_banned = False
        state.ban_reason = ""
        state.banned_at = None
        state.banned_by = None
        state.updated_at = utc_now_iso()
        await self.store.upsert_admin_user_state(state)

        await self.audit(actor, "user.unban", target_uid=target_uid)
        return state

    async def update_settings(
        self,
        actor: dict,
        **updates,
    ) -> AppSettingsState:
        settings = await self.store.get_app_settings()

        for key, value in updates.items():
            if value is not None:
                setattr(settings, key, value)

        settings.updated_at = utc_now_iso()
        settings.updated_by = actor["uid"]
        await self.store.update_app_settings(settings)

        await self.audit(
            actor,
            "settings.update",
            metadata={key: value for key, value in updates.items() if value is not None},
        )
        return settings

    async def get_overview(self) -> AdminOverviewResponse:
        import asyncio
        settings = await self.store.get_app_settings()
        asyncio.create_task(self.cleanup_old_usage_logs(settings))

        sessions, users, usage_today, usage_30d = await asyncio.gather(
            self.store.admin_list_sessions(limit=5000),
            self.store.list_admin_user_states(limit=5000),
            self.store.list_ai_usage_logs(
                since=self._today_start_iso(),
                limit=5000,
            ),
            self.store.list_ai_usage_logs(
                since=self._days_ago_iso(30),
                limit=5000,
            ),
        )

        user_ids = {session.user_id for session in sessions}
        user_ids.update(user.uid for user in users)

        return AdminOverviewResponse(
            app_name=self.settings.app_name,
            app_env=self.settings.app_env,
            storage_mode=self._storage_mode(),
            text_provider=self.settings.text_provider,
            text_model=self.settings.text_model,
            embedding_provider=self.settings.embedding_provider,
            catalog_count=len(list_world_catalog()),
            sessions_total=len(sessions),
            sessions_saved=sum(1 for session in sessions if session.is_saved),
            sessions_draft=sum(1 for session in sessions if not session.is_saved),
            sessions_adventure=sum(1 for session in sessions if session.mode == "adventure"),
            sessions_novel=sum(1 for session in sessions if session.mode == "novel"),
            users_total=len(user_ids),
            users_banned=sum(1 for user in users if user.is_banned),
            total_points_balance=sum(user.points_balance for user in users),
            usage_today=len(usage_today),
            usage_errors_today=sum(1 for entry in usage_today if entry.status != "success"),
            estimated_tokens_today=sum(
                entry.estimated_input_tokens + entry.estimated_output_tokens
                for entry in usage_today
            ),
            estimated_tokens_30d=sum(
                entry.estimated_input_tokens + entry.estimated_output_tokens
                for entry in usage_30d
            ),
            points_spent_today=sum(
                abs(entry.points_delta)
                for entry in usage_today
                if entry.points_delta < 0
            ),
            latest_updated_at=sessions[0].updated_at if sessions else None,
            settings=settings,
            readiness=build_readiness_report(
                settings=self.settings,
                app_settings=settings,
                firestore_active=bool(self.store.db),
            ),
        )

    async def list_sessions(
        self,
        limit: int = 30,
        before: str | None = None,
        mode: str | None = None,
        saved: bool | None = None,
    ) -> AdminSessionsResponse:
        sessions = await self.store.admin_list_sessions(
            limit=limit,
            before=before,
            mode=mode,
            saved=saved,
        )

        items = [self._session_item(session) for session in sessions]
        next_before = items[-1].updated_at if len(items) == limit else None
        return AdminSessionsResponse(items=items, count=len(items), next_before=next_before)

    async def list_users(self, limit: int = 100) -> AdminUsersResponse:
        sessions = await self.store.admin_list_sessions(limit=5000)
        states = {state.uid: state for state in await self.store.list_admin_user_states(limit=5000)}
        usage_today = await self.store.list_ai_usage_logs(
            since=self._today_start_iso(),
            limit=5000,
        )
        usage_30d = await self.store.list_ai_usage_logs(
            since=self._days_ago_iso(30),
            limit=5000,
        )
        user_ids = set(states)
        user_ids.update(session.user_id for session in sessions)
        user_ids.update(entry.uid for entry in usage_30d)

        session_counts: dict[str, dict[str, int | str | None]] = {}
        for session in sessions:
            counts = session_counts.setdefault(
                session.user_id,
                {"saved": 0, "draft": 0, "latest": None},
            )
            if session.is_saved:
                counts["saved"] = int(counts["saved"]) + 1
            else:
                counts["draft"] = int(counts["draft"]) + 1

            latest = counts["latest"]
            if latest is None or session.updated_at > str(latest):
                counts["latest"] = session.updated_at

        items: list[AdminUserListItem] = []
        for uid in user_ids:
            state = states.get(uid)
            counts = session_counts.get(uid, {"saved": 0, "draft": 0, "latest": None})
            today_logs = [entry for entry in usage_today if entry.uid == uid]
            logs_30d = [entry for entry in usage_30d if entry.uid == uid]
            items.append(
                AdminUserListItem(
                    uid=uid,
                    email=state.email if state else None,
                    name=state.name if state else None,
                    provider=state.provider if state else None,
                    points_balance=state.points_balance if state else 0,
                    is_banned=state.is_banned if state else False,
                    ban_reason=state.ban_reason if state else "",
                    last_seen_at=state.last_seen_at if state else None,
                    saved_sessions=int(counts["saved"]),
                    draft_sessions=int(counts["draft"]),
                    latest_session_at=counts["latest"],
                    usage_today=len(today_logs),
                    usage_30d=len(logs_30d),
                    estimated_tokens_today=sum(
                        entry.estimated_input_tokens + entry.estimated_output_tokens
                        for entry in today_logs
                    ),
                    estimated_tokens_30d=sum(
                        entry.estimated_input_tokens + entry.estimated_output_tokens
                        for entry in logs_30d
                    ),
                )
            )

        items.sort(
            key=lambda item: item.latest_session_at or item.last_seen_at or "",
            reverse=True,
        )
        return AdminUsersResponse(items=items[:limit], count=min(len(items), limit))

    async def list_ledger(
        self,
        uid: str | None = None,
        limit: int = 100,
    ) -> list[PointsLedgerEntry]:
        return await self.store.list_points_ledger(uid=uid, limit=limit)

    async def list_audit_logs(self, limit: int = 100) -> list[AuditLogEntry]:
        return await self.store.list_audit_logs(limit=limit)

    async def get_usage(self, uid: str | None = None, limit: int = 100) -> AdminUsageResponse:
        settings = await self.store.get_app_settings()
        await self.cleanup_old_usage_logs(settings)

        today = await self.store.list_ai_usage_logs(
            uid=uid,
            since=self._today_start_iso(),
            limit=5000,
        )
        last_30d = await self.store.list_ai_usage_logs(
            uid=uid,
            since=self._days_ago_iso(30),
            limit=5000,
        )
        items = await self.store.list_ai_usage_logs(uid=uid, limit=limit)

        return AdminUsageResponse(
            today=self._usage_totals(today),
            last_30d=self._usage_totals(last_30d),
            items=items,
            count=len(items),
        )

    async def list_usage_users(self, limit: int = 100) -> AdminUsageUsersResponse:
        states = {state.uid: state for state in await self.store.list_admin_user_states(limit=5000)}
        usage_today = await self.store.list_ai_usage_logs(
            since=self._today_start_iso(),
            limit=5000,
        )
        usage_30d = await self.store.list_ai_usage_logs(
            since=self._days_ago_iso(30),
            limit=5000,
        )

        user_ids = set(states)
        user_ids.update(entry.uid for entry in usage_30d)

        items: list[AdminUsageUserItem] = []
        for uid in user_ids:
            state = states.get(uid)
            today_logs = [entry for entry in usage_today if entry.uid == uid]
            logs_30d = [entry for entry in usage_30d if entry.uid == uid]
            items.append(
                AdminUsageUserItem(
                    uid=uid,
                    email=state.email if state else None,
                    name=state.name if state else None,
                    requests_today=len(today_logs),
                    requests_30d=len(logs_30d),
                    errors_today=sum(1 for entry in today_logs if entry.status != "success"),
                    estimated_tokens_today=sum(
                        entry.estimated_input_tokens + entry.estimated_output_tokens
                        for entry in today_logs
                    ),
                    estimated_tokens_30d=sum(
                        entry.estimated_input_tokens + entry.estimated_output_tokens
                        for entry in logs_30d
                    ),
                    points_spent_today=sum(
                        abs(entry.points_delta)
                        for entry in today_logs
                        if entry.points_delta < 0
                    ),
                    points_spent_30d=sum(
                        abs(entry.points_delta)
                        for entry in logs_30d
                        if entry.points_delta < 0
                    ),
                )
            )

        items.sort(key=lambda item: item.requests_today, reverse=True)
        return AdminUsageUsersResponse(items=items[:limit], count=min(len(items), limit))

    async def list_ai_errors(self, limit: int = 100) -> AdminErrorsResponse:
        items = await self.store.list_ai_usage_logs(
            limit=limit,
            error_only=True,
        )
        return AdminErrorsResponse(items=items, count=len(items))

    async def cleanup_old_usage_logs(
        self,
        settings: AppSettingsState | None = None,
    ) -> int:
        app_settings = settings or await self.store.get_app_settings()
        retention_days = max(1, int(app_settings.usage_log_retention_days))
        cutoff = self._days_ago_iso(retention_days)
        return await self.store.cleanup_ai_usage_logs(older_than=cutoff)

    async def audit(
        self,
        actor: dict,
        action: str,
        target_uid: str | None = None,
        session_id: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        entry = AuditLogEntry(
            entry_id=str(uuid4()),
            actor_uid=actor["uid"],
            actor_email=actor.get("email"),
            action=action,
            target_uid=target_uid,
            session_id=session_id,
            metadata=metadata or {},
        )
        await self.store.append_audit_log(entry)

    async def _get_or_create_user_state(self, uid: str) -> AdminUserState:
        state = await self.store.get_admin_user_state(uid)
        if state:
            return state

        state = AdminUserState(uid=uid)
        await self.store.upsert_admin_user_state(state)
        return state

    def _cost_for_action(self, settings: AppSettingsState, action: str) -> int:
        key = AI_ACTIONS.get(action)
        if not key:
            return 0
        return int(getattr(settings, key))

    def _usage_totals(self, entries: list[AIUsageLogEntry]) -> AdminUsageTotals:
        return AdminUsageTotals(
            requests=len(entries),
            successes=sum(1 for entry in entries if entry.status == "success"),
            errors=sum(1 for entry in entries if entry.status == "error"),
            blocked=sum(1 for entry in entries if entry.status == "blocked"),
            estimated_input_tokens=sum(entry.estimated_input_tokens for entry in entries),
            estimated_output_tokens=sum(entry.estimated_output_tokens for entry in entries),
            actual_input_tokens=sum(entry.actual_input_tokens or 0 for entry in entries),
            actual_output_tokens=sum(entry.actual_output_tokens or 0 for entry in entries),
            points_spent=sum(abs(entry.points_delta) for entry in entries if entry.points_delta < 0),
        )

    def _today_start_iso(self) -> str:
        now = datetime.now(timezone.utc)
        return now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()

    def _days_ago_iso(self, days: int) -> str:
        return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    def _session_item(self, session: SessionState) -> AdminSessionListItem:
        preview, source = self._preview_for_session(session)

        return AdminSessionListItem(
            session_id=session.session_id,
            user_id=session.user_id,
            title=session.title,
            mode=session.mode,
            is_saved=session.is_saved,
            created_at=session.created_at,
            updated_at=session.updated_at,
            target_words=session.target_words,
            preview=preview,
            summary_source=source,
        )

    def _preview_for_session(self, session: SessionState) -> tuple[str, str]:
        candidates = [
            ("story_summary", session.story_summary),
            ("world_summary", session.world_summary),
            ("foundation_text", session.foundation_text),
            ("character_summary", session.character_summary),
        ]

        for source, text in candidates:
            preview = " ".join((text or "").split())
            if preview:
                return self._truncate(preview, 260), source

        return "", "empty"

    def _truncate(self, text: str, limit: int) -> str:
        if len(text) <= limit:
            return text
        return text[: limit - 1].rstrip() + "…"

    def _storage_mode(self) -> str:
        if self.store.db:
            return "firebase"
        if self.settings.use_local_store_if_firebase_missing:
            return "local-fallback"
        return "firebase-required"