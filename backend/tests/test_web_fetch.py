from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.agents.tools.web_fetch import fetch_source_content


class FakeResponse:
    def __init__(self, body: str, *, headers: dict[str, str] | None = None):
        self.body = body.encode("utf-8")
        self.headers = headers or {"Content-Type": "text/html"}
        self.encoding = "utf-8"

    def raise_for_status(self) -> None:
        return None

    def iter_content(self, chunk_size: int):
        for index in range(0, len(self.body), chunk_size):
            yield self.body[index : index + chunk_size]


def test_fetch_source_content_extracts_article_text(monkeypatch) -> None:
    html = """
    <html>
      <body>
        <nav>Navigation junk</nav>
        <article>
          <h1>Python Async Guide</h1>
          <p>Asyncio helps Python applications handle concurrent IO-bound work efficiently.</p>
          <p>It is commonly used for web clients, servers, queues, and automation tasks.</p>
        </article>
      </body>
    </html>
    """

    def fake_get(*_args, **_kwargs):
        return FakeResponse(html)

    monkeypatch.setattr("app.agents.tools.web_fetch.requests.get", fake_get)

    result = fetch_source_content("https://example.com/article", user_agent="test-agent")

    assert "Python Async Guide" in result["content"]
    assert "Navigation junk" not in result["content"]
    assert "concurrent IO-bound work" in result["content"]


def test_fetch_source_content_removes_doc_navigation_and_sidebars(monkeypatch) -> None:
    html = """
    <html>
      <body>
        <div class="devsite-sidebar">Products Pricing Docs Console</div>
        <div class="breadcrumb">Home Docs AI</div>
        <main>
          <h1>Gemini Model Parameters</h1>
          <p>Gemini models support parameters such as temperature, topP, topK, and output token limits.</p>
          <p>The supported inputs can include text, images, audio, video, and documents depending on the model.</p>
        </main>
        <div id="footer">Privacy policy Terms of service</div>
      </body>
    </html>
    """

    def fake_get(*_args, **_kwargs):
        return FakeResponse(html)

    monkeypatch.setattr("app.agents.tools.web_fetch.requests.get", fake_get)

    result = fetch_source_content("https://example.com/docs", user_agent="test-agent")

    assert "Gemini Model Parameters" in result["content"]
    assert "temperature" in result["content"]
    assert "Products Pricing Docs Console" not in result["content"]
    assert "Privacy policy" not in result["content"]


def test_fetch_source_content_rejects_non_text_content(monkeypatch) -> None:
    def fake_get(*_args, **_kwargs):
        return FakeResponse("image-bytes", headers={"Content-Type": "image/png"})

    monkeypatch.setattr("app.agents.tools.web_fetch.requests.get", fake_get)

    with pytest.raises(ValueError, match="Unsupported source content type"):
        fetch_source_content("https://example.com/image.png", user_agent="test-agent")


def test_fetch_source_content_rejects_large_pages_from_header(monkeypatch) -> None:
    def fake_get(*_args, **_kwargs):
        return FakeResponse(
            "too large",
            headers={"Content-Type": "text/html", "Content-Length": "2000000"},
        )

    monkeypatch.setattr("app.agents.tools.web_fetch.requests.get", fake_get)

    with pytest.raises(ValueError, match="too large"):
        fetch_source_content("https://example.com/huge", user_agent="test-agent", max_bytes=1000)


def test_fetch_source_content_uses_library_extract_when_available(monkeypatch) -> None:
    html = """
    <html>
      <body>
        <nav>Products Pricing Documentation Console Support</nav>
        <main><p>Short fallback content.</p></main>
      </body>
    </html>
    """

    def fake_get(*_args, **_kwargs):
        return FakeResponse(html)

    def fake_extract(*_args, **_kwargs):
        return (
            "Context windows define how many tokens a model can consider at once. "
            "When a conversation exceeds that limit, older or less relevant content must be truncated, "
            "summarized, or otherwise compressed before the model receives the next prompt."
        )

    monkeypatch.setattr("app.agents.tools.web_fetch.requests.get", fake_get)
    monkeypatch.setattr("app.agents.tools.web_fetch.trafilatura", SimpleNamespace(extract=fake_extract))

    result = fetch_source_content("https://example.com/article", user_agent="test-agent")

    assert "Context windows define" in result["content"]
    assert "Products Pricing" not in result["content"]
