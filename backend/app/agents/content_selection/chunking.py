from __future__ import annotations

from .models import PipelineConfig, SourceChunk
from .text import estimate_tokens, lexical_similarity, sentence_split, terms_for_text


def chunk_sources(topic: str, sources: list[dict[str, str]], config: PipelineConfig) -> list[SourceChunk]:
    chunks: list[SourceChunk] = []
    for source_index, source in enumerate(sources, start=1):
        source_id = source.get("source_id") or f"source_{source_index}"
        title = source.get("title") or source.get("url") or f"Source {source_index}"
        url = source.get("url", "")
        text = " ".join(
            part.strip()
            for part in [source.get("snippet", ""), source.get("content", "")]
            if part and part.strip()
        )
        sentences = sentence_split(text)
        if not sentences and text.strip():
            sentences = [text.strip()]

        chunk_sentences: list[str] = []
        chunk_index = 1
        for sentence in sentences:
            candidate = " ".join([*chunk_sentences, sentence]).strip()
            if chunk_sentences and estimate_tokens(candidate) > config.target_chunk_tokens:
                chunks.append(_make_chunk(source_id, title, url, chunk_index, chunk_sentences))
                chunk_index += 1
                overlap = chunk_sentences[-config.chunk_overlap_sentences :] if config.chunk_overlap_sentences else []
                chunk_sentences = [*overlap, sentence]
            else:
                chunk_sentences.append(sentence)

        if chunk_sentences:
            chunks.append(_make_chunk(source_id, title, url, chunk_index, chunk_sentences))

    topic_terms = terms_for_text(topic)
    return [
        chunk
        for chunk in chunks
        if chunk.token_count >= 12 and lexical_similarity(topic_terms, chunk.terms) >= 0.02
    ]


def _make_chunk(
    source_id: str,
    title: str,
    url: str,
    chunk_index: int,
    sentences: list[str],
) -> SourceChunk:
    text = " ".join(sentences).strip()
    return SourceChunk(
        chunk_id=f"{source_id}_chunk_{chunk_index}",
        source_id=source_id,
        source_title=title,
        source_url=url,
        text=text,
        token_count=estimate_tokens(text),
        terms=terms_for_text(f"{title} {text}"),
    )
