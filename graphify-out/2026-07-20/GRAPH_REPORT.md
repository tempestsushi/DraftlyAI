# Graph Report - LinkedInAi  (2026-07-20)

## Corpus Check
- 109 files · ~36,879 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 723 nodes · 1653 edges · 41 communities (36 shown, 5 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 91 edges (avg confidence: 0.78)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_models.py|models.py]]
- [[_COMMUNITY_dashboard.tsx|dashboard.tsx]]
- [[_COMMUNITY_dependencies|dependencies]]
- [[_COMMUNITY_main.py|main.py]]
- [[_COMMUNITY_agent.py|agent.py]]
- [[_COMMUNITY_compilerOptions|compilerOptions]]
- [[_COMMUNITY_components.json|components.json]]
- [[_COMMUNITY_local-data.ts|local-data.ts]]
- [[_COMMUNITY_Comprehensive System Architecture Walkthrough In-App LinkedIn AI Automation Bot|Comprehensive System Architecture Walkthrough: In-App LinkedIn AI Automation Bot]]
- [[_COMMUNITY_SQLiteStoreBase|SQLiteStoreBase]]
- [[_COMMUNITY_local-data.ts|local-data.ts]]
- [[_COMMUNITY_Project Commands|Project Commands]]
- [[_COMMUNITY_Backend|Backend]]
- [[_COMMUNITY___init__.py|__init__.py]]
- [[_COMMUNITY___init__.py|__init__.py]]
- [[_COMMUNITY___init__.py|__init__.py]]
- [[_COMMUNITY_tailwind.config.ts|tailwind.config.ts]]
- [[_COMMUNITY_TopicRecord|TopicRecord]]
- [[_COMMUNITY_search_web|search_web]]
- [[_COMMUNITY_test_health_and_topics.py|test_health_and_topics.py]]
- [[_COMMUNITY_classify_request|classify_request]]
- [[_COMMUNITY_sidebar.tsx|sidebar.tsx]]
- [[_COMMUNITY_models.py|models.py]]
- [[_COMMUNITY_api.ts|api.ts]]
- [[_COMMUNITY_dashboard.tsx|dashboard.tsx]]
- [[_COMMUNITY_chat-message.tsx|chat-message.tsx]]
- [[_COMMUNITY_drafts.py|drafts.py]]
- [[_COMMUNITY_resolve_research_profile|resolve_research_profile]]
- [[_COMMUNITY_create_agent_graph|create_agent_graph]]
- [[_COMMUNITY_build_search_query|build_search_query]]
- [[_COMMUNITY_workflow.py|workflow.py]]
- [[_COMMUNITY_topics.py|topics.py]]
- [[_COMMUNITY_drafts-page.tsx|drafts-page.tsx]]
- [[_COMMUNITY_button.tsx|button.tsx]]
- [[_COMMUNITY_._compact_answer_for_draft|._compact_answer_for_draft]]
- [[_COMMUNITY_.build_extractive_source_context_text|.build_extractive_source_context_text]]

## God Nodes (most connected - your core abstractions)
1. `AgentGraph` - 43 edges
2. `SupabaseStore` - 41 edges
3. `InMemoryStore` - 34 edges
4. `stream_agent_run()` - 28 edges
5. `PipelineConfig` - 27 edges
6. `cn()` - 19 edges
7. `ContentSelectionPipeline` - 18 edges
8. `terms_for_text()` - 18 edges
9. `DraftRecord` - 17 edges
10. `run_rag_evaluation()` - 17 edges

## Surprising Connections (you probably didn't know these)
- `test_create_draft_from_topic_response_builds_new_draft()` --calls--> `create_draft_from_topic_response()`  [INFERRED]
  backend/tests/test_agent_service.py → backend/app/services/agent/drafts.py
- `test_rank_image_results_filters_low_quality_and_prefers_diagrams()` --calls--> `rank_image_results()`  [INFERRED]
  backend/tests/test_images.py → backend/app/services/images/search.py
- `AgentGraph` --uses--> `ResearchProfile`  [INFERRED]
  backend/app/agents/graph/helper.py → backend/app/agents/graph/profiles.py
- `test_answer_prompt_and_memory_context_stay_compact()` --calls--> `AgentGraph`  [INFERRED]
  backend/tests/test_agent_service.py → backend/app/agents/graph/helper.py
- `test_depth_window_does_not_expand_utility_llm_timeouts()` --calls--> `AgentGraph`  [INFERRED]
  backend/tests/test_agent_service.py → backend/app/agents/graph/helper.py

## Import Cycles
- None detected.

## Communities (41 total, 5 thin omitted)

