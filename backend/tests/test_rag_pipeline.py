from app.agents.retrieval import RagConfig, build_rag_source_context, format_rag_context


def test_rag_pipeline_selects_relevant_chunks_from_extracted_pages() -> None:
    context = build_rag_source_context(
        "How does tokenization work inside an AI model?",
        [
            {
                "title": "Tokenization guide",
                "url": "https://example.com/tokenization",
                "snippet": "Tokenization splits text into tokens before model inference.",
                "content": (
                    "Tokenization breaks input text into smaller tokens such as words, subwords, or characters. "
                    "The tokenizer maps each token to an integer id that the model can process. "
                    "Unrelated deployment notes are not important here."
                ),
            },
            {
                "title": "Marketing glossary",
                "url": "https://example.com/marketing",
                "snippet": "Marketing teams plan campaigns.",
                "content": "Brand positioning and media planning help marketing teams organize campaigns.",
            },
        ],
        RagConfig(top_k=2, chunk_size=220, chunk_overlap=30, source_char_limit=180),
    )

    assert context.selected_chunks
    assert context.selected_chunks[0].source_title == "Tokenization guide"
    assert "token" in context.selected_chunks[0].text.lower()
    assert context.debug_metrics["rag_candidate_chunks"] >= 2
    assert context.debug_metrics["rag_selected_chunks"] <= 2


def test_rag_context_format_limits_source_text() -> None:
    context = build_rag_source_context(
        "What is quantization?",
        [
            {
                "title": "Quantization docs",
                "url": "https://example.com/quantization",
                "snippet": "Quantization reduces model precision.",
                "content": "Quantization reduces numerical precision so models need less memory and compute. " * 8,
            }
        ],
        RagConfig(top_k=1, chunk_size=500, chunk_overlap=20, source_char_limit=90),
    )

    formatted = format_rag_context(context, source_char_limit=90)

    assert "Evidence for:" in formatted
    assert "Quantization docs" in formatted
    evidence_line = next(line for line in formatted.splitlines() if "Evidence:" in line)
    assert len(evidence_line) < 120
