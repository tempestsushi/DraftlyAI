from __future__ import annotations

from app.agents.tools.web_search import is_text_source_url, search_web
from app.agents.graph.ranking import rank_search_results


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self.payload


def test_tavily_search_maps_results(monkeypatch) -> None:
    captured = {}

    def fake_post(url, *, headers, json, timeout):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        captured["timeout"] = timeout
        return FakeResponse(
            {
                "results": [
                    {
                        "title": "Jenkins Documentation",
                        "url": "https://www.jenkins.io/doc/",
                        "content": "Jenkins helps automate CI/CD pipelines.",
                    }
                ]
            }
        )

    monkeypatch.setattr("app.agents.tools.web_search.requests.post", fake_post)

    results = search_web(
        "jenkins ci cd",
        max_results=1,
        tavily_api_key="tvly-test",
        tavily_search_depth="basic",
    )

    assert captured["url"] == "https://api.tavily.com/search"
    assert captured["headers"]["Authorization"] == "Bearer tvly-test"
    assert captured["json"]["query"] == "jenkins ci cd"
    assert captured["json"]["max_results"] == 3
    assert captured["json"]["search_depth"] == "basic"
    assert results == [
        {
            "title": "Jenkins Documentation",
            "url": "https://www.jenkins.io/doc/",
            "snippet": "Jenkins helps automate CI/CD pipelines.",
        }
    ]


def test_tavily_requires_api_key() -> None:
    try:
        search_web("jenkins")
    except ValueError as exc:
        assert "TAVILY_API_KEY" in str(exc)
    else:
        raise AssertionError("Expected missing Tavily API key to raise ValueError")


def test_text_source_filter_blocks_video_and_media_urls() -> None:
    assert not is_text_source_url("https://www.youtube.com/watch?v=abc123")
    assert not is_text_source_url("https://youtu.be/abc123")
    assert not is_text_source_url("https://www.reddit.com/r/OpenAI/comments/example")
    assert not is_text_source_url("https://www.linkedin.com/posts/example")
    assert not is_text_source_url("https://twitter.com/example/status/123")
    assert not is_text_source_url("https://www.facebook.com/example")
    assert not is_text_source_url("https://example.com/image.webp")
    assert not is_text_source_url("https://example.com/video.mp4")
    assert not is_text_source_url("https://example.com/report.pdf")
    assert is_text_source_url("https://docs.python.org/3/tutorial/index.html")


def test_tavily_search_skips_video_and_image_results(monkeypatch) -> None:
    def fake_post(url, *, headers, json, timeout):
        _ = url, headers, json, timeout
        return FakeResponse(
            {
                "results": [
                    {
                        "title": "Reddit discussion",
                        "url": "https://www.reddit.com/r/OpenAI/comments/example",
                        "content": "A forum discussion that should be filtered out.",
                    },
                    {
                        "title": "LinkedIn post",
                        "url": "https://www.linkedin.com/posts/example",
                        "content": "A social post that should be filtered out.",
                    },
                    {
                        "title": "Video result",
                        "url": "https://www.youtube.com/watch?v=abc123",
                        "content": "A video result that should be filtered out.",
                    },
                    {
                        "title": "Image result",
                        "url": "https://example.com/diagram.png",
                        "content": "An image result that should be filtered out.",
                    },
                    {
                        "title": "Text documentation",
                        "url": "https://example.com/docs/tutorial",
                        "content": "A text page that should be kept.",
                    },
                ]
            }
        )

    monkeypatch.setattr("app.agents.tools.web_search.requests.post", fake_post)

    results = search_web(
        "example topic",
        max_results=2,
        tavily_api_key="tvly-test",
        tavily_search_depth="basic",
    )

    assert results == [
        {
            "title": "Text documentation",
            "url": "https://example.com/docs/tutorial",
            "snippet": "A text page that should be kept.",
        }
    ]


def test_ranking_prefers_relevant_authoritative_sources_and_limits_duplicate_domains() -> None:
    results = [
        {
            "title": "Context Window Explained",
            "url": "https://thin.example.com/context-window",
            "snippet": "A short generic page.",
        },
        {
            "title": "What is a context window?",
            "url": "https://www.ibm.com/think/topics/context-window?utm_source=test",
            "snippet": "The context window is the amount of text, in tokens, that a large language model can process.",
        },
        {
            "title": "Another IBM duplicate",
            "url": "https://www.ibm.com/think/topics/context-window?utm_medium=duplicate",
            "snippet": "The context window is the amount of text a model can process.",
        },
        {
            "title": "Social discussion",
            "url": "https://www.reddit.com/r/example/comments/abc",
            "snippet": "Forum thread.",
        },
    ]

    ranked = rank_search_results("What is the context window in an LLM?", results)

    assert ranked[0]["url"].startswith("https://www.ibm.com/think/topics/context-window")
    assert all("reddit.com" not in result["url"] for result in ranked)
    assert sum(1 for result in ranked if "ibm.com" in result["url"]) == 1


def test_ranking_demotes_question_word_dictionary_results() -> None:
    results = [
        {
            "title": "WHAT Definition & Meaning",
            "url": "https://www.dictionary.com/browse/what",
            "snippet": "A dictionary definition page for the word what.",
        },
        {
            "title": "Anthropology's Impact on Marketing",
            "url": "https://www.thethomascollective.com/post/anthropology-impact-on-marketing",
            "snippet": "Anthropology helps marketers understand cultural meaning, audience behavior, and human-centered campaigns.",
        },
        {
            "title": "How Cultural Anthropology Can Inform Business Strategy",
            "url": "https://www.businessnewsdaily.com/10033-cultural-anthropology-social-science-business.html",
            "snippet": "Cultural anthropology can help businesses understand customer behavior, demographic response, and market strategy.",
        },
    ]

    ranked = rank_search_results(
        "What role does cultural anthropology play in predicting how a new demographic will respond to a traditional marketing message?",
        results,
    )

    assert "dictionary.com" not in ranked[0]["url"]
    assert ranked[-1]["url"] == "https://www.dictionary.com/browse/what"
