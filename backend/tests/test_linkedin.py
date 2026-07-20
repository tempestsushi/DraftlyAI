from __future__ import annotations

import requests

from app.models import DraftStatus, LinkedInAccountRecord, LogSource, TopicStatus


def test_callback_with_expired_state_returns_connected_when_account_exists(client, test_store) -> None:
    test_store.save_linkedin_account(
        LinkedInAccountRecord(
            provider_user_id="person-1",
            name="Test User",
            access_token="token",
        )
    )

    response = client.get("/api/linkedin/callback?code=old-code&state=missing-state")

    assert response.status_code == 200
    assert "/settings?linkedin=connected" in response.text
    assert "invalid or expired" not in response.text


def test_callback_with_expired_state_returns_error_when_no_account_exists(client) -> None:
    response = client.get("/api/linkedin/callback?code=old-code&state=missing-state")

    assert response.status_code == 200
    assert "linkedin=error" in response.text
    assert "invalid+or+expired" in response.text


def test_publish_uses_saved_draft_content_instead_of_payload(client, test_store, monkeypatch) -> None:
    topic = test_store.create_topic("KanbanKaii post", TopicStatus.review)
    saved_content = (
        "I built KanbanKaii to bridge personal productivity and team collaboration.\n\n"
        "The platform includes a private My Tasks board, shared workspaces, AI message validation, "
        "and Supabase-powered real-time updates."
    )
    draft = test_store.add_draft(
        title="KanbanKaii launch",
        content=saved_content,
        source="research",
        topic_id=topic.id,
    )
    test_store.update_draft_status(draft.id, status=DraftStatus.approved)
    test_store.save_linkedin_account(
        LinkedInAccountRecord(
            provider_user_id="person-1",
            name="Test User",
            access_token="token",
        )
    )
    captured: dict[str, str] = {}

    def fake_create_post(account, content: str) -> str:
        captured["content"] = content
        return "urn:li:share:123"

    monkeypatch.setattr("app.services.linkedin._create_linkedin_post", fake_create_post)

    response = client.post(
        "/api/linkedin/publish",
        json={"draft_id": draft.id, "content": "cut frontend payload"},
    )

    assert response.status_code == 200
    assert captured["content"] == saved_content
    updated = test_store.get_draft(draft.id)
    assert updated is not None
    assert updated.status == DraftStatus.published
    assert updated.linkedin_post_url == "https://www.linkedin.com/feed/update/urn:li:share:123"
    log_messages = [log.message for log in test_store.logs.values() if log.source == LogSource.linkedin]
    assert any(f"Publishing saved draft to LinkedIn ({len(saved_content)} chars" in message for message in log_messages)
    assert any("Ending preview:" in message and "Supabase-powered real-time updates." in message for message in log_messages)


def test_publish_rejects_empty_saved_draft(client, test_store) -> None:
    draft = test_store.add_draft(title="Empty", content="   ", source="research")
    test_store.save_linkedin_account(
        LinkedInAccountRecord(
            provider_user_id="person-1",
            name="Test User",
            access_token="token",
        )
    )

    response = client.post("/api/linkedin/publish", json={"draft_id": draft.id})

    assert response.status_code == 400
    assert "Draft content is empty" in response.json()["detail"]


def test_publish_appends_public_draft_attachment_links(client, test_store, monkeypatch) -> None:
    draft = test_store.add_draft(
        title="Image post",
        content="Here is the post body.",
        source="research",
    )
    test_store.save_draft_image(
        draft_id=draft.id,
        topic_id=None,
        title="Public image",
        image_url="https://cdn.example.com/image.png",
        thumbnail_url=None,
        source_url="https://example.com/article",
        source_domain="example.com",
        provider="test",
        width=None,
        height=None,
    )
    test_store.save_linkedin_account(
        LinkedInAccountRecord(
            provider_user_id="person-1",
            name="Test User",
            access_token="token",
        )
    )
    captured: dict[str, str] = {}

    def fake_create_post(account, content: str) -> str:
        captured["content"] = content
        return "urn:li:share:456"

    monkeypatch.setattr("app.services.linkedin._create_linkedin_post", fake_create_post)

    response = client.post("/api/linkedin/publish", json={"draft_id": draft.id})

    assert response.status_code == 200
    assert captured["content"] == "Here is the post body.\n\nAttached link:\nhttps://cdn.example.com/image.png"


