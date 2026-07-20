from __future__ import annotations

from threading import Lock

from app.models import (
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


class InMemoryStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self.topics: dict[str, TopicRecord] = {}
        self.messages: dict[str, MessageRecord] = {}
        self.logs: dict[str, TerminalLogRecord] = {}
        self.message_sources: dict[str, MessageSourceRecord] = {}
        self.drafts: dict[str, DraftRecord] = {}
        self.draft_versions: dict[str, DraftVersionRecord] = {}
        self.draft_images: dict[str, DraftImageRecord] = {}
        self.integrations: dict[str, IntegrationRecord] = {}
        self.linkedin_accounts: dict[str, LinkedInAccountRecord] = {}
        self.linkedin_oauth_states: dict[str, LinkedInOAuthStateRecord] = {}

    def initialize(self) -> None:
        if not any(item.type == "linkedin_publish" for item in self.integrations.values()):
            integration = IntegrationRecord(
                id="linkedin-publish",
                type="linkedin_publish",
                name="LinkedIn Publishing",
                status=IntegrationStatus.disconnected,
            )
            self.integrations[integration.id] = integration

    def list_topics(self) -> list[TopicRecord]:
        return sorted(self.topics.values(), key=lambda item: item.created_at, reverse=True)

    def get_topic(self, topic_id: str) -> TopicRecord | None:
        return self.topics.get(topic_id)

    def create_topic(self, topic: str, status: TopicStatus) -> TopicRecord:
        record = TopicRecord(topic=topic, status=status)
        self.topics[record.id] = record
        return record

    def update_topic_status(self, topic_id: str, status: TopicStatus) -> TopicRecord | None:
        record = self.topics.get(topic_id)
        if record is None:
            return None
        updated = record.model_copy(update={"status": status, "updated_at": utc_now()})
        self.topics[topic_id] = updated
        return updated

    def update_topic_response(
        self,
        topic_id: str,
        *,
        response_content: str,
        conversation_summary: str | None = None,
        status: TopicStatus | None = None,
    ) -> TopicRecord | None:
        record = self.topics.get(topic_id)
        if record is None:
            return None
        updated = record.model_copy(
            update={
                "response_content": response_content,
                "conversation_summary": conversation_summary
                if conversation_summary is not None
                else record.conversation_summary,
                "status": status or record.status,
                "updated_at": utc_now(),
            }
        )
        self.topics[topic_id] = updated
        return updated

    def delete_topic(self, topic_id: str) -> bool:
        if topic_id not in self.topics:
            return False
        self.topics.pop(topic_id)
        self.messages = {key: value for key, value in self.messages.items() if value.topic_id != topic_id}
        self.logs = {key: value for key, value in self.logs.items() if value.topic_id != topic_id}
        self.message_sources = {
            key: value for key, value in self.message_sources.items() if value.topic_id != topic_id
        }
        self.drafts = {key: value for key, value in self.drafts.items() if value.topic_id != topic_id}
        self.draft_images = {key: value for key, value in self.draft_images.items() if value.topic_id != topic_id}
        return True

    def add_message(self, topic_id: str, role: MessageRole, content: str) -> MessageRecord:
        message = MessageRecord(topic_id=topic_id, role=role, content=content)
        self.messages[message.id] = message
        return message

    def list_messages(self, topic_id: str) -> list[MessageRecord]:
        rows = [message for message in self.messages.values() if message.topic_id == topic_id]
        return sorted(rows, key=lambda item: item.created_at)

    def list_recent_messages(self, topic_id: str, limit: int = 8) -> list[MessageRecord]:
        return self.list_messages(topic_id)[-limit:]

    def update_message(self, topic_id: str, message_id: str, content: str) -> MessageRecord | None:
        message = self.messages.get(message_id)
        if message is None or message.topic_id != topic_id:
            return None
        updated = message.model_copy(update={"content": content})
        self.messages[message_id] = updated
        return updated

    def add_log(self, topic_id: str | None, source: LogSource, message: str) -> TerminalLogRecord:
        log = TerminalLogRecord(topic_id=topic_id, source=source, message=message)
        self.logs[log.id] = log
        return log

    def list_logs(self, topic_id: str | None = None) -> list[TerminalLogRecord]:
        rows = [log for log in self.logs.values() if topic_id is None or log.topic_id == topic_id]
        return sorted(rows, key=lambda item: item.created_at)

    def add_message_sources(
        self,
        topic_id: str,
        message_id: str,
        sources: list[dict[str, str | None]],
    ) -> list[MessageSourceRecord]:
        records: list[MessageSourceRecord] = []
        for source in sources:
            if not source.get("title") or not source.get("url"):
                continue
            record = MessageSourceRecord(
                topic_id=topic_id,
                message_id=message_id,
                title=str(source["title"]),
                url=str(source["url"]),
                domain=str(source["domain"]) if source.get("domain") else None,
                snippet=str(source["snippet"]) if source.get("snippet") else None,
            )
            self.message_sources[record.id] = record
            records.append(record)
        return records

    def list_message_sources(self, topic_id: str) -> list[MessageSourceRecord]:
        rows = [source for source in self.message_sources.values() if source.topic_id == topic_id]
        return sorted(rows, key=lambda item: item.created_at)

    def _add_draft_version(self, draft_id: str, content: str, reason: str) -> DraftVersionRecord:
        latest = max(
            (version.version_number for version in self.draft_versions.values() if version.draft_id == draft_id),
            default=0,
        )
        version = DraftVersionRecord(
            draft_id=draft_id,
            version_number=latest + 1,
            content=content,
            reason=reason,
        )
        self.draft_versions[version.id] = version
        return version

    def add_draft(
        self,
        *,
        title: str,
        content: str,
        source: str,
        topic_id: str | None = None,
        source_message_id: str | None = None,
    ) -> DraftRecord:
        draft = DraftRecord(
            title=title,
            content=content,
            source=source,
            topic_id=topic_id,
            source_message_id=source_message_id,
        )
        self.drafts[draft.id] = draft
        self._add_draft_version(draft.id, draft.content, "created")
        return draft

    def list_drafts(self) -> list[DraftRecord]:
        return sorted(self.drafts.values(), key=lambda item: item.created_at, reverse=True)

    def get_draft(self, draft_id: str) -> DraftRecord | None:
        return self.drafts.get(draft_id)

    def update_draft_status(
        self,
        draft_id: str,
        *,
        status: DraftStatus,
        linkedin_post_url: str | None = None,
    ) -> DraftRecord | None:
        draft = self.drafts.get(draft_id)
        if draft is None:
            return None
        updated = draft.model_copy(
            update={
                "status": status,
                "linkedin_post_url": linkedin_post_url or draft.linkedin_post_url,
                "posted_at": utc_now() if linkedin_post_url else draft.posted_at,
                "updated_at": utc_now(),
            }
        )
        self.drafts[draft_id] = updated
        return updated

    def update_draft(
        self,
        draft_id: str,
        *,
        content: str | None = None,
        status: DraftStatus | None = None,
        clear_linkedin_post: bool = False,
        version_reason: str = "edited",
    ) -> DraftRecord | None:
        draft = self.drafts.get(draft_id)
        if draft is None:
            return None
        updated = draft.model_copy(
            update={
                "content": content if content is not None else draft.content,
                "status": status or (DraftStatus.approved if content is not None and draft.status == DraftStatus.published else draft.status),
                "linkedin_post_url": None if clear_linkedin_post else draft.linkedin_post_url,
                "posted_at": None if clear_linkedin_post else draft.posted_at,
                "updated_at": utc_now(),
            }
        )
        self.drafts[draft_id] = updated
        if content is not None and content != draft.content:
            self._add_draft_version(draft_id, content, version_reason)
        return updated

    def list_draft_versions(self, draft_id: str) -> list[DraftVersionRecord]:
        rows = [version for version in self.draft_versions.values() if version.draft_id == draft_id]
        return sorted(rows, key=lambda item: item.version_number, reverse=True)

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
        existing = next(
            (
                image
                for image in self.draft_images.values()
                if image.draft_id == draft_id and image.image_url == image_url
            ),
            None,
        )
        if existing:
            return existing
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
        self.draft_images[image.id] = image
        return image

    def get_draft_image(self, draft_id: str) -> DraftImageRecord | None:
        images = self.list_draft_images(draft_id)
        return images[0] if images else None

    def list_draft_images(self, draft_id: str) -> list[DraftImageRecord]:
        rows = [image for image in self.draft_images.values() if image.draft_id == draft_id]
        return sorted(rows, key=lambda item: item.created_at)

    def delete_draft_image(self, draft_id: str) -> bool:
        ids = [image_id for image_id, image in self.draft_images.items() if image.draft_id == draft_id]
        for image_id in ids:
            self.draft_images.pop(image_id)
        return bool(ids)

    def delete_draft_image_by_id(self, draft_id: str, image_id: str) -> bool:
        image = self.draft_images.get(image_id)
        if image is None or image.draft_id != draft_id:
            return False
        self.draft_images.pop(image_id)
        return True

    def list_integrations(self) -> list[IntegrationRecord]:
        return sorted(self.integrations.values(), key=lambda item: item.name)

    def update_integration(
        self,
        integration_id: str,
        *,
        status: IntegrationStatus,
        connected_at,
    ) -> IntegrationRecord | None:
        integration = self.integrations.get(integration_id)
        if integration is None:
            return None
        updated = integration.model_copy(update={"status": status, "connected_at": connected_at})
        self.integrations[integration_id] = updated
        return updated

    def create_linkedin_oauth_state(self, state: str, expires_at) -> LinkedInOAuthStateRecord:
        record = LinkedInOAuthStateRecord(state=state, expires_at=expires_at)
        self.linkedin_oauth_states[state] = record
        return record

    def consume_linkedin_oauth_state(self, state: str) -> LinkedInOAuthStateRecord | None:
        return self.linkedin_oauth_states.pop(state, None)

    def get_linkedin_account(self) -> LinkedInAccountRecord | None:
        return self.linkedin_accounts.get("primary")

    def save_linkedin_account(self, account: LinkedInAccountRecord) -> LinkedInAccountRecord:
        self.linkedin_accounts[account.id] = account
        return account

    def delete_linkedin_account(self) -> bool:
        existed = self.linkedin_accounts.pop("primary", None) is not None
        self.update_integration("linkedin-publish", status=IntegrationStatus.disconnected, connected_at=None)
        return existed