### Community 0 - "models.py"
Cohesion: 0.10
Nodes (47): chunk_sources(), _make_chunk(), cluster_duplicates(), _find_duplicate(), format_selected_context(), _source_label(), calculate_mmr(), PipelineConfig (+39 more)

### Community 1 - "dashboard.tsx"
Cohesion: 0.13
Nodes (16): Badge(), BadgeProps, badgeVariants, DialogContent, DialogDescription, DialogFooter(), DialogHeader(), DialogOverlay (+8 more)

### Community 2 - "dependencies"
Cohesion: 0.06
Nodes (30): dependencies, autoprefixer, class-variance-authority, clsx, lucide-react, postcss, @radix-ui/react-dialog, @radix-ui/react-label (+22 more)

### Community 3 - "main.py"
Cohesion: 0.15
Nodes (12): lifespan(), IntegrationUpdateRequest, LinkedInPublishRequest, LinkedInPublishResponse, agent_stream(), ResearchDepth, update_integration(), linkedin_publish() (+4 more)

### Community 4 - "agent.py"
Cohesion: 0.11
Nodes (12): FakeAgent, test_create_draft_from_topic_response_builds_new_draft(), test_create_draft_from_topic_response_reuses_existing_draft(), test_moderate_mode_updates_conversation_summary(), test_quick_mode_skips_conversation_summary_update(), test_regenerate_draft_falls_back_to_latest_assistant_message(), test_stream_agent_run_passes_follow_up_memory_into_research_state(), test_stream_agent_run_persists_answer_and_sources() (+4 more)

### Community 5 - "compilerOptions"
Cohesion: 0.11
Nodes (17): compilerOptions, allowJs, esModuleInterop, isolatedModules, jsx, lib, module, moduleResolution (+9 more)

### Community 6 - "components.json"
Cohesion: 0.12
Nodes (16): aliases, components, hooks, lib, ui, utils, rsc, $schema (+8 more)

### Community 7 - "local-data.ts"
Cohesion: 0.20
Nodes (9): AGENT_INTRO, DEFAULT_DRAFT_OPTIONS, RESEARCH_DEPTH_OPTIONS, useDashboard(), ChatMessage(), ThinkingMessage(), CommandCenterPage(), CommandCenterPageProps (+1 more)

### Community 8 - "Comprehensive System Architecture Walkthrough: In-App LinkedIn AI Automation Bot"
Cohesion: 0.33
Nodes (5): 1. System Overview, 2. Chat And Research Flow, 3. Draft Flow, 4. LinkedIn Publishing Flow, Draftly Project Flow

### Community 9 - "SQLiteStoreBase"
Cohesion: 0.05
Nodes (20): create_supabase_store(), TopicStatus, SupabaseStore, DraftImageRecord, DraftRecord, DraftStatus, DraftVersionRecord, IntegrationRecord (+12 more)

### Community 10 - "local-data.ts"
Cohesion: 0.19
Nodes (15): _coerce_embedding(), cosine_similarity(), _embed_with_legacy_ollama(), embed_with_ollama(), EmbeddingError, RagChunk, RagConfig, RagContext (+7 more)

### Community 11 - "Project Commands"
Cohesion: 0.33
Nodes (5): Agent Test Flow, Backend, Frontend, Ollama, Project Commands

### Community 12 - "Backend"
Cohesion: 0.40
Nodes (4): Backend, Endpoints, Run, Test

### Community 14 - "__init__.py"
Cohesion: 0.70
Nodes (3): Backend application package., configure_langchain_defaults(), configure_warning_filters()

### Community 21 - "TopicRecord"
Cohesion: 0.19
Nodes (3): AgentGraph, test_answer_prompt_and_memory_context_stay_compact(), test_summarize_sources_uses_local_evidence_without_llm_call()

### Community 22 - "search_web"
Cohesion: 0.07
Nodes (46): _bm25_scores(), rank_search_results(), clean_source_text(), _is_junk_line(), _strip_markdown_noise(), _extract_with_trafilatura(), fetch_source_content(), _is_useful_extract() (+38 more)

### Community 23 - "test_health_and_topics.py"
Cohesion: 0.14
Nodes (16): ImageGenerateRequest, ImageResult, generate_image_options(), _build_generation_prompt(), _concept_visual_direction(), _extract_gemini_image(), _find_image_data(), generate_images() (+8 more)

### Community 24 - "classify_request"
Cohesion: 0.09
Nodes (39): AgentIntent, classify_request(), _contains_any(), _is_question(), RoutingDecision, _starts_with_any(), chunk_text(), sse_event() (+31 more)

### Community 25 - "sidebar.tsx"
Cohesion: 0.13
Nodes (12): CommandCenterPage, DraftsPage, ImagesPage, SettingsPage, topicIdFromUrl(), NAV_ITEMS, Sidebar(), SidebarProps (+4 more)

