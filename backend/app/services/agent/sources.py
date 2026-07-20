from __future__ import annotations

from urllib.parse import urlparse


def normalize_sources(
    fetched_sources: list[dict],
    search_results: list[dict],
) -> list[dict[str, str | None]]:
    normalized: list[dict[str, str | None]] = []
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()
    candidates = fetched_sources or search_results
    for item in candidates:
        url = str(item.get("url", "")).strip()
        title = str(item.get("title", "")).strip()
        normalized_title = " ".join(title.lower().split())
        if not url or not title or url in seen_urls or normalized_title in seen_titles:
            continue
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "") if parsed.netloc else None
        normalized.append(
            {
                "title": title,
                "url": url,
                "domain": domain,
                "snippet": str(item.get("snippet", "")).strip() or None,
            }
        )
        seen_urls.add(url)
        seen_titles.add(normalized_title)
        if len(normalized) >= 5:
            break
    return normalized
