from app.models import ResearchDepth
from app.services import rag_evaluation


def test_rag_evaluation_writes_backend_log(monkeypatch, tmp_path) -> None:
    log_path = tmp_path / "rag_eval.txt"

    monkeypatch.setattr(rag_evaluation.settings, "rag_evaluation_log_path", str(log_path))
    monkeypatch.setattr(rag_evaluation.settings, "rag_provider", "local")
    monkeypatch.setattr(rag_evaluation.settings, "tavily_api_key", None)

    def fake_search_web(*_args, **_kwargs):
        return [
            {
                "title": "Tokenization docs",
                "url": "https://example.com/tokenization",
                "snippet": "Tokenization splits text into tokens.",
            }
        ]

    def fake_fetch_source_content(*_args, **_kwargs):
        return {
            "content": (
                "Tokenization splits text into tokens. "
                "The tokenizer maps tokens to integer ids before model inference."
            )
        }

    monkeypatch.setattr(rag_evaluation, "search_web", fake_search_web)
    monkeypatch.setattr(rag_evaluation, "fetch_source_content", fake_fetch_source_content)

    result = rag_evaluation.run_rag_evaluation(
        "How does tokenization work inside an AI model?",
        ResearchDepth.moderate,
        include_responses=False,
    )

    assert result["ok"] is True
    assert result["candidate_sources"] == 1
    assert result["fetched_sources"] == 1
    assert log_path.exists()
    log_text = log_path.read_text(encoding="utf-8")
    assert "Extractive Pipeline" in log_text
    assert "RAG Pipeline" in log_text
    assert "RAG Selected Chunks" in log_text
    assert "Generated Responses" in log_text
    assert "skipped" in log_text
