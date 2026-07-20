from app.agents.content_selection import ContentSelectionPipeline, PipelineConfig, format_selected_context
from app.agents.graph.helper import AgentGraph


def test_content_selection_dedupes_repeated_opening_and_preserves_support() -> None:
    pipeline = ContentSelectionPipeline(
        PipelineConfig(
            total_source_token_budget=220,
            duplicate_similarity_threshold=0.65,
            maximum_chunks_per_source=1,
        )
    )

    result = pipeline.process(
        "How AI changes healthcare operations",
        [
            {
                "source_id": "source_1",
                "title": "Hospital AI report",
                "url": "https://example.com/one",
                "content": "AI changes healthcare operations by automating hospital workflows and improving patient scheduling.",
            },
            {
                "source_id": "source_2",
                "title": "Healthcare AI article",
                "url": "https://example.com/two",
                "content": "AI changes healthcare operations by automating hospital workflows and improving patient scheduling.",
            },
        ],
    )

    assert len(result.selected_items) == 1
    assert result.selected_items[0].supporting_source_ids == ["source_1", "source_2"]
    assert any(item["reason"] == "duplicate" for item in result.excluded_chunks)


def test_content_selection_keeps_useful_sources_from_long_source_dominating() -> None:
    pipeline = ContentSelectionPipeline(
        PipelineConfig(
            target_chunk_tokens=60,
            total_source_token_budget=180,
            maximum_chunks_per_source=1,
        )
    )

    result = pipeline.process(
        "AI in digital marketing",
        [
            {
                "source_id": "source_1",
                "title": "Long AI marketing guide",
                "url": "https://example.com/long",
                "content": " ".join(
                    ["AI helps digital marketing teams personalize campaigns and analyze audience behavior."] * 15
                ),
            },
            {
                "source_id": "source_2",
                "title": "Digital marketing brand voice article",
                "url": "https://example.com/voice",
                "content": "AI content in digital marketing still needs human brand voice, editorial review, and audience strategy.",
            },
        ],
    )

    assert result.source_coverage["source_1"] == 1
    assert result.source_coverage["source_2"] == 1


def test_content_selection_excludes_irrelevant_source() -> None:
    pipeline = ContentSelectionPipeline(PipelineConfig(total_source_token_budget=180))

    result = pipeline.process(
        "AI in digital marketing",
        [
            {
                "source_id": "source_1",
                "title": "Marketing AI guide",
                "url": "https://example.com/marketing",
                "content": "AI helps marketers personalize digital campaigns and analyze customer behavior.",
            },
            {
                "source_id": "source_2",
                "title": "Travel cooking notes",
                "url": "https://example.com/travel",
                "content": "Mountain travel requires warm clothes, careful packing, and reliable transportation.",
            },
        ],
    )

    assert "source_1" in result.source_coverage
    assert "source_2" not in result.source_coverage


def test_content_selection_formats_only_selected_context_for_gemini() -> None:
    pipeline = ContentSelectionPipeline(
        PipelineConfig(
            target_chunk_tokens=50,
            total_source_token_budget=120,
            maximum_chunks_per_source=1,
        )
    )

    result = pipeline.process(
        "AI in content marketing",
        [
            {
                "source_id": "source_1",
                "title": "Content marketing AI",
                "url": "https://example.com/content",
                "content": "AI supports content marketing by drafting posts, testing headlines, and adapting campaign messages.",
            }
        ],
    )
    formatted = format_selected_context(result)

    assert "Evidence for: AI in content marketing" in formatted
    assert "relevance_score" not in formatted
    assert "excluded_chunks" not in formatted
    assert "Content marketing AI" in formatted


