from __future__ import annotations

import re
from datetime import datetime
from urllib.parse import urlparse

try:
    from rank_bm25 import BM25Okapi
except ImportError:  # pragma: no cover - dependency fallback
    BM25Okapi = None

try:
    from ..tools.web_search import canonical_source_url, source_domain
except ImportError:  # pragma: no cover - direct module execution fallback
    canonical_source_url = None
    source_domain = None

from ..content_selection.text import terms_for_text

AUTHORITATIVE_DOMAIN_HINTS = (
    "docs.",
    "developer.",
    "developers.",
    "learn.",
    "engineering.",
    "newsroom.",
    "press.",
    "investor.",
    "research.",
    "support.",
    "help.",
    ".org",
    ".edu",
    ".gov",
)

HIGH_VALUE_PATH_HINTS = (
    "/about",
    "/article",
    "/articles",
    "/blog",
    "/case-study",
    "/case-studies",
    "/changelog",
    "/company",
    "/docs",
    "/doc/",
    "/documentation",
    "/developer",
    "/developers",
    "/guide",
    "/guides",
    "/insights",
    "/learn",
    "/news",
    "/newsroom",
    "/press",
    "/reference",
    "/report",
    "/reports",
    "/research",
    "/resources",
    "/release",
    "/releases",
    "/think",
    "/topic",
    "/topics",
    "/whitepaper",
)

LOW_QUALITY_DOMAIN_HINTS = (
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "medium.com",
    "dev.to",
    "hashnode.dev",
    "reddit.com",
    "x.com",
    "twitter.com",
    "quora.com",
    "news.ycombinator.com",
    "geeksforgeeks.org",
    "tutorialspoint.com",
    "w3schools.com",
    "javatpoint.com",
    "simplilearn.com",
    "upgrad.com",
    "intellipaat.com",
    "knowledgehut.com",
    "hackr.io",
    "dictionary.com",
    "merriam-webster.com",
    "thesaurus.com",
)

BLOCKED_RANKING_DOMAIN_HINTS = (
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "reddit.com",
    "x.com",
    "twitter.com",
    "quora.com",
    "news.ycombinator.com",
)

THIN_CONTENT_TITLE_HINTS = (
    "top ",
    "best ",
    "ultimate guide",
    "complete guide",
    "what is ",
    "explained",
    "for beginners",
)

GENERIC_REFERENCE_TITLE_HINTS = (
    "definition & meaning",
    "definition and meaning",
    "dictionary",
    "thesaurus",
)

FRESHNESS_TERMS = {
    "latest",
    "recent",
    "released",
    "release",
    "new",
    "current",
    "today",
    "2026",
}


