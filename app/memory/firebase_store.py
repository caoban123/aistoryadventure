from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.domain.models import (
    AIUsageLogEntry,
    AdminUserState,
    AppSettingsState,
    AuditLogEntry,
    CommunityWorld,
    Message,
    PointsLedgerEntry,
    SessionState,
)


class FirebaseStore:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.db = None
        self.local_dir = Path(self.settings.local_data_dir)
        self.local_dir.mkdir(parents=True, exist_ok=True)
        self._init_firestore()

    def _init_firestore(self) -> None:
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore

            if firebase_admin._apps:
                self.db = firestore.client()
                return

            cred = None
            if self.settings.firebase_credentials_path:
                cred = credentials.Certificate(self.settings.firebase_credentials_path)
            elif self.settings.firebase_service_account_json:
                data = json.loads(self.settings.firebase_service_account_json)
                cred = credentials.Certificate(data)

            if cred:
                firebase_admin.initialize_app(cred)
                self.db = firestore.client()
            elif not self.settings.use_local_store_if_firebase_missing:
                raise RuntimeError("Missing Firebase credentials")
        except Exception:
            if not self.settings.use_local_store_if_firebase_missing:
                raise
            self.db = None

    def _session_file(self, session_id: str) -> Path:
        return self.local_dir / f"{session_id}.json"

    def _admin_file(self) -> Path:
        return self.local_dir / "_admin_state.json"

    def _read_admin_state(self) -> dict[str, Any]:
        path = self._admin_file()
        if not path.exists():
            return {
                "users": {},
                "points_ledger": [],
                "settings": AppSettingsState().model_dump(),
                "audit_logs": [],
                "ai_usage_logs": [],
                "community_worlds": {},
            }

        data = json.loads(path.read_text(encoding="utf-8"))
        data.setdefault("users", {})
        data.setdefault("points_ledger", [])
        data.setdefault("settings", AppSettingsState().model_dump())
        data.setdefault("audit_logs", [])
        data.setdefault("ai_usage_logs", [])
        data.setdefault("community_worlds", {})
        return data

    def _write_admin_state(self, data: dict[str, Any]) -> None:
        self._admin_file().write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    async def create_session(self, session: SessionState) -> None:
        if self.db:
            self.db.collection("sessions").document(session.session_id).set(session.model_dump())
            return
        self._write_local(session, [])

    async def get_session(self, session_id: str) -> SessionState | None:
        if self.db:
            doc = self.db.collection("sessions").document(session_id).get()
            if not doc.exists:
                return None
            return SessionState(**doc.to_dict())
        path = self._session_file(session_id)
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return SessionState(**data["session"])

    async def update_session(self, session: SessionState) -> None:
        if self.db:
            self.db.collection("sessions").document(session.session_id).set(session.model_dump(), merge=True)
            return
        messages = await self.get_messages(session.session_id, limit=9999)
        self._write_local(session, messages)

    async def add_message(self, message: Message) -> None:
        if self.db:
            self.db.collection("sessions").document(message.session_id).collection("messages").document(message.message_id).set(message.model_dump())
            return
        session = await self.get_session(message.session_id)
        messages = await self.get_messages(message.session_id, limit=9999)
        messages.append(message)
        if session:
            self._write_local(session, messages)

    async def get_messages(self, session_id: str, limit: int = 20) -> list[Message]:
        if self.db:
            docs = (
                self.db.collection("sessions")
                .document(session_id)
                .collection("messages")
                .order_by("created_at")
                .stream()
            )
            messages = [Message(**doc.to_dict()) for doc in docs]
            return messages[-limit:]
        path = self._session_file(session_id)
        if not path.exists():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        messages = [Message(**m) for m in data.get("messages", [])]
        return messages[-limit:]

    def _write_local(self, session: SessionState, messages: list[Message]) -> None:
        payload: dict[str, Any] = {
            "session": session.model_dump(),
            "messages": [m.model_dump() for m in messages],
        }
        self._session_file(session.session_id).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    async def list_sessions(self, user_id: str, limit: int = 20,) -> list[SessionState]:
        if self.db:
            docs = (
                self.db.collection("sessions")
                .where("user_id", "==", user_id)
                .order_by("updated_at", direction="DESCENDING")
                .limit(max(limit * 10, 200))
                .stream()
            )

            sessions = [
                session
                for session in (SessionState(**doc.to_dict()) for doc in docs)
                if session.is_saved
            ]
            return sessions[:limit]

        files = sorted(
            self.local_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        sessions: list[SessionState] = []

        for path in files:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                session = SessionState(**data["session"])

                if session.user_id != user_id:
                    continue

                if not session.is_saved:
                    continue

                sessions.append(session)

                if len(sessions) >= limit:
                    break
            except Exception:
                continue

        return sessions

    async def admin_list_sessions(
        self,
        limit: int = 100,
        before: str | None = None,
        mode: str | None = None,
        saved: bool | None = None,
    ) -> list[SessionState]:
        if self.db:
            docs = (
                self.db.collection("sessions")
                .order_by("updated_at", direction="DESCENDING")
                .limit(min(max(limit * 5, 200), 5000))
                .stream()
            )
            candidates = [SessionState(**doc.to_dict()) for doc in docs]
        else:
            candidates = []
            for path in self.local_dir.glob("*.json"):
                if path.name.startswith("_"):
                    continue
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    candidates.append(SessionState(**data["session"]))
                except Exception:
                    continue
            candidates.sort(key=lambda session: session.updated_at, reverse=True)

        sessions: list[SessionState] = []

        for session in candidates:
            if before and session.updated_at >= before:
                continue
            if mode and session.mode != mode:
                continue
            if saved is not None and session.is_saved is not saved:
                continue

            sessions.append(session)

            if len(sessions) >= limit:
                break

        return sessions

    async def get_admin_user_state(self, uid: str) -> AdminUserState | None:
        if self.db:
            doc = self.db.collection("admin_user_states").document(uid).get()
            if not doc.exists:
                return None
            return AdminUserState(**doc.to_dict())

        data = self._read_admin_state()
        user = data["users"].get(uid)
        return AdminUserState(**user) if user else None

    async def upsert_admin_user_state(self, state: AdminUserState) -> None:
        if self.db:
            self.db.collection("admin_user_states").document(state.uid).set(
                state.model_dump(),
                merge=True,
            )
            return

        data = self._read_admin_state()
        data["users"][state.uid] = state.model_dump()
        self._write_admin_state(data)

    async def list_admin_user_states(self, limit: int = 100) -> list[AdminUserState]:
        if self.db:
            docs = (
                self.db.collection("admin_user_states")
                .order_by("last_seen_at", direction="DESCENDING")
                .limit(limit)
                .stream()
            )
            return [AdminUserState(**doc.to_dict()) for doc in docs]

        data = self._read_admin_state()
        users = [AdminUserState(**item) for item in data["users"].values()]
        users.sort(key=lambda user: user.last_seen_at, reverse=True)
        return users[:limit]

    async def get_app_settings(self) -> AppSettingsState:
        if self.db:
            doc = self.db.collection("admin_settings").document("app").get(
                timeout=self.settings.firestore_timeout_seconds,
            )
            if not doc.exists:
                return AppSettingsState()
            return AppSettingsState(**doc.to_dict())

        data = self._read_admin_state()
        return AppSettingsState(**data["settings"])

    async def update_app_settings(self, settings: AppSettingsState) -> None:
        if self.db:
            self.db.collection("admin_settings").document("app").set(
                settings.model_dump(),
                merge=True,
            )
            return

        data = self._read_admin_state()
        data["settings"] = settings.model_dump()
        self._write_admin_state(data)

    async def append_points_ledger(self, entry: PointsLedgerEntry) -> None:
        if self.db:
            self.db.collection("admin_points_ledger").document(entry.entry_id).set(
                entry.model_dump()
            )
            return

        data = self._read_admin_state()
        data["points_ledger"].append(entry.model_dump())
        self._write_admin_state(data)

    async def list_points_ledger(
        self,
        uid: str | None = None,
        limit: int = 100,
    ) -> list[PointsLedgerEntry]:
        if self.db:
            docs = (
                self.db.collection("admin_points_ledger")
                .order_by("created_at", direction="DESCENDING")
                .limit(max(limit * 5, 200))
                .stream()
            )
            entries = [PointsLedgerEntry(**doc.to_dict()) for doc in docs]
        else:
            data = self._read_admin_state()
            entries = [PointsLedgerEntry(**item) for item in data["points_ledger"]]
            entries.sort(key=lambda entry: entry.created_at, reverse=True)

        if uid:
            entries = [entry for entry in entries if entry.uid == uid]

        return entries[:limit]

    async def append_audit_log(self, entry: AuditLogEntry) -> None:
        if self.db:
            self.db.collection("admin_audit_logs").document(entry.entry_id).set(
                entry.model_dump()
            )
            return

        data = self._read_admin_state()
        data["audit_logs"].append(entry.model_dump())
        self._write_admin_state(data)

    async def list_audit_logs(self, limit: int = 100) -> list[AuditLogEntry]:
        if self.db:
            docs = (
                self.db.collection("admin_audit_logs")
                .order_by("created_at", direction="DESCENDING")
                .limit(limit)
                .stream()
            )
            return [AuditLogEntry(**doc.to_dict()) for doc in docs]

        data = self._read_admin_state()
        entries = [AuditLogEntry(**item) for item in data["audit_logs"]]
        entries.sort(key=lambda entry: entry.created_at, reverse=True)
        return entries[:limit]

    async def append_ai_usage_log(self, entry: AIUsageLogEntry) -> None:
        if self.db:
            self.db.collection("admin_ai_usage_logs").document(entry.entry_id).set(
                entry.model_dump()
            )
            return

        data = self._read_admin_state()
        data["ai_usage_logs"].append(entry.model_dump())
        self._write_admin_state(data)

    async def list_ai_usage_logs(
        self,
        limit: int = 100,
        uid: str | None = None,
        since: str | None = None,
        status: str | None = None,
        error_only: bool = False,
    ) -> list[AIUsageLogEntry]:
        if self.db:
            docs = (
                self.db.collection("admin_ai_usage_logs")
                .order_by("created_at", direction="DESCENDING")
                .limit(max(limit * 5, 200))
                .stream()
            )
            entries = [AIUsageLogEntry(**doc.to_dict()) for doc in docs]
        else:
            data = self._read_admin_state()
            entries = [AIUsageLogEntry(**item) for item in data["ai_usage_logs"]]
            entries.sort(key=lambda entry: entry.created_at, reverse=True)

        if uid:
            entries = [entry for entry in entries if entry.uid == uid]
        if since:
            entries = [entry for entry in entries if entry.created_at >= since]
        if status:
            entries = [entry for entry in entries if entry.status == status]
        if error_only:
            entries = [
                entry
                for entry in entries
                if entry.status in {"error", "blocked"} or bool(entry.error_kind)
            ]

        return entries[:limit]

    async def cleanup_ai_usage_logs(self, older_than: str) -> int:
        removed = 0

        if self.db:
            docs = (
                self.db.collection("admin_ai_usage_logs")
                .where("created_at", "<", older_than)
                .limit(500)
                .stream()
            )
            for doc in docs:
                doc.reference.delete()
                removed += 1
            return removed

        data = self._read_admin_state()
        kept = []
        for item in data["ai_usage_logs"]:
            if str(item.get("created_at", "")) < older_than:
                removed += 1
                continue
            kept.append(item)

        if removed:
            data["ai_usage_logs"] = kept
            self._write_admin_state(data)

        return removed

    async def list_old_draft_sessions(
        self,
        user_id: str,
        older_than: str,
        limit: int = 100,
    ) -> list[SessionState]:
        if self.db:
            docs = (
                self.db.collection("sessions")
                .where("user_id", "==", user_id)
                .limit(max(limit * 5, 100))
                .stream()
            )

            sessions = []
            for doc in docs:
                session = SessionState(**doc.to_dict())

                if session.is_saved:
                    continue
                if (session.updated_at or session.created_at) >= older_than:
                    continue

                sessions.append(session)

                if len(sessions) >= limit:
                    break

            return sessions

        files = sorted(
            self.local_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
        )

        sessions: list[SessionState] = []

        for path in files:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                session = SessionState(**data["session"])

                if session.user_id != user_id:
                    continue
                if session.is_saved:
                    continue
                if (session.updated_at or session.created_at) >= older_than:
                    continue

                sessions.append(session)

                if len(sessions) >= limit:
                    break
            except Exception:
                continue

        return sessions

    async def delete_session(self, session_id: str) -> None:
        if self.db:
            session_ref = self.db.collection("sessions").document(session_id)

            messages = session_ref.collection("messages").stream()

            for msg in messages:
                msg.reference.delete()

            session_ref.delete()
            return

        path = self._session_file(session_id)

        if path.exists():
            path.unlink()

    async def create_community_world(self, item: CommunityWorld) -> None:
        if self.db:
            self.db.collection("community_worlds").document(item.id).set(item.model_dump())
            return
        data = self._read_admin_state()
        data["community_worlds"][item.id] = item.model_dump()
        self._write_admin_state(data)

    async def get_community_world(self, item_id: str) -> CommunityWorld | None:
        if self.db:
            doc = self.db.collection("community_worlds").document(item_id).get()
            if not doc.exists:
                return None
            return CommunityWorld(**doc.to_dict())
        data = self._read_admin_state()
        item = data["community_worlds"].get(item_id)
        return CommunityWorld(**item) if item else None

    async def update_community_world(self, item: CommunityWorld) -> None:
        if self.db:
            self.db.collection("community_worlds").document(item.id).set(item.model_dump(), merge=True)
            return
        data = self._read_admin_state()
        data["community_worlds"][item.id] = item.model_dump()
        self._write_admin_state(data)

    async def delete_community_world(self, item_id: str) -> None:
        if self.db:
            self.db.collection("community_worlds").document(item_id).delete()
            return
        data = self._read_admin_state()
        if item_id in data["community_worlds"]:
            del data["community_worlds"][item_id]
            self._write_admin_state(data)

    async def list_community_worlds(self, approved_only: bool = True, limit: int = 100) -> list[CommunityWorld]:
        if self.db:
            ref = self.db.collection("community_worlds")
            if approved_only:
                docs = ref.where("is_approved", "==", True).limit(limit).stream()
            else:
                docs = ref.limit(limit).stream()
            # Sort in memory to avoid index requirements in Firestore (less strict setup for first launch)
            worlds = [CommunityWorld(**doc.to_dict()) for doc in docs]
            worlds.sort(key=lambda w: w.created_at, reverse=True)
            return worlds[:limit]
        
        data = self._read_admin_state()
        worlds = [CommunityWorld(**item) for item in data["community_worlds"].values()]
        if approved_only:
            worlds = [w for w in worlds if w.is_approved]
        worlds.sort(key=lambda w: w.created_at, reverse=True)
        return worlds[:limit]