def test_content_selection_debug_log_reports_stats() -> None:
    context = ContentSelectionPipeline(PipelineConfig(total_source_token_budget=180)).process(
        "AI in content marketing",
        [
            {
                "source_id": "source_1",
                "title": "Content marketing AI",
                "url": "https://example.com/content",
                "content": "AI supports content marketing by drafting posts, testing headlines, and adapting campaign messages.",
            }
        ],
    )

    debug_log = AgentGraph.format_content_selection_debug_log(context, source_count=1)

    assert "Content selection stats:" in debug_log
    assert "fetched sources: 1" in debug_log
    assert "selected ideas:" in debug_log
    assert "selected source tokens:" in debug_log
    assert "source coverage:" in debug_log
    assert "candidate chunks:" in debug_log
    assert "top relevance scores:" in debug_log
    assert "fallback selected:" in debug_log
    assert "selected idea target:" in debug_log


def test_content_selection_normalizes_related_terms_for_chunking_and_relevance() -> None:
    result = ContentSelectionPipeline(
        PipelineConfig(
            target_chunk_tokens=60,
            total_source_token_budget=240,
            maximum_chunks_per_source=1,
        )
    ).process(
        "explain how relevancy score and chunking can fix this problem",
        [
            {
                "source_id": "source_1",
                "title": "Evaluating Chunking Strategies",
                "url": "https://example.com/chunking",
                "content": (
                    "Chunk boundaries affect how much useful context a model receives. "
                    "Token-level relevance can show whether selected passages match the question."
                ),
            },
            {
                "source_id": "source_2",
                "title": "Content Processing Quality",
                "url": "https://example.com/quality",
                "content": (
                    "Breaking content into focused sections can reduce noise and improve answer quality. "
                    "Relevance scoring helps select passages that match the user intent."
                ),
            },
        ],
    )

    assert result.selected_items
    assert result.debug_metrics["candidate_chunks"] >= 2
    assert "source_1" in result.source_coverage or "source_2" in result.source_coverage


def test_content_selection_falls_back_to_best_titled_chunks_when_threshold_blocks_all() -> None:
    result = ContentSelectionPipeline(
        PipelineConfig(
            minimum_relevance=0.95,
            fallback_minimum_relevance=0.01,
            target_chunk_tokens=60,
            total_source_token_budget=180,
            maximum_chunks_per_source=1,
        )
    ).process(
        "how can relevancy score and chunking fix the problem",
        [
            {
                "source_id": "source_1",
                "title": "Evaluating Chunking Strategies",
                "url": "https://example.com/chunking",
                "content": "Chunk boundaries and token-level relevance help select focused context for model answers.",
            },
            {
                "source_id": "source_2",
                "title": "Garden planning",
                "url": "https://example.com/garden",
                "content": "Healthy plants need soil, light, watering, and seasonal pruning.",
            },
        ],
    )

    assert result.selected_items
    assert result.debug_metrics["fallback_selected"] >= 1
    assert result.selected_items[0].source_title == "Evaluating Chunking Strategies"


def test_content_selection_respects_selected_idea_target_before_token_budget() -> None:
    result = ContentSelectionPipeline(
        PipelineConfig(
            selected_idea_target=3,
            target_chunk_tokens=45,
            total_source_token_budget=600,
            maximum_chunks_per_source=1,
        )
    ).process(
        "what is tokenization in a model and how is it implemented inside a model",
        [
            {
                "source_id": "source_1",
                "title": "Tokenization definition",
                "url": "https://example.com/one",
                "content": "Tokenization breaks text into tokens. Tokens can be words, subwords, or symbols used by language models. " * 4,
            },
            {
                "source_id": "source_2",
                "title": "AI tokenization explained",
                "url": "https://example.com/two",
                "content": "A tokenizer converts raw input into token ids that the model can process through embeddings. " * 4,
            },
            {
                "source_id": "source_3",
                "title": "Model implementation tokens",
                "url": "https://example.com/three",
                "content": "Inside a model, token ids map to vectors before attention layers process the sequence. " * 4,
            },
        ],
    )

    assert len(result.selected_items) == 3
    assert result.total_selected_tokens < 600
    assert result.debug_metrics["selected_idea_target"] == 3
    assert result.source_coverage == {"source_1": 1, "source_2": 1, "source_3": 1}
