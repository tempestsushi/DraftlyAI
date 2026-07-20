from __future__ import annotations

from .models import PipelineConfig, SourceChunk
from .text import lexical_similarity, normalized_text_key


def cluster_duplicates(
    chunks: list[SourceChunk],
    config: PipelineConfig,
) -> tuple[list[SourceChunk], dict[str, list[str]], list[dict[str, str]]]:
    representatives: list[SourceChunk] = []
    support: dict[str, list[str]] = {}
    excluded: list[dict[str, str]] = []

    for chunk in chunks:
        duplicate_of = _find_duplicate(chunk, representatives, config)
        if duplicate_of is None:
            representatives.append(chunk)
            support[chunk.chunk_id] = [chunk.source_id]
            continue

        support.setdefault(duplicate_of.chunk_id, [duplicate_of.source_id])
        if chunk.source_id not in support[duplicate_of.chunk_id]:
            support[duplicate_of.chunk_id].append(chunk.source_id)
        excluded.append(
            {
                "chunk_id": chunk.chunk_id,
                "reason": "duplicate",
                "duplicate_of": duplicate_of.chunk_id,
            }
        )

    return representatives, {key: sorted(value) for key, value in support.items()}, excluded


def _find_duplicate(
    chunk: SourceChunk,
    representatives: list[SourceChunk],
    config: PipelineConfig,
) -> SourceChunk | None:
    chunk_key = normalized_text_key(chunk.text)
    for representative in representatives:
        if chunk_key == normalized_text_key(representative.text):
            return representative
        similarity = lexical_similarity(chunk.terms, representative.terms)
        if similarity >= config.duplicate_similarity_threshold:
            return representative
    return None
