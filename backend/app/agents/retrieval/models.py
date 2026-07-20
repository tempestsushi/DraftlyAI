from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class RagConfig:
    top_k: int = 4
    chunk_size: int = 600
    chunk_overlap: int = 80
    source_char_limit: int = 700
    provider: str = "local"
    embed_model: str = ""
    ollama_base_url: str = "http://127.0.0.1:11434"
    embedding_timeout_seconds: float = 8


@dataclass(slots=True)
class RagChunk:
    chunk_id: str
    source_id: str
    source_title: str
    source_url: str
    text: str
    score: float = 0
    embedding_score: float = 0
    lexical_score: float = 0
    bm25_score: float = 0
    title_score: float = 0
    terms: set[str] = field(default_factory=set)


@dataclass(slots=True)
class RagContext:
    topic: str
    selected_chunks: list[RagChunk]
    total_source_chars: int
    debug_metrics: dict[str, str | int | float] = field(default_factory=dict)
