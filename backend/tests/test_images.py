from __future__ import annotations

from app.models import TopicStatus


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self.payload


def test_image_generate_endpoint_maps_gemini_image_result(client, monkeypatch) -> None:
    import app.services.images.generate as image_generate
    captured = {}

    def fake_post(*_args, **kwargs):
        captured["url"] = _args[0]
        captured["headers"] = kwargs["headers"]
        captured["json"] = kwargs["json"]
        return FakeResponse({"output_image": {"data": "gemini-base64"}})

    monkeypatch.setattr(image_generate.settings, "gemini_api_key", "chat-key")
    monkeypatch.setattr(image_generate.settings, "gemini_image_api_key", "image-key")
    monkeypatch.setattr(image_generate.settings, "image_generation_provider", "gemini")
    monkeypatch.setattr(image_generate.settings, "gemini_image_model", "gemini-3.1-flash-image")
    monkeypatch.setattr(image_generate.requests, "post", fake_post)

    response = client.post(
        "/api/images/generate",
        json={
            "prompt": "how a text prompt creates an image through processing with AI models",
            "use_case": "technical_concept",
        },
    )

    assert response.status_code == 200, response.json()
    body = response.json()
    assert len(body) == 1
    assert body[0]["provider"] == "gemini-image"
    assert body[0]["source_domain"] == "ai.google.dev"
    assert body[0]["image_url"].endswith("gemini-base64")
    assert captured["url"].endswith("/v1beta/interactions")
    assert captured["headers"]["x-goog-api-key"] == "image-key"
    assert captured["json"]["model"] == "gemini-3.1-flash-image"
    assert captured["json"]["input"]
    assert captured["json"]["response_format"]["type"] == "image"
    assert captured["json"]["response_format"]["aspect_ratio"] == "16:9"


def test_image_generate_endpoint_maps_openrouter_image_result(client, monkeypatch) -> None:
    import app.services.images.generate as image_generate
    captured = {}

    def fake_post(*_args, **kwargs):
        captured["url"] = _args[0]
        captured["headers"] = kwargs["headers"]
        captured["json"] = kwargs["json"]
        return FakeResponse({"data": [{"b64_json": "openrouter-base64", "media_type": "image/png"}]})

    monkeypatch.setattr(image_generate.settings, "image_generation_provider", "openrouter")
    monkeypatch.setattr(image_generate.settings, "openrouter_api_key", "openrouter-key")
    monkeypatch.setattr(image_generate.settings, "openrouter_image_model", "openai/gpt-image-test")
    monkeypatch.setattr(image_generate.settings, "openrouter_image_size", "")
    monkeypatch.setattr(image_generate.settings, "openrouter_image_aspect_ratio", "")
    monkeypatch.setattr(image_generate.requests, "post", fake_post)

    response = client.post(
        "/api/images/generate",
        json={
            "prompt": "a clean AI image pipeline illustration",
            "use_case": "technical_concept",
        },
    )

    assert response.status_code == 200, response.json()
    body = response.json()
    assert body[0]["provider"] == "openrouter-image"
    assert body[0]["source_domain"] == "openrouter.ai"
    assert body[0]["image_url"].endswith("openrouter-base64")
    assert captured["url"].endswith("/api/v1/images")
    assert captured["headers"]["Authorization"] == "Bearer openrouter-key"
    assert captured["json"]["model"] == "openai/gpt-image-test"
    assert captured["json"]["prompt"]


def test_image_generation_prompt_uses_text_to_image_visual_pipeline() -> None:
    from app.models import ImageUseCase
    from app.services.images.generate import _build_generation_prompt

    prompt = _build_generation_prompt(
        "create an illustration of how a text prompt creates an image through processing with AI models",
        ImageUseCase.technical_concept,
    ).lower()

    assert "text prompt becoming an image" in prompt
    assert "token blocks" in prompt
    assert "denoising stages" in prompt
    assert "do not render words" in prompt


def test_save_list_and_delete_multiple_draft_images(client, test_store) -> None:
    topic = test_store.create_topic("Tokenization", TopicStatus.complete)
    draft = test_store.add_draft(
        title="Tokenization draft",
        content="Draft content",
        source="research",
        topic_id=topic.id,
    )
    payload_a = {
        "title": "Tokenization diagram",
        "image_url": "https://assets.example.com/tokenization.jpg",
        "thumbnail_url": "https://assets.example.com/tokenization-thumb.jpg",
        "source_url": "https://example.com/article/tokenization",
        "source_domain": "example.com",
        "provider": "gemini-image",
        "width": 1400,
        "height": 800,
    }
    payload_b = {
        **payload_a,
        "title": "Embedding diagram",
        "image_url": "https://assets.example.com/embedding.jpg",
        "thumbnail_url": "https://assets.example.com/embedding-thumb.jpg",
    }

    save_response = client.post(f"/api/drafts/{draft.id}/images", json=payload_a)
    assert save_response.status_code == 200
    assert save_response.json()["draft_id"] == draft.id
    assert save_response.json()["topic_id"] == topic.id
    second_response = client.post(f"/api/drafts/{draft.id}/images", json=payload_b)
    duplicate_response = client.post(f"/api/drafts/{draft.id}/images", json=payload_a)

    assert second_response.status_code == 200
    assert duplicate_response.status_code == 200
    images = client.get(f"/api/drafts/{draft.id}/images").json()
    assert [image["image_url"] for image in images] == [
        payload_a["image_url"],
        payload_b["image_url"],
    ]
    assert client.get(f"/api/drafts/{draft.id}/image").json()["image_url"] == payload_a["image_url"]

    delete_response = client.delete(f"/api/drafts/{draft.id}/images/{images[0]['id']}")
    assert delete_response.status_code == 200
    assert delete_response.json() == {"deleted": True}
    remaining = client.get(f"/api/drafts/{draft.id}/images").json()
    assert [image["image_url"] for image in remaining] == [payload_b["image_url"]]

    delete_all_response = client.delete(f"/api/drafts/{draft.id}/image")
    assert delete_all_response.status_code == 200
    assert client.get(f"/api/drafts/{draft.id}/images").json() == []
