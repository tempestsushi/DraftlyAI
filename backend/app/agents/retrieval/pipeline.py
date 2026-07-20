from __future__ import annotations

from collections import Counter

from rapidfuzz import fuzz

try:
    from rank_bm25 import BM25Okapi
except ImportError:  # pragma: no cover - dependency fallback
    BM25Okapi = None

from ..content_selection.text import lexical_similarity, terms_for_text
from .chunking import chunk_sources
from .embeddings import cosine_similarity, embed_with_ollama
from .models import RagChunk, RagConfig, RagContext


class RagPipeline:
    def __init__(self, config: RagConfig) -> None:
        self.config = config

    def process(self, topic: str, sources: list[dict[str, str]]) -> RagContext:
        chunks = chunk_sources(
            sources,
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
        )
        selected = self._retrieve(topic, chunks)
        total_chars = sum(min(len(chunk.text), self.config.source_char_limit) for chunk in selected)
        return RagContext(
            topic=topic,
            selected_chunks=selected,
            total_source_chars=total_chars,
            debug_metrics=self._debug_metrics(chunks, selected),
        )

    def _retrieve(self, topic: str, chunks: list[RagChunk]) -> list[RagChunk]:
        if not chunks:
            return []
        topic_terms = terms_for_text(topic)
        bm25_scores = _bm25_scores(topic_terms, chunks)
        embedding_scores, embedding_error = self._embedding_scores(topic, chunks)
        scored: list[RagChunk] = []
        for index, chunk in enumerate(chunks):
            chunk.bm25_score = bm25_scores.get(index, 0.0)
            chunk.lexical_score = lexical_similarity(topic_terms, chunk.terms)
            chunk.title_score = lexical_similarity(topic_terms, terms_for_text(chunk.source_title))
            chunk.embedding_score = embedding_scores.get(index, 0.0)
            if embedding_scores:
                chunk.score = (
                    chunk.embedding_score * 4.0
                    + chunk.bm25_score * 0.6
                    + chunk.lexical_score * 1.4
                    + chunk.title_score * 0.5
                )
            else:
                chunk.score = chunk.bm25_score + (chunk.lexical_score * 2.5) + (chunk.title_score * 0.8)
            scored.append(chunk)

        scored.sort(key=lambda item: item.score, reverse=True)
        selected: list[RagChunk] = []
        seen_text_keys: set[str] = set()
        seen_texts: list[str] = []
        source_counts: Counter[str] = Counter()
        for chunk in scored:
            normalized_text = " ".join(chunk.text.lower().split())
            key = normalized_text[:220]
            if key in seen_text_keys:
                continue
            if _is_near_duplicate(normalized_text, seen_texts):
                continue
            if source_counts[chunk.source_id] >= 1 and len(source_counts) < max(2, len(set(item.source_id for item in chunks))):
                continue
            selected.append(chunk)
            seen_text_keys.add(key)
            seen_texts.append(normalized_text[:700])
            source_counts[chunk.source_id] += 1
            if len(selected) >= self.config.top_k:
                break
        self._last_embedding_error = embedding_error
        self._last_embedding_used = bool(embedding_scores)
        return selected

    def _debug_metrics(self, chunks: list[RagChunk], selected: list[RagChunk]) -> dict[str, str | int | float]:
        top_scores = ", ".join(f"{chunk.score:.2f}" for chunk in selected[:5]) or "none"
        top_embedding_scores = ", ".join(f"{chunk.embedding_score:.2f}" for chunk in selected[:5]) or "none"
        coverage = Counter(chunk.source_id for chunk in selected)
        return {
            "rag_enabled": 1,
            "rag_provider": self.config.provider,
            "rag_embed_model": self.config.embed_model,
            "rag_retrieval_mode": "embedding" if getattr(self, "_last_embedding_used", False) else "lexical_fallback",
            "rag_embedding_error": getattr(self, "_last_embedding_error", ""),
            "rag_top_k": self.config.top_k,
            "rag_chunk_size": self.config.chunk_size,
            "rag_chunk_overlap": self.config.chunk_overlap,
            "rag_source_char_limit": self.config.source_char_limit,
            "rag_candidate_chunks": len(chunks),
            "rag_selected_chunks": len(selected),
            "rag_selected_chars": sum(min(len(chunk.text), self.config.source_char_limit) for chunk in selected),
            "rag_top_scores": top_scores,
            "rag_top_embedding_scores": top_embedding_scores,
            "rag_source_coverage": ", ".join(f"{source}:{count}" for source, count in sorted(coverage.items())) or "none",
        }

    def _embedding_scores(self, topic: str, chunks: list[RagChunk]) -> tuple[dict[int, float], str]:
        if self.config.provider != "ollama" or not self.config.embed_model:
            return {}, ""
        try:
            embeddings = embed_with_ollama(
                [topic, *[chunk.text for chunk in chunks]],
                base_url=self.config.ollama_base_url,
                model=self.config.embed_model,
                timeout_seconds=self.config.embedding_timeout_seconds,
            )
        except Exception as exc:  # pragma: no cover - network dependent fallback
            return {}, str(exc)[:240]
        if len(embeddings) != len(chunks) + 1:
            return {}, "Ollama returned an unexpected number of embeddings"
        query_embedding = embeddings[0]
        return {
            index: cosine_similarity(query_embedding, embedding)
            for index, embedding in enumerate(embeddings[1:])
        }, ""


def build_rag_source_context(topic: str, sources: list[dict[str, str]], config: RagConfig) -> RagContext:
    return RagPipeline(config).process(topic, sources)


def format_rag_context(
    context: RagContext,
    *,
    source_char_limit: int,
    include_scores: bool = False,
    include_urls: bool = False,
) -> str:
    if not context.selected_chunks:
        return f"Evidence for: {context.topic}\nNo relevant RAG chunks were selected."

    lines = [f"Evidence for: {context.topic}", ""]
    for index, chunk in enumerate(context.selected_chunks, start=1):
        text = " ".join(chunk.text.split())[:source_char_limit].rstrip()
        lines.extend(
            [
                f"{index}. {chunk.source_title}",
            ]
        )
        if include_urls:
            lines.append(f"   URL: {chunk.source_url}")
        if include_scores:
            lines.append(
                "   Scores: "
                f"total={chunk.score:.2f}, embedding={chunk.embedding_score:.2f}, "
                f"bm25={chunk.bm25_score:.2f}, lexical={chunk.lexical_score:.2f}"
            )
        lines.append(f"   Evidence: {text}")
    return "\n".join(lines).strip()


def _bm25_scores(topic_terms: set[str], chunks: list[RagChunk]) -> dict[int, float]:
    if BM25Okapi is None or not topic_terms:
        return {}
    corpus = [sorted(chunk.terms) for chunk in chunks]
    if not any(corpus):
        return {}
    bm25 = BM25Okapi(corpus)
    scores = bm25.get_scores(sorted(topic_terms))
    return {index: float(score) for index, score in enumerate(scores)}


def _is_near_duplicate(text: str, selected_texts: list[str]) -> bool:
    return any(fuzz.token_set_ratio(text[:700], selected) >= 86 for selected in selected_texts)
