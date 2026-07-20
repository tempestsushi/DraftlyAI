from __future__ import annotations

import re
from html import unescape

import requests
from bs4 import BeautifulSoup

from ..text_cleaning import clean_source_text

try:
    import trafilatura
except ImportError:  # pragma: no cover - dependency fallback
    trafilatura = None

TEXT_CONTENT_TYPES = (
    "text/html",
    "application/xhtml+xml",
    "text/plain",
    "text/markdown",
    "application/json",
)


def fetch_source_content(
    url: str,
    *,
    user_agent: str,
    char_limit: int = 4000,
    timeout_seconds: float = 12,
    max_bytes: int = 1_500_000,
) -> dict[str, str]:
    response = requests.get(
        url,
        headers={"User-Agent": user_agent},
        timeout=timeout_seconds,
        stream=True,
    )
    response.raise_for_status()
    content_type = response.headers.get("Content-Type", "").lower()
    if content_type and not any(allowed in content_type for allowed in TEXT_CONTENT_TYPES):
        raise ValueError(f"Unsupported source content type: {content_type}")

    content_length = response.headers.get("Content-Length")
    if content_length:
        try:
            if int(content_length) > max_bytes:
                raise ValueError("Source page is too large to extract efficiently")
        except ValueError as exc:
            if "too large" in str(exc):
                raise

    chunks: list[bytes] = []
    total_bytes = 0
    for chunk in response.iter_content(chunk_size=65536):
        if not chunk:
            continue
        total_bytes += len(chunk)
        if total_bytes > max_bytes:
            raise ValueError("Source page exceeded extraction size limit")
        chunks.append(chunk)

    raw_text = b"".join(chunks).decode(response.encoding or "utf-8", errors="ignore")

    if "text/plain" in content_type or "text/markdown" in content_type or "application/json" in content_type:
        text = clean_source_text(raw_text)
        return {
            "url": url,
            "content": text[:char_limit],
        }

    library_text = _extract_with_trafilatura(raw_text, url=url)
    if _is_useful_extract(library_text):
        return {
            "url": url,
            "content": library_text[:char_limit],
        }

    soup = BeautifulSoup(raw_text, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "nav", "footer", "header", "form", "aside"]):
        tag.decompose()
    for tag in soup.find_all(
        attrs={
            "class": re.compile(
                r"(nav|navbar|menu|sidebar|side-bar|toc|table-of-contents|breadcrumb|footer|header|"
                r"cookie|subscribe|social|pagination|related|promo|announcement|devsite-sidebar|devsite-nav)",
                re.I,
            )
        }
    ):
        tag.decompose()
    for tag in soup.find_all(
        attrs={
            "id": re.compile(
                r"(nav|navbar|menu|sidebar|side-bar|toc|table-of-contents|breadcrumb|footer|header|"
                r"cookie|subscribe|social|pagination|related|promo|announcement)",
                re.I,
            )
        }
    ):
        tag.decompose()
    for tag in soup.find_all(attrs={"aria-label": re.compile(r"(breadcrumb|navigation|sidebar|table of contents)", re.I)}):
        tag.decompose()

    content_root = (
        soup.find("article")
        or soup.find("main")
        or soup.find(attrs={"role": "main"})
        or soup.find(attrs={"id": re.compile(r"(content|main|article|post|entry|markdown|body)", re.I)})
        or soup.find(attrs={"class": re.compile(r"(content|main|article|post|entry|markdown|prose|body)", re.I)})
        or soup.body
        or soup
    )
    parts: list[str] = []
    for element in content_root.find_all(["h1", "h2", "h3", "p", "li", "pre", "code"]):
        text = element.get_text(" ", strip=True)
        if text:
            parts.append(text)

    if len(parts) < 4:
        fallback_root = soup.find(attrs={"id": re.compile(r"(content|main|article)", re.I)}) or soup.find(
            attrs={"class": re.compile(r"(content|main|article|post|entry|markdown)", re.I)}
        )
        if fallback_root is not None:
            fallback_parts: list[str] = []
            for element in fallback_root.find_all(["div", "section", "p", "li", "h1", "h2", "h3"]):
                text = element.get_text(" ", strip=True)
                if text and len(text) > 40:
                    fallback_parts.append(text)
            if fallback_parts:
                parts = fallback_parts

    text = clean_source_text("\n".join(parts))
    if not text:
        meta_description = soup.find("meta", attrs={"name": "description"}) or soup.find(
            "meta", attrs={"property": "og:description"}
        )
        if meta_description is not None:
            text = clean_source_text(unescape(meta_description.get("content", "")).strip())
    if not text:
        title = soup.find("title")
        if title is not None:
            text = clean_source_text(title.get_text(" ", strip=True))
    return {
        "url": url,
        "content": text[:char_limit],
    }


def _extract_with_trafilatura(raw_text: str, *, url: str) -> str:
    if trafilatura is None:
        return ""
    extracted = trafilatura.extract(
        raw_text,
        url=url,
        include_comments=False,
        include_tables=False,
        no_fallback=False,
        favor_precision=True,
    )
    return clean_source_text(extracted or "")


def _is_useful_extract(text: str) -> bool:
    cleaned = " ".join(text.split())
    if len(cleaned) < 180:
        return False
    if len(cleaned.split()) < 30:
        return False
    return True
