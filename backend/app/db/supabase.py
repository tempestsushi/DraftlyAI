from __future__ import annotations

from threading import Lock
from urllib.parse import quote

import requests

from ..config import settings
from ..models import (
    DraftImageRecord,
    DraftRecord,
    DraftStatus,
    DraftVersionRecord,
    IntegrationRecord,
    IntegrationStatus,
    LinkedInAccountRecord,
    LinkedInOAuthStateRecord,
    LogSource,
    MessageRecord,
    MessageRole,
    MessageSourceRecord,
    TerminalLogRecord,
    TopicRecord,
    TopicStatus,
    utc_now,
)


class SupabaseStore:
    def __init__(self, supabase_url: str, service_role_key: str) -> None:
        self._lock = Lock()
        self._base_url = supabase_url.rstrip("/") + "/rest/v1"
        self._headers = {
            "apikey": service_role_key,
            "Authorization": f"Bearer {service_role_key}",
            "Content-Type": "application/json",
        }

    def initialize(self) -> None:
        self._seed_integrations()

    @staticmethod
    def _serialize_datetime(value):
        return value.isoformat() if value else None

    def _request(
        self,
        method: str,
        table: str,
        *,
        params: str = "",
        json=None,
        prefer: str | None = None,
    ):
        headers = dict(self._headers)
        if prefer:
            headers["Prefer"] = prefer
        url = f"{self._base_url}/{table}{params}"
        response = requests.request(method, url, headers=headers, json=json, timeout=30)
        response.raise_for_status()
        if not response.content:
            return None
        return response.json()

    def _select(self, table: str, params: str = "?select=*") -> list[dict]:
        data = self._request("GET", table, params=params)
        return data if isinstance(data, list) else []

    def _select_one(self, table: str, params: str) -> dict | None:
        rows = self._select(table, params=f"{params}&limit=1")
        return rows[0] if rows else None

    def _insert(self, table: str, payload: dict) -> dict:
        rows = self._request("POST", table, json=payload, prefer="return=representation")
        return rows[0] if isinstance(rows, list) else rows

    def _upsert(self, table: str, payload: dict, *, on_conflict: str = "id") -> dict:
        rows = self._request(
            "POST",
            table,
            params=f"?on_conflict={quote(on_conflict)}",
            json=payload,
            prefer="resolution=merge-duplicates,return=representation",
        )
        return rows[0] if isinstance(rows, list) else rows

    def _patch(self, table: str, params: str, payload: dict) -> dict | None:
        rows = self._request("PATCH", table, params=params, json=payload, prefer="return=representation")
        return rows[0] if isinstance(rows, list) and rows else None

    def _delete(self, table: str, params: str) -> bool:
        rows = self._request("DELETE", table, params=params, prefer="return=representation")
        return bool(rows)

    def _seed_integrations(self) -> None:
        existing = self._select_one("integrations", "?select=*&type=eq.linkedin_publish")
        if existing:
            return
        integration = IntegrationRecord(
            id="linkedin-publish",
            type="linkedin_publish",
            name="LinkedIn Publishing",
            status=IntegrationStatus.disconnected,
        )
        self._insert("integrations", integration.model_dump(mode="json"))

    def list_topics(self) -> list[TopicRecord]:
        with self._lock:
            rows = self._select("topics", "?select=*&order=created_at.desc")
            return [TopicRecord.model_validate(row) for row in rows]

    def get_topic(self, topic_id: str) -> TopicRecord | None:
        with self._lock:
            row = self._select_one("topics", f"?select=*&id=eq.{quote(topic_id)}")
            return TopicRecord.model_validate(row) if row else None

    def create_topic(self, topic: str, status: TopicStatus) -> TopicRecord:
        with self._lock:
            record = TopicRecord(topic=topic, status=status)
            row = self._insert("topics", record.model_dump(mode="json"))
            return TopicRecord.model_validate(row)

    def update_topic_status(self, topic_id: str, status: TopicStatus) -> TopicRecord | None:
        with self._lock:
            row = self._patch(
                "topics",
                f"?id=eq.{quote(topic_id)}",
                {"status": status.value, "updated_at": self._serialize_datetime(utc_now())},
            )
            return TopicRecord.model_validate(row) if row else None

    def update_topic_response(
        self,
        topic_id: str,
        *,
        response_content: str,
        conversation_summary: str | None = None,
        status: TopicStatus | None = None,
    ) -> TopicRecord | None:
        with self._lock:
            current = self._select_one("topics", f"?select=*&id=eq.{quote(topic_id)}")
            if current is None:
                return None
            payload = {
                "response_content": response_content,
                "conversation_summary": conversation_summary
                if conversation_summary is not None
                else current.get("conversation_summary"),
                "status": status.value if status is not None else current["status"],
                "updated_at": self._serialize_datetime(utc_now()),
            }
            row = self._patch("topics", f"?id=eq.{quote(topic_id)}", payload)
            return TopicRecord.model_validate(row) if row else None

    def delete_topic(self, topic_id: str) -> bool:
        with self._lock:
            return self._delete("topics", f"?id=eq.{quote(topic_id)}")

    def add_message(self, topic_id: str, role: MessageRole, content: str) -> MessageRecord:
        with self._lock:
            message = MessageRecord(topic_id=topic_id, role=role, content=content)
            row = self._insert("messages", message.model_dump(mode="json"))
            return MessageRecord.model_validate(row)

    def list_messages(self, topic_id: str) -> list[MessageRecord]:
        with self._lock:
            rows = self._select("messages", f"?select=*&topic_id=eq.{quote(topic_id)}&order=created_at.asc")
            return [MessageRecord.model_validate(row) for row in rows]

    def list_recent_messages(self, topic_id: str, limit: int = 8) -> list[MessageRecord]:
        with self._lock:
            rows = self._select(
                "messages",
                f"?select=*&topic_id=eq.{quote(topic_id)}&order=created_at.desc&limit={limit}",
            )
            return [MessageRecord.model_validate(row) for row in reversed(rows)]

    def update_message(self, topic_id: str, message_id: str, content: str) -> MessageRecord | None:
        with self._lock:
            row = self._patch(
                "messages",
                f"?id=eq.{quote(message_id)}&topic_id=eq.{quote(topic_id)}",
                {"content": content},
            )
            return MessageRecord.model_validate(row) if row else None

    def add_log(self, topic_id: str | None, source: LogSource, message: str) -> TerminalLogRecord:
        with self._lock:
            log = TerminalLogRecord(topic_id=topic_id, source=source, message=message)
            row = self._insert("logs", log.model_dump(mode="json"))
            return TerminalLogRecord.model_validate(row)

    def list_logs(self, topic_id: str | None = None) -> list[TerminalLogRecord]:
        with self._lock:
            params = "?select=*&order=created_at.asc"
            if topic_id is not None:
                params = f"?select=*&topic_id=eq.{quote(topic_id)}&order=created_at.asc"
            rows = self._select("logs", params)
            return [TerminalLogRecord.model_validate(row) for row in rows]

    def add_message_sources(
        self,
        topic_id: str,
        message_id: str,
        sources: list[dict[str, str | None]],
    ) -> list[MessageSourceRecord]:
        with self._lock:
            records = [
                MessageSourceRecord(
                    topic_id=topic_id,
                    message_id=message_id,
                    title=str(source["title"]),
                    url=str(source["url"]),
                    domain=str(source["domain"]) if source.get("domain") else None,
                    snippet=str(source["snippet"]) if source.get("snippet") else None,
                )
                for source in sources
                if source.get("title") and source.get("url")
            ]
            if not records:
                return []
            rows = self._request(
                "POST",
                "message_sources",
                json=[record.model_dump(mode="json") for record in records],
                prefer="return=representation",
            )
            return [MessageSourceRecord.model_validate(row) for row in rows]

    def list_message_sources(self, topic_id: str) -> list[MessageSourceRecord]:
        with self._lock:
            rows = self._select("message_sources", f"?select=*&topic_id=eq.{quote(topic_id)}&order=created_at.asc")
            return [MessageSourceRecord.model_validate(row) for row in rows]

    def _add_draft_version_unlocked(self, *, draft_id: str, content: str, reason: str) -> DraftVersionRecord:
        rows = self._select(
            "draft_versions",
            f"?select=version_number&draft_id=eq.{quote(draft_id)}&order=version_number.desc&limit=1",
        )
        latest = int(rows[0]["version_number"]) if rows else 0
        version = DraftVersionRecord(
            draft_id=draft_id,
            version_number=latest + 1,
            content=content,
            reason=reason,
        )
        row = self._insert("draft_versions", version.model_dump(mode="json"))
        return DraftVersionRecord.model_validate(row)

    def add_draft(
        self,
        *,
        title: str,
        content: str,
        source: str,
        topic_id: str | None = None,
        source_message_id: str | None = None,
    ) -> DraftRecord:
        with self._lock:
            draft = DraftRecord(
                title=title,
                content=content,
                source=source,
                topic_id=topic_id,
                source_message_id=source_message_id,
            )
            row = self._insert("drafts", draft.model_dump(mode="json"))
            self._add_draft_version_unlocked(draft_id=draft.id, content=draft.content, reason="created")
            return DraftRecord.model_validate(row)

    def list_drafts(self) -> list[DraftRecord]:
        with self._lock:
            rows = self._select("drafts", "?select=*&order=created_at.desc")
            return [DraftRecord.model_validate(row) for row in rows]

    def get_draft(self, draft_id: str) -> DraftRecord | None:
        with self._lock:
            row = self._select_one("drafts", f"?select=*&id=eq.{quote(draft_id)}")
            return DraftRecord.model_validate(row) if row else None

    def update_draft_status(
        self,
        draft_id: str,
        *,
        status: DraftStatus,
        linkedin_post_url: str | None = None,
    ) -> DraftRecord | None:
        with self._lock:
            payload = {"status": status.value, "updated_at": self._serialize_datetime(utc_now())}
            if linkedin_post_url:
                payload["linkedin_post_url"] = linkedin_post_url
                payload["posted_at"] = self._serialize_datetime(utc_now())
            row = self._patch("drafts", f"?id=eq.{quote(draft_id)}", payload)
            return DraftRecord.model_validate(row) if row else None

    def update_draft(
        self,
        draft_id: str,
        *,
        content: str | None = None,
        status: DraftStatus | None = None,
        clear_linkedin_post: bool = False,
        version_reason: str = "edited",
    ) -> DraftRecord | None:
        with self._lock:
            current = self._select_one("drafts", f"?select=*&id=eq.{quote(draft_id)}")
            if current is None:
                return None
            payload = {"updated_at": self._serialize_datetime(utc_now())}
            if content is not None:
                payload["content"] = content
                if current.get("status") == DraftStatus.published.value:
                    payload["status"] = DraftStatus.approved.value
            if status is not None:
                payload["status"] = status.value
            if clear_linkedin_post:
                payload["linkedin_post_url"] = None
                payload["posted_at"] = None
            row = self._patch("drafts", f"?id=eq.{quote(draft_id)}", payload)
            if content is not None and content != current["content"]:
                self._add_draft_version_unlocked(draft_id=draft_id, content=content, reason=version_reason)
            return DraftRecord.model_validate(row) if row else None

    def list_draft_versions(self, draft_id: str) -> list[DraftVersionRecord]:
        with self._lock:
            rows = self._select(
                "draft_versions",
                f"?select=*&draft_id=eq.{quote(draft_id)}&order=version_number.desc",
            )
            return [DraftVersionRecord.model_validate(row) for row in rows]

    def save_draft_image(
        self,
        *,
        draft_id: str,
        title: str,
        image_url: str,
        source_url: str,
        topic_id: str | None = None,
        thumbnail_url: str | None = None,
        source_domain: str | None = None,
        provider: str = "gemini-image",
        width: int | None = None,
        height: int | None = None,
    ) -> DraftImageRecord:
        with self._lock:
            existing_rows = self._select("draft_images", f"?select=*&draft_id=eq.{quote(draft_id)}")
            existing = next((row for row in existing_rows if row.get("image_url") == image_url), None)
            if existing:
                return DraftImageRecord.model_validate(existing)
            image = DraftImageRecord(
                draft_id=draft_id,
                topic_id=topic_id,
                title=title,
                image_url=image_url,
                thumbnail_url=thumbnail_url,
                source_url=source_url,
                source_domain=source_domain,
                provider=provider,
                width=width,
                height=height,
            )
            row = self._insert("draft_images", image.model_dump(mode="json"))
            return DraftImageRecord.model_validate(row)

    def get_draft_image(self, draft_id: str) -> DraftImageRecord | None:
        with self._lock:
            row = self._select_one(
                "draft_images",
                f"?select=*&draft_id=eq.{quote(draft_id)}&order=created_at.asc",
            )
            return DraftImageRecord.model_validate(row) if row else None

    def list_draft_images(self, draft_id: str) -> list[DraftImageRecord]:
        with self._lock:
            rows = self._select("draft_images", f"?select=*&draft_id=eq.{quote(draft_id)}&order=created_at.asc")
            return [DraftImageRecord.model_validate(row) for row in rows]

    def delete_draft_image(self, draft_id: str) -> bool:
        with self._lock:
            return self._delete("draft_images", f"?draft_id=eq.{quote(draft_id)}")

    def delete_draft_image_by_id(self, draft_id: str, image_id: str) -> bool:
        with self._lock:
            return self._delete("draft_images", f"?draft_id=eq.{quote(draft_id)}&id=eq.{quote(image_id)}")

    def list_integrations(self) -> list[IntegrationRecord]:
        with self._lock:
            rows = self._select("integrations", "?select=*&order=name.asc")
            return [IntegrationRecord.model_validate(row) for row in rows]

    def update_integration(
        self,
        integration_id: str,
        *,
        status: IntegrationStatus,
        connected_at,
    ) -> IntegrationRecord | None:
        with self._lock:
            row = self._patch(
                "integrations",
                f"?id=eq.{quote(integration_id)}",
                {"status": status.value, "connected_at": self._serialize_datetime(connected_at)},
            )
            return IntegrationRecord.model_validate(row) if row else None

    def create_linkedin_oauth_state(self, state: str, expires_at) -> LinkedInOAuthStateRecord:
        with self._lock:
            record = LinkedInOAuthStateRecord(state=state, expires_at=expires_at)
            row = self._upsert(
                "linkedin_oauth_states",
                record.model_dump(mode="json"),
                on_conflict="state",
            )
            return LinkedInOAuthStateRecord.model_validate(row)

    def consume_linkedin_oauth_state(self, state: str) -> LinkedInOAuthStateRecord | None:
        with self._lock:
            row = self._select_one("linkedin_oauth_states", f"?select=*&state=eq.{quote(state)}")
            if row is None:
                return None
            self._delete("linkedin_oauth_states", f"?state=eq.{quote(state)}")
            return LinkedInOAuthStateRecord.model_validate(row)

    def get_linkedin_account(self) -> LinkedInAccountRecord | None:
        with self._lock:
            row = self._select_one("linkedin_accounts", "?select=*&id=eq.primary")
            return LinkedInAccountRecord.model_validate(row) if row else None

    def save_linkedin_account(self, account: LinkedInAccountRecord) -> LinkedInAccountRecord:
        with self._lock:
            row = self._upsert(
                "linkedin_accounts",
                account.model_dump(mode="json"),
                on_conflict="id",
            )
            return LinkedInAccountRecord.model_validate(row)

    def delete_linkedin_account(self) -> bool:
        with self._lock:
            deleted = self._delete("linkedin_accounts", "?id=eq.primary")
            self._patch(
                "integrations",
                "?id=eq.linkedin-publish",
                {"status": IntegrationStatus.disconnected.value, "connected_at": None},
            )
            return deleted


def create_supabase_store() -> SupabaseStore:
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")
    return SupabaseStore(settings.supabase_url, settings.supabase_service_role_key)
