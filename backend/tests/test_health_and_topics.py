from __future__ import annotations

from app.models import MessageRole, TopicStatus


def test_health_returns_service_metadata(client) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert "service" in body
    assert "model" in body


def test_topics_and_messages_round_trip(client, test_store) -> None:
    topic = test_store.create_topic("Test CI/CD topic", TopicStatus.pending)
    test_store.add_message(topic.id, MessageRole.user, "Tell me about CI/CD.")
    test_store.add_message(topic.id, MessageRole.assistant, "CI/CD helps teams ship safely.")

    topics_response = client.get("/api/topics")
    assert topics_response.status_code == 200
    topics = topics_response.json()
    assert any(item["id"] == topic.id for item in topics)

    topic_response = client.get(f"/api/topics/{topic.id}")
    assert topic_response.status_code == 200
    assert topic_response.json()["topic"] == "Test CI/CD topic"

    messages_response = client.get(f"/api/topics/{topic.id}/messages")
    assert messages_response.status_code == 200
    messages = messages_response.json()
    assert [message["role"] for message in messages] == ["user", "assistant"]


def test_user_prompt_can_be_edited(client, test_store) -> None:
    topic = test_store.create_topic("Editable topic", TopicStatus.pending)
    message = test_store.add_message(topic.id, MessageRole.user, "Original prompt")

    response = client.patch(
        f"/api/topics/{topic.id}/messages/{message.id}",
        json={"content": "Updated prompt"},
    )

    assert response.status_code == 200
    assert response.json()["content"] == "Updated prompt"
    assert test_store.list_messages(topic.id)[0].content == "Updated prompt"


def test_assistant_message_cannot_be_edited_as_prompt(client, test_store) -> None:
    topic = test_store.create_topic("Editable topic", TopicStatus.pending)
    message = test_store.add_message(topic.id, MessageRole.assistant, "Assistant answer")

    response = client.patch(
        f"/api/topics/{topic.id}/messages/{message.id}",
        json={"content": "Updated prompt"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Only user prompts can be edited"


def test_delete_topic_removes_topic_and_children(client, test_store) -> None:
    topic = test_store.create_topic("Delete me", TopicStatus.pending)
    test_store.add_message(topic.id, MessageRole.user, "temporary")
    test_store.add_draft(title="Temp draft", content="Draft body", source="research", topic_id=topic.id)

    response = client.delete(f"/api/topics/{topic.id}")

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert test_store.get_topic(topic.id) is None
    assert test_store.list_messages(topic.id) == []