def rank_search_results(topic: str, results: list[dict[str, str]]) -> list[dict[str, str]]:
    topic_lower = " ".join(topic.lower().split())
    topic_terms = terms_for_text(topic_lower)
    latest_intent = bool(topic_terms & FRESHNESS_TERMS)
    current_year = datetime.now().year
    bm25_scores = _bm25_scores(topic, results)
    scored: list[tuple[float, int, dict[str, str]]] = []
    seen_urls: set[str] = set()
    for position, result in enumerate(results):
        raw_url = result.get("url", "").strip()
        url = canonical_source_url(raw_url) if canonical_source_url is not None else raw_url
        title = result.get("title", "").strip()
        snippet = result.get("snippet", "").strip()
        if not url or not title or url in seen_urls:
            continue
        seen_urls.add(url)

        parsed = urlparse(url)
        domain = source_domain(url) if source_domain is not None else parsed.netloc.lower().removeprefix("www.")
        path = parsed.path.lower()
        if any(domain == blocked or domain.endswith(f".{blocked}") for blocked in BLOCKED_RANKING_DOMAIN_HINTS):
            continue
        title_lower = title.lower()
        snippet_lower = snippet.lower()
        combined = f"{title_lower} {snippet_lower}"
        result = {**result, "url": url}
        score = float(bm25_scores.get(position, 0.0))

        matched_terms = [term for term in topic_terms if term in combined]
        score += len(matched_terms) * 3
        score += sum(3 for term in topic_terms if term in title_lower)
        if topic_lower and (topic_lower in title_lower or topic_lower in snippet_lower):
            score += 14
        if title_lower.startswith(tuple(topic_terms)) or any(title_lower.startswith(term) for term in topic_terms):
            score += 4

        domain_parts = set(re.split(r"[\W_]+", domain))
        domain_term_matches = len(topic_terms & domain_parts)
        score += domain_term_matches * 8
        if any(source_hint in domain for source_hint in AUTHORITATIVE_DOMAIN_HINTS):
            score += 5
        if any(term in domain for term in topic_terms):
            score += 4
        if any(term in combined for term in ("official", "source", "documentation", "newsroom", "press release")):
            score += 6

        if any(path_hint in path for path_hint in HIGH_VALUE_PATH_HINTS):
            score += 5
        if any(path_hint in path for path_hint in ("/release", "/releases", "/changelog")):
            score += 8

        if any(low_quality in domain for low_quality in LOW_QUALITY_DOMAIN_HINTS):
            score -= 18
        if any(hint in title_lower for hint in GENERIC_REFERENCE_TITLE_HINTS):
            score -= 16
        if not snippet:
            score -= 8
        elif len(snippet) < 70:
            score -= 3
        if any(hint in title_lower for hint in THIN_CONTENT_TITLE_HINTS):
            score -= 4
        if "/tag/" in path or "/category/" in path or "/author/" in path:
            score -= 3

        years = [int(year) for year in re.findall(r"\b(20\d{2})\b", combined)]
        if latest_intent:
            if years:
                newest_year = max(years)
                if newest_year >= current_year - 1:
                    score += 7
                elif newest_year <= current_year - 3:
                    score -= 8
            if "what is" in title_lower and not any(hint in path for hint in ("/release", "/releases", "/changelog")):
                score -= 7
            if any(term in combined for term in ("latest", "new", "released", "release notes", "changelog")):
                score += 4

        scored.append((score, -position, result))

    scored.sort(key=lambda item: (item[0], item[1]), reverse=True)

    ranked: list[dict[str, str]] = []
    domain_counts: dict[str, int] = {}
    for _, _, result in scored:
        url = result.get("url", "")
        domain = source_domain(url) if source_domain is not None else urlparse(url).netloc.lower().removeprefix("www.")
        count = domain_counts.get(domain, 0)
        if count >= 2:
            continue
        ranked.append(result)
        domain_counts[domain] = count + 1
    return ranked


def _bm25_scores(topic: str, results: list[dict[str, str]]) -> dict[int, float]:
    if BM25Okapi is None:
        return {}
    corpus: list[list[str]] = []
    positions: list[int] = []
    for position, result in enumerate(results):
        text = f"{result.get('title', '')} {result.get('snippet', '')}"
        tokens = sorted(terms_for_text(text))
        if tokens:
            corpus.append(tokens)
            positions.append(position)
    query_tokens = sorted(terms_for_text(topic))
    if not corpus or not query_tokens:
        return {}
    bm25 = BM25Okapi(corpus)
    scores = bm25.get_scores(query_tokens)
    return {position: float(score) * 4 for position, score in zip(positions, scores)}


def build_search_query_variants(topic: str, primary_query: str, count: int) -> list[str]:
    candidates = [
        primary_query.strip(),
        topic.strip(),
    ]
    lowered = f"{topic} {primary_query}".lower()
    if any(term in lowered for term in ("latest", "recent", "released", "new", "current", "today")):
        candidates.extend(
            [
                f"{primary_query} official sources",
                f"{primary_query} latest news",
                f"{primary_query} recent articles",
            ]
        )
    else:
        candidates.extend(
            [
                f"{primary_query} official sources",
                f"{primary_query} articles",
                f"{primary_query} overview",
            ]
        )

    variants: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        normalized = " ".join(candidate.split())
        key = normalized.lower()
        if normalized and key not in seen:
            variants.append(normalized)
            seen.add(key)
        if len(variants) >= count:
            break
    return variants