### Community 26 - "models.py"
Cohesion: 0.24
Nodes (14): AgentStreamPayload, DraftLength, DraftTone, ImageUseCase, IntegrationStatus, LogSource, MessageRole, TopicStatus (+6 more)

### Community 27 - "api.ts"
Cohesion: 0.15
Nodes (12): DEFAULT_REGENERATE_OPTIONS, api, Draft, DraftImage, DraftVersion, ImageUseCase, StreamHandlers, TerminalLog (+4 more)

### Community 28 - "dashboard.tsx"
Cohesion: 0.18
Nodes (13): UseDashboardProps, ChatMessageRecord, DraftOptions, Integration, CHATBOT_TONE_OPTIONS, ChatbotSettings, ChatbotTone, DEFAULT_CHATBOT_SETTINGS (+5 more)

### Community 29 - "chat-message.tsx"
Cohesion: 0.13
Nodes (8): CommandCenterMessage, MessageSource, INLINE_DEPTH_OPTIONS, isTableStart(), MarkdownContent(), MarkdownTable(), splitTableRow(), TogglePill()

### Community 30 - "drafts.py"
Cohesion: 0.24
Nodes (13): DraftImageSaveRequest, DraftRegenerateRequest, DraftUpdateRequest, add_draft_image(), delete_draft_image(), delete_one_draft_image(), get_draft(), get_draft_image() (+5 more)

### Community 31 - "resolve_research_profile"
Cohesion: 0.16
Nodes (12): create_chat_model(), ResearchDepth, ResearchProfile, resolve_research_profile(), build_search_query_variants(), test_create_chat_model_requires_gemini_key(), test_depth_window_does_not_expand_utility_llm_timeouts(), test_friendly_agent_error_messages_are_provider_specific() (+4 more)

### Community 32 - "create_agent_graph"
Cohesion: 0.25
Nodes (8): create_agent_graph(), ResearchDepth, FakeGraph, test_fetch_node_backfills_failed_fetches_with_snippets(), test_fetch_node_fetches_sources_in_parallel(), test_fetch_node_replaces_weak_extracts_with_later_strong_sources(), test_quick_depth_fetches_when_snippet_is_weak(), test_quick_depth_uses_snippet_without_fetch_when_snippet_is_strong()

### Community 33 - "build_search_query"
Cohesion: 0.33
Nodes (9): build_search_query(), _compact_prompt(), _looks_like_follow_up(), _meaningful_word_count(), _recent_context_for_follow_up(), test_build_search_query_preserves_freshness_terms(), test_build_search_query_preserves_user_prompt_wording(), test_build_search_query_uses_context_for_clarification_follow_up() (+1 more)

### Community 34 - "workflow.py"
Cohesion: 0.29
Nodes (4): AgentState, Settings, ResearchDepth, TypedDict

### Community 35 - "topics.py"
Cohesion: 0.31
Nodes (7): MessageUpdateRequest, TopicDraftRequest, create_topic_draft(), get_topic(), list_topic_messages(), list_topic_sources(), update_topic_message()

### Community 36 - "drafts-page.tsx"
Cohesion: 0.36
Nodes (5): useDraftQueue(), PageShell(), DraftsPage(), formatDraftPreview(), ToggleChip()

### Community 37 - "button.tsx"
Cohesion: 0.33
Nodes (5): Button, ButtonProps, buttonVariants, ResearchDepth, ChatComposer()

## Knowledge Gaps
- **97 isolated node(s):** `Settings`, `$schema`, `style`, `rsc`, `tsx` (+92 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ImageSearchResult` connect `models.py` to `api.ts`?**
  _High betweenness centrality (0.240) - this node is a cross-community bridge._
- **Why does `_normalize_image_result()` connect `models.py` to `search_web`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **Why does `AgentGraph` connect `TopicRecord` to `models.py`, `create_agent_graph`, `workflow.py`, `._compact_answer_for_draft`, `.build_extractive_source_context_text`, `local-data.ts`, `search_web`, `classify_request`, `resolve_research_profile`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `AgentGraph` (e.g. with `ResearchProfile` and `test_answer_prompt_and_memory_context_stay_compact()`) actually correct?**
  _`AgentGraph` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `stream_agent_run()` (e.g. with `test_moderate_mode_updates_conversation_summary()` and `test_quick_mode_skips_conversation_summary_update()`) actually correct?**
  _`stream_agent_run()` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `PipelineConfig` (e.g. with `ContentSelectionPipeline` and `test_content_selection_debug_log_reports_stats()`) actually correct?**
  _`PipelineConfig` has 9 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Backend application package.`, `Settings`, `Database package for backend persistence.` to the rest of the system?**
  _100 weakly-connected nodes found - possible documentation gaps or missing edges._