def test_publish_skips_generated_non_public_attachment_links(client, test_store, monkeypatch) -> None:
    draft = test_store.add_draft(
        title="Generated image post",
        content="Here is the post body.",
        source="research",
    )
    test_store.save_draft_image(
        draft_id=draft.id,
        topic_id=None,
        title="Generated image",
        image_url="data:image/png;charset=utf-8;base64,abc123",
        thumbnail_url=None,
        source_url="https://ai.google.dev/gemini-api/docs/image-generation",
        source_domain="ai.google.dev",
        provider="gemini-image",
        width=None,
        height=None,
    )
    test_store.save_linkedin_account(
        LinkedInAccountRecord(
            provider_user_id="person-1",
            name="Test User",
            access_token="token",
        )
    )
    captured: dict[str, str] = {}

    def fake_create_post(account, content: str) -> str:
        captured["content"] = content
        return "urn:li:share:789"

    monkeypatch.setattr("app.services.linkedin._create_linkedin_post", fake_create_post)

    response = client.post("/api/linkedin/publish", json={"draft_id": draft.id})

    assert response.status_code == 200
    assert captured["content"] == "Here is the post body."
    log_messages = [log.message for log in test_store.logs.values() if log.source == LogSource.linkedin]
    assert any("skipped non-public/generated attachment links: 1" in message for message in log_messages)


def test_publish_normalizes_markdown_links_without_article_preview(client, test_store, monkeypatch) -> None:
    draft = test_store.add_draft(
        title="KanbanKaii",
        content=(
            "You can check out the repository at "
            "[**https://github.com/tempestsushi/KanbanKaii**](https://github.com/tempestsushi/KanbanKaii).\n"
            "The project is deployed on [**https://kanban-kaii.vercel.app**](https://kanban-kaii.vercel.app)."
        ),
        source="research",
    )
    test_store.save_linkedin_account(
        LinkedInAccountRecord(
            provider_user_id="person-1",
            name="Test User",
            access_token="token",
        )
    )
    captured: dict[str, str] = {}

    def fake_create_post(account, content: str) -> str:
        captured["content"] = content
        return "urn:li:share:999"

    monkeypatch.setattr("app.services.linkedin._create_linkedin_post", fake_create_post)

    response = client.post("/api/linkedin/publish", json={"draft_id": draft.id})

    assert response.status_code == 200
    assert captured["content"] == (
        "You can check out the repository at https://github.com/tempestsushi/KanbanKaii.\n"
        "The project is deployed on https://kanban-kaii.vercel.app."
    )


def test_publish_can_request_article_preview_without_title(client, test_store, monkeypatch) -> None:
    monkeypatch.setattr("app.services.linkedin.settings.linkedin_article_preview_enabled", True)
    draft = test_store.add_draft(
        title="KanbanKaii",
        content="Project: https://kanban-kaii.vercel.app",
        source="research",
    )
    test_store.save_linkedin_account(
        LinkedInAccountRecord(
            provider_user_id="person-1",
            name="Test User",
            access_token="token",
        )
    )
    captured: dict[str, str | None] = {}

    def fake_create_post(account, content: str, *, preview_url=None) -> str:
        captured["content"] = content
        captured["preview_url"] = preview_url
        return "urn:li:share:1000"

    monkeypatch.setattr("app.services.linkedin._create_linkedin_post", fake_create_post)

    response = client.post("/api/linkedin/publish", json={"draft_id": draft.id})

    assert response.status_code == 200
    assert captured["content"] == "Project: https://kanban-kaii.vercel.app"
    assert captured["preview_url"] == "https://kanban-kaii.vercel.app"


def test_publish_falls_back_to_text_only_when_article_preview_fails(client, test_store, monkeypatch) -> None:
    monkeypatch.setattr("app.services.linkedin.settings.linkedin_article_preview_enabled", True)
    draft = test_store.add_draft(
        title="KanbanKaii",
        content="Project: https://kanban-kaii.vercel.app",
        source="research",
    )
    test_store.save_linkedin_account(
        LinkedInAccountRecord(
            provider_user_id="person-1",
            name="Test User",
            access_token="token",
        )
    )
    calls: list[str | None] = []

    def fake_create_post(account, content: str, *, preview_url=None) -> str:
        calls.append(preview_url)
        if preview_url:
            response = requests.Response()
            response.status_code = 400
            raise requests.HTTPError(response=response)
        return "urn:li:share:1001"

    monkeypatch.setattr("app.services.linkedin._create_linkedin_post", fake_create_post)

    response = client.post("/api/linkedin/publish", json={"draft_id": draft.id})

    assert response.status_code == 200
    assert calls == ["https://kanban-kaii.vercel.app", None]
    log_messages = [log.message for log in test_store.logs.values() if log.source == LogSource.linkedin]
    assert any("LinkedIn article preview failed (400); retrying text-only post" in message for message in log_messages)
