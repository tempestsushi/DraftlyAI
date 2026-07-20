# Graph Report - LinkedInAi  (2026-07-20)

## Corpus Check
- 109 files · ~40,945 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 779 nodes · 1792 edges · 42 communities (33 shown, 9 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 105 edges (avg confidence: 0.78)
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
- [[_COMMUNITY_FakeGraph|FakeGraph]]

## God Nodes (most connected - your core abstractions)
1. `SupabaseStore` - 47 edges
2. `AgentGraph` - 44 edges
3. `InMemoryStore` - 39 edges
4. `stream_agent_run()` - 30 edges
5. `PipelineConfig` - 27 edges
6. `create_agent_graph()` - 24 edges
7. `DraftRecord` - 20 edges
8. `LinkedInAccountRecord` - 19 edges
9. `cn()` - 19 edges
10. `ContentSelectionPipeline` - 18 edges

## Surprising Connections (you probably didn't know these)
- `test_create_chat_model_requires_gemini_key()` --calls--> `create_chat_model()`  [INFERRED]
  backend/tests/test_agent_service.py → backend/app/agents/graph/llms.py
- `test_create_draft_from_topic_response_builds_new_draft()` --calls--> `create_draft_from_topic_response()`  [INFERRED]
  backend/tests/test_agent_service.py → backend/app/services/agent/drafts.py
- `test_stream_agent_run_prepares_query_without_planning_log()` --calls--> `stream_agent_run()`  [INFERRED]
  backend/tests/test_agent_service.py → backend/app/services/agent/stream.py
- `test_stream_agent_run_returns_error_done_payload()` --calls--> `stream_agent_run()`  [INFERRED]
  backend/tests/test_agent_service.py → backend/app/services/agent/stream.py
- `AgentGraph` --uses--> `ResearchProfile`  [INFERRED]
  backend/app/agents/graph/helper.py → backend/app/agents/graph/profiles.py

## Import Cycles
- None detected.

## Communities (42 total, 9 thin omitted)

### Community 0 - "models.py"
Cohesion: 0.08
Nodes (53): chunk_sources(), _make_chunk(), cluster_duplicates(), _find_duplicate(), format_selected_context(), _source_label(), calculate_mmr(), PipelineConfig (+45 more)

### Community 1 - "dashboard.tsx"
Cohesion: 0.14
Nodes (15): Badge(), BadgeProps, badgeVariants, DialogContent, DialogDescription, DialogFooter(), DialogHeader(), DialogOverlay (+7 more)

### Community 2 - "dependencies"
Cohesion: 0.06
Nodes (30): dependencies, autoprefixer, class-variance-authority, clsx, lucide-react, postcss, @radix-ui/react-dialog, @radix-ui/react-label (+22 more)

### Community 3 - "main.py"
Cohesion: 0.07
Nodes (32): create_supabase_store(), lifespan(), DraftImageSaveRequest, DraftRegenerateRequest, DraftUpdateRequest, IntegrationUpdateRequest, MessageUpdateRequest, RagEvaluationRequest (+24 more)

### Community 4 - "agent.py"
Cohesion: 0.09
Nodes (16): FakeAgent, test_create_chat_model_requires_gemini_key(), test_create_draft_from_topic_response_builds_new_draft(), test_create_draft_from_topic_response_reuses_existing_draft(), test_moderate_mode_updates_conversation_summary(), test_quick_mode_skips_conversation_summary_update(), test_regenerate_draft_falls_back_to_latest_assistant_message(), test_stream_agent_run_passes_follow_up_memory_into_research_state() (+8 more)

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
Cohesion: 0.09
Nodes (9): DraftImageRecord, IntegrationRecord, LinkedInOAuthStateRecord, MessageSourceRecord, client(), _swap_store(), test_store(), InMemoryStore (+1 more)

### Community 10 - "local-data.ts"
Cohesion: 0.09
Nodes (42): AgentStreamPayload, LinkedInAccountRecord, LinkedInPublishRequest, LinkedInPublishResponse, LinkedInStatusResponse, linkedin_callback(), linkedin_connect(), linkedin_disconnect() (+34 more)

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
Cohesion: 0.18
Nodes (3): AgentGraph, test_answer_prompt_and_memory_context_stay_compact(), test_summarize_sources_uses_local_evidence_without_llm_call()

### Community 22 - "search_web"
Cohesion: 0.05
Nodes (55): create_chat_model(), ResearchDepth, ResearchProfile, resolve_research_profile(), _bm25_scores(), build_search_query_variants(), rank_search_results(), _is_transient_fetch_error() (+47 more)

### Community 23 - "test_health_and_topics.py"
Cohesion: 0.13
Nodes (18): ImageGenerateRequest, ImageResult, generate_image_options(), _build_generation_prompt(), _concept_visual_direction(), _extract_gemini_image(), _extract_openrouter_image(), _find_image_data() (+10 more)

### Community 24 - "classify_request"
Cohesion: 0.09
Nodes (38): AgentIntent, classify_request(), _contains_any(), _is_question(), RoutingDecision, _starts_with_any(), chunk_text(), sse_event() (+30 more)

### Community 25 - "sidebar.tsx"
Cohesion: 0.12
Nodes (13): CommandCenterPage, DraftsPage, ImagesPage, SettingsPage, topicIdFromUrl(), NAV_ITEMS, Sidebar(), SidebarProps (+5 more)

### Community 26 - "models.py"
Cohesion: 0.22
Nodes (16): DraftLength, DraftRecord, DraftStatus, DraftTone, ImageUseCase, IntegrationStatus, LogSource, MessageRole (+8 more)

### Community 27 - "api.ts"
Cohesion: 0.12
Nodes (17): DEFAULT_REGENERATE_OPTIONS, api, Draft, DraftImage, DraftOptions, DraftVersion, ImageResult, ImageUseCase (+9 more)

### Community 28 - "dashboard.tsx"
Cohesion: 0.22
Nodes (10): UseDashboardProps, ChatMessageRecord, CHATBOT_TONE_OPTIONS, ChatbotSettings, ChatbotTone, DEFAULT_CHATBOT_SETTINGS, DEFAULT_DRAFT_OPTIONS, loadChatbotSettings() (+2 more)

### Community 29 - "chat-message.tsx"
Cohesion: 0.13
Nodes (8): CommandCenterMessage, MessageSource, INLINE_DEPTH_OPTIONS, isTableStart(), MarkdownContent(), MarkdownTable(), splitTableRow(), TogglePill()

### Community 30 - "drafts.py"
Cohesion: 0.14
Nodes (3): TopicStatus, SupabaseStore, utc_now()

### Community 32 - "create_agent_graph"
Cohesion: 0.21
Nodes (15): create_agent_graph(), ResearchDepth, AgentState, test_article_url_fetch_uses_general_fallback_variants(), test_fetch_node_backfills_failed_fetches_with_snippets(), test_fetch_node_fetches_sources_in_parallel(), test_fetch_node_replaces_weak_extracts_with_later_strong_sources(), test_follow_up_reuses_prior_source_url_without_search() (+7 more)

### Community 33 - "build_search_query"
Cohesion: 0.33
Nodes (9): build_search_query(), _compact_prompt(), _looks_like_follow_up(), _meaningful_word_count(), _recent_context_for_follow_up(), test_build_search_query_preserves_freshness_terms(), test_build_search_query_preserves_user_prompt_wording(), test_build_search_query_uses_context_for_clarification_follow_up() (+1 more)

### Community 36 - "drafts-page.tsx"
Cohesion: 0.36
Nodes (5): useDraftQueue(), PageShell(), DraftsPage(), formatDraftPreview(), ToggleChip()

### Community 37 - "button.tsx"
Cohesion: 0.33
Nodes (5): Button, ButtonProps, buttonVariants, ResearchDepth, ChatComposer()

## Knowledge Gaps
- **97 isolated node(s):** `Settings`, `$schema`, `style`, `rsc`, `tsx` (+92 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AgentGraph` connect `TopicRecord` to `models.py`, `create_agent_graph`, `._compact_answer_for_draft`, `.build_extractive_source_context_text`, `search_web`, `classify_request`?**
  _High betweenness centrality (0.050) - this node is a cross-community bridge._
- **Why does `SupabaseStore` connect `drafts.py` to `workflow.py`, `topics.py`, `main.py`, `SQLiteStoreBase`, `models.py`, `resolve_research_profile`?**
  _High betweenness centrality (0.025) - this node is a cross-community bridge._
- **Why does `PipelineConfig` connect `models.py` to `search_web`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `AgentGraph` (e.g. with `ResearchProfile` and `test_answer_prompt_and_memory_context_stay_compact()`) actually correct?**
  _`AgentGraph` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `stream_agent_run()` (e.g. with `test_moderate_mode_updates_conversation_summary()` and `test_quick_mode_skips_conversation_summary_update()`) actually correct?**
  _`stream_agent_run()` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `PipelineConfig` (e.g. with `ContentSelectionPipeline` and `test_content_selection_debug_log_reports_stats()`) actually correct?**
  _`PipelineConfig` has 9 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Backend application package.`, `Settings`, `Database package for backend persistence.` to the rest of the system?**
  _100 weakly-connected nodes found - possible documentation gaps or missing edges._