from __future__ import annotations

from ..content_selection.text import sentence_split, terms_for_text
from .models import RagChunk


def chunk_sources(
    sources: list[dict[str, str]],
    *,
    chunk_size: int,
    chunk_overlap: int,
) -> list[RagChunk]:
    chunks: list[RagChunk] = []
    target = max(180, chunk_size)
    overlap = max(0, min(chunk_overlap, target // 2))

    for source_index, source in enumerate(sources, start=1):
        source_id = str(source.get("source_id") or f"source_{source_index}")
        title = source.get("title", "") or "Untitled source"
        url = source.get("url", "")
        text = " ".join(
            part.strip()
            for part in (source.get("snippet", ""), source.get("content", ""))
            if part and part.strip()
        )
        if not text:
            continue
        for chunk_index, chunk_text in enumerate(_split_text(text, target=target, overlap=overlap), start=1):
            chunks.append(
                RagChunk(
                    chunk_id=f"{source_id}_chunk_{chunk_index}",
                    source_id=source_id,
                    source_title=title,
                    source_url=url,
                    text=chunk_text,
                    terms=terms_for_text(f"{title} {chunk_text}"),
                )
            )
    return chunks


def _split_text(text: str, *, target: int, overlap: int) -> list[str]:
    sentences = sentence_split(text)
    if not sentences:
        cleaned = " ".join(text.split())
        return [cleaned[:target]] if cleaned else []

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for sentence in sentences:
        sentence_len = len(sentence)
        if current and current_len + sentence_len + 1 > target:
            chunks.append(" ".join(current).strip())
            carried = _overlap_tail(current, overlap)
            current = carried
            current_len = len(" ".join(current))
        current.append(sentence)
        current_len += sentence_len + 1
    if current:
        chunks.append(" ".join(current).strip())
    return [chunk for chunk in chunks if chunk]


def _overlap_tail(sentences: list[str], overlap: int) -> list[str]:
    if overlap <= 0:
        return []
    tail: list[str] = []
    total = 0
    for sentence in reversed(sentences):
        if total + len(sentence) > overlap and tail:
            break
        tail.insert(0, sentence)
        total += len(sentence)
    return tail
