from __future__ import annotations

import math

import requests


class EmbeddingError(RuntimeError):
    pass


def embed_with_ollama(
    texts: list[str],
    *,
    base_url: str,
    model: str,
    timeout_seconds: float,
) -> list[list[float]]:
    if not texts:
        return []
    endpoint = f"{base_url.rstrip('/')}/api/embed"
    response = requests.post(
        endpoint,
        json={"model": model, "input": texts},
        timeout=timeout_seconds,
    )
    if response.status_code == 404:
        return _embed_with_legacy_ollama(
            texts,
            base_url=base_url,
            model=model,
            timeout_seconds=timeout_seconds,
        )
    response.raise_for_status()
    payload = response.json()
    embeddings = payload.get("embeddings")
    if not isinstance(embeddings, list):
        raise EmbeddingError("Ollama embed response did not include embeddings")
    return [_coerce_embedding(item) for item in embeddings]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


def _embed_with_legacy_ollama(
    texts: list[str],
    *,
    base_url: str,
    model: str,
    timeout_seconds: float,
) -> list[list[float]]:
    endpoint = f"{base_url.rstrip('/')}/api/embeddings"
    embeddings: list[list[float]] = []
    for text in texts:
        response = requests.post(
            endpoint,
            json={"model": model, "prompt": text},
            timeout=timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        embedding = payload.get("embedding")
        if not isinstance(embedding, list):
            raise EmbeddingError("Ollama embeddings response did not include an embedding")
        embeddings.append(_coerce_embedding(embedding))
    return embeddings


def _coerce_embedding(value: object) -> list[float]:
    if not isinstance(value, list):
        raise EmbeddingError("Embedding value was not a list")
    return [float(item) for item in value]
