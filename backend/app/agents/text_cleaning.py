from __future__ import annotations

import re


JUNK_LINE_PATTERNS = (
    r"^skip to (main )?content$",
    r"^table of contents:?$",
    r"^on this page$",
    r"^was this helpful\??$",
    r"^send feedback$",
    r"^sign in$",
    r"^contact sales$",
    r"^get started$",
    r"^try for free$",
    r"^subscribe$",
    r"^share this",
    r"^cookie",
    r"^privacy policy$",
    r"^terms of service$",
    r"^(products|solutions|pricing|docs|documentation|resources|partners|support|console)$",
)

JUNK_PHRASE_PATTERNS = (
    r"\[skip to content\]\([^)]+\)",
    r"!\[[^\]]*\]\([^)]+\)",
    r"\[(products|solutions|pricing|docs|documentation|resources|support|console)\]\([^)]+\)",
)


def clean_source_text(text: str) -> str:
    text = _strip_markdown_noise(text)
    lines = []
    seen: set[str] = set()
    for raw_line in re.split(r"[\r\n]+|(?<=[.!?])\s{2,}", text):
        line = " ".join(raw_line.split()).strip()
        if not line or _is_junk_line(line):
            continue
        normalized = line.lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        lines.append(line)
    return re.sub(r"\s+", " ", " ".join(lines)).strip()


def _strip_markdown_noise(text: str) -> str:
    cleaned = text
    for pattern in JUNK_PHRASE_PATTERNS:
        cleaned = re.sub(pattern, " ", cleaned, flags=re.I)
    cleaned = re.sub(r"\s*[|•]\s*", " ", cleaned)
    return cleaned


def _is_junk_line(line: str) -> bool:
    lowered = line.lower().strip(" -:|")
    if len(lowered) <= 2:
        return True
    if any(re.search(pattern, lowered, flags=re.I) for pattern in JUNK_LINE_PATTERNS):
        return True
    link_count = lowered.count("http") + lowered.count("](")
    if link_count >= 3 and len(lowered) < 220:
        return True
    words = lowered.split()
    nav_words = {
        "products",
        "solutions",
        "pricing",
        "docs",
        "documentation",
        "resources",
        "support",
        "console",
        "partners",
    }
    if len(words) <= 12 and sum(1 for word in words if word.strip(",.") in nav_words) >= 3:
        return True
    return False
