from __future__ import annotations

import asyncio

from app.models import DraftStatus, MessageRole, TopicStatus


def test_list_drafts_can_filter_by_topic(client, test_store) -> None:
    topic_a = test_store.create_topic("Topic A", TopicStatus.pending)
    topic_b = test_store.create_topic("Topic B", TopicStatus.pending)
    test_store.add_draft(title="Draft A", content="A", source="research", topic_id=topic_a.id)
    test_store.add_draft(title="Draft B", content="B", source="research", topic_id=topic_b.id)

    response = client.get("/api/drafts", params={"topic_id": topic_a.id})

    assert response.status_code == 200
    drafts = response.json()
    assert len(drafts) == 1
    assert drafts[0]["topic_id"] == topic_a.id


def test_create_topic_draft_uses_latest_assistant_message(client, monkeypatch, test_store) -> None:
    topic = test_store.create_topic("LangGraph", TopicStatus.complete)
    test_store.add_message(topic.id, MessageRole.user, "Explain LangGraph")
    assistant = test_store.add_message(topic.id, MessageRole.assistant, "LangGraph helps orchestrate stateful flows.")

    async def fake_create_draft_from_topic_response(store, topic_id, title=None, message_id=None, **kwargs):
        assert store is test_store
        assert topic_id == topic.id
        assert message_id is None
        assert kwargs["tone"].value == "professional"
        return store.add_draft(
            title=title or "Generated draft",
            content=f"Draft from {assistant.id}",
            source="research",
            topic_id=topic_id,
            source_message_id=assistant.id,
        )

    monkeypatch.setattr(
        "app.routes.topics.create_draft_from_topic_response",
        fake_create_draft_from_topic_response,
    )

    response = client.post(f"/api/topics/{topic.id}/draft", json={})

    assert response.status_code == 200
    body = response.json()
    assert body["topic_id"] == topic.id
    assert body["source_message_id"] == assistant.id


def test_update_draft_changes_content_and_status(client, test_store) -> None:
    draft = test_store.add_draft(title="Original", content="Before", source="research")

    response = client.patch(
        f"/api/drafts/{draft.id}",
        json={"content": "After", "status": DraftStatus.approved.value},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["content"] == "After"
    assert body["status"] == DraftStatus.approved.value

    versions = client.get(f"/api/drafts/{draft.id}/versions").json()
    assert [version["reason"] for version in versions] == ["edited", "created"]
    assert versions[0]["content"] == "After"


def test_editing_published_draft_can_clear_linkedin_post_for_repost(client, test_store) -> None:
    draft = test_store.add_draft(title="Published", content="Before", source="research")
    test_store.update_draft_status(
        draft.id,
        status=DraftStatus.published,
        linkedin_post_url="https://www.linkedin.com/feed/update/urn:li:share:1",
    )

    response = client.patch(
        f"/api/drafts/{draft.id}",
        json={"content": "After small edit", "clear_linkedin_post": True},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["content"] == "After small edit"
    assert body["status"] == DraftStatus.approved.value
    assert body["linkedin_post_url"] is None
    assert body["posted_at"] is None


def test_regenerate_draft_updates_same_draft_and_adds_version(client, monkeypatch, test_store) -> None:
    topic = test_store.create_topic("LangGraph", TopicStatus.complete)
    assistant = test_store.add_message(topic.id, MessageRole.assistant, "LangGraph helps teams build agent workflows.")
    draft = test_store.add_draft(
        title="LangGraph draft",
        content="Old draft",
        source="research",
        topic_id=topic.id,
        source_message_id=assistant.id,
    )

    async def fake_regenerate(store, draft_id, **kwargs):
        assert store is test_store
        assert draft_id == draft.id
        assert kwargs["tone"].value == "casual"
        return store.update_draft(
            draft.id,
            content="New casual draft",
            status=DraftStatus.pending,
            version_reason="regenerated",
        )

    monkeypatch.setattr("app.routes.drafts.regenerate_draft_from_same_answer", fake_regenerate)

    response = client.post(
        f"/api/drafts/{draft.id}/regenerate",
        json={"tone": "casual", "length": "short", "include_cta": False, "include_hashtags": True},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == draft.id
    assert body["content"] == "New casual draft"
    versions = client.get(f"/api/drafts/{draft.id}/versions").json()
    assert [version["reason"] for version in versions] == ["regenerated", "created"]


def test_create_topic_draft_returns_handled_error_when_generation_times_out(client, monkeypatch, test_store) -> None:
    topic = test_store.create_topic("Timeout topic", TopicStatus.complete)
    test_store.add_message(topic.id, MessageRole.assistant, "Saved answer content")

    async def fake_create_draft_from_topic_response(*_args, **_kwargs):
        raise ValueError("Draft generation timed out. Please try again, or use a shorter answer / lighter draft settings.")

    monkeypatch.setattr(
        "app.routes.topics.create_draft_from_topic_response",
        fake_create_draft_from_topic_response,
    )

    response = client.post(f"/api/topics/{topic.id}/draft", json={})

    assert response.status_code == 400
    assert "timed out" in response.json()["detail"]
