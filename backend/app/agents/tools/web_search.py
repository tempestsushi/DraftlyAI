from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

import requests
from requests import HTTPError

from ..text_cleaning import clean_source_text

try:
    from courlan import clean_url
except ImportError:  # pragma: no cover - dependency fallback
    clean_url = None

try:
    import tldextract
except ImportError:  # pragma: no cover - dependency fallback
    tldextract = None

BLOCKED_SOURCE_DOMAINS = {
    "facebook.com",
    "fb.com",
    "instagram.com",
    "linkedin.com",
    "lnkd.in",
    "reddit.com",
    "old.reddit.com",
    "x.com",
    "twitter.com",
    "youtube.com",
    "youtu.be",
    "vimeo.com",
    "dailymotion.com",
    "tiktok.com",
    "pinterest.com",
    "imgur.com",
    "flickr.com",
    "giphy.com",
    "quora.com",
    "stackoverflow.com",
    "stackexchange.com",
    "news.ycombinator.com",
    "discord.com",
    "discord.gg",
}

BLOCKED_SOURCE_EXTENSIONS = {
    ".apng",
    ".avi",
    ".bmp",
    ".gif",
    ".heic",
    ".jpeg",
    ".jpg",
    ".m4v",
    ".mov",
    ".mp4",
    ".mpeg",
    ".mpg",
    ".pdf",
    ".png",
    ".svg",
    ".tif",
    ".tiff",
    ".webm",
    ".webp",
    ".wmv",
}


@dataclass(slots=True)
class SearchResult:
    title: str
    url: str
    snippet: str

    def as_dict(self) -> dict[str, str]:
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
        }


def canonical_source_url(raw_url: str) -> str:
    url = raw_url.strip()
    if not url:
        return ""
    if clean_url is None:
        return url
    normalized = clean_url(url)
    return normalized or url


def source_domain(raw_url: str) -> str:
    parsed = urlparse(raw_url)
    domain = parsed.netloc.lower().removeprefix("www.")
    if tldextract is None or not domain:
        return domain
    extracted = tldextract.extract(raw_url)
    registered = ".".join(part for part in (extracted.domain, extracted.suffix) if part)
    return registered or domain


def is_text_source_url(raw_url: str) -> bool:
    url = canonical_source_url(raw_url)
    parsed = urlparse(url)
    domain = source_domain(url)
    path = parsed.path.lower()
    if not parsed.scheme.startswith("http") or not domain:
        return False
    if any(domain == blocked or domain.endswith(f".{blocked}") for blocked in BLOCKED_SOURCE_DOMAINS):
        return False
    if any(path.endswith(extension) for extension in BLOCKED_SOURCE_EXTENSIONS):
        return False
    return True


def _search_tavily(
    query: str,
    *,
    api_key: str,
    max_results: int = 5,
    search_depth: str = "basic",
) -> list[dict[str, str]]:
    response = requests.post(
        "https://api.tavily.com/search",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "query": query,
            "search_depth": search_depth,
            "max_results": min(max_results * 3, 20),
            "topic": "general",
            "include_answer": False,
            "include_raw_content": False,
            "include_images": False,
            "include_image_descriptions": False,
            "include_favicon": False,
            "auto_parameters": False,
        },
        timeout=30,
    )
    try:
        response.raise_for_status()
    except HTTPError as exc:
        detail = response.text[:500]
        raise HTTPError(f"Tavily search failed with {response.status_code}: {detail}") from exc
    payload = response.json()

    results: list[dict[str, str]] = []
    seen_urls: set[str] = set()
    for item in payload.get("results", []):
        url = canonical_source_url(str(item.get("url", "")).strip())
        title = str(item.get("title", "")).strip()
        snippet = clean_source_text(str(item.get("content", "")).strip())
        if not url or not title or not is_text_source_url(url) or url in seen_urls:
            continue
        results.append(SearchResult(title=title, url=url, snippet=snippet).as_dict())
        seen_urls.add(url)
        if len(results) >= max_results:
            break
    return results


def search_web(
    query: str,
    *,
    max_results: int = 5,
    tavily_api_key: str | None = None,
    tavily_search_depth: str = "basic",
) -> list[dict[str, str]]:
    if not tavily_api_key:
        raise ValueError("TAVILY_API_KEY is required for web search")
    return _search_tavily(
        query,
        api_key=tavily_api_key,
        max_results=max_results,
        search_depth=tavily_search_depth,
    )
