# Graph Report - LinkedInAi  (2026-07-13)

## Corpus Check
- 76 files · ~17,409 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 415 nodes · 817 edges · 24 communities (20 shown, 4 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 21 edges (avg confidence: 0.63)
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

## God Nodes (most connected - your core abstractions)
1. `AgentGraph` - 21 edges
2. `SQLiteStore` - 20 edges
3. `cn()` - 17 edges
4. `DraftRecord` - 14 edges
5. `FakeAgent` - 14 edges
6. `compilerOptions` - 14 edges
7. `stream_agent_run()` - 13 edges
8. `SQLiteStoreBase` - 12 edges
9. `utc_now()` - 10 edges
10. `TopicRecord` - 10 edges

## Surprising Connections (you probably didn't know these)
- `test_resolve_research_profile_distinguishes_depths()` --calls--> `resolve_research_profile()`  [INFERRED]
  backend/tests/test_agent_service.py → backend/app/agents/graph.py
- `test_stream_agent_run_returns_error_done_payload()` --calls--> `stream_agent_run()`  [INFERRED]
  backend/tests/test_agent_service.py → backend/app/services/agent.py
- `test_stream_agent_run_uses_fallback_when_planner_times_out()` --calls--> `stream_agent_run()`  [INFERRED]
  backend/tests/test_agent_service.py → backend/app/services/agent.py
- `TogglePill()` --calls--> `cn()`  [EXTRACTED]
  frontend/src/pages/command-center/chat-message.tsx → frontend/src/lib/utils.ts
- `AgentGraph` --uses--> `AgentState`  [INFERRED]
  backend/app/agents/graph.py → backend/app/agents/state.py

## Import Cycles
- None detected.

## Communities (24 total, 4 thin omitted)

### Community 0 - "models.py"
Cohesion: 0.14
Nodes (10): AgentGraph, create_agent_graph(), ResearchDepth, ResearchProfile, resolve_research_profile(), classify_request(), _contains_any(), RoutingDecision (+2 more)

### Community 1 - "dashboard.tsx"
Cohesion: 0.10
Nodes (30): App(), useGitHubSync(), PageShell(), NAV_ITEMS, Sidebar(), SidebarProps, Badge(), BadgeProps (+22 more)

### Community 2 - "dependencies"
Cohesion: 0.06
Nodes (30): dependencies, autoprefixer, class-variance-authority, clsx, lucide-react, postcss, @radix-ui/react-dialog, @radix-ui/react-label (+22 more)

### Community 3 - "main.py"
Cohesion: 0.07
Nodes (28): Settings, _ensure_column(), initialize_schema(), Connection, Connection, seed_integrations(), lifespan(), AgentStreamPayload (+20 more)

### Community 4 - "agent.py"
Cohesion: 0.08
Nodes (34): AgentIntent, chunk_text(), sse_event(), DraftRepositoryMixin, IntegrationRepositoryMixin, DraftLength, DraftRecord, DraftStatus (+26 more)

### Community 5 - "compilerOptions"
Cohesion: 0.11
Nodes (17): compilerOptions, allowJs, esModuleInterop, isolatedModules, jsx, lib, module, moduleResolution (+9 more)

### Community 6 - "components.json"
Cohesion: 0.12
Nodes (16): aliases, components, hooks, lib, ui, utils, rsc, $schema (+8 more)

### Community 7 - "local-data.ts"
Cohesion: 0.08
Nodes (28): AGENT_INTRO, CommandCenterMessage, DEFAULT_DRAFT_OPTIONS, QUICK_REPLIES, RESEARCH_DEPTH_OPTIONS, useDashboard(), UseDashboardProps, useDraftQueue() (+20 more)

### Community 8 - "Comprehensive System Architecture Walkthrough: In-App LinkedIn AI Automation Bot"
Cohesion: 0.17
Nodes (11): 1. System Overview & Physical Boundaries, 2. Trigger Flow 1: On-Demand Research & Drafting, 3. Trigger Flow 2: Automated Portfolio & GitHub Sync, 4. The Final Publishing Destination (LinkedIn Core API), Comprehensive System Architecture Walkthrough: In-App LinkedIn AI Automation Bot, Phase A: Request and Handshake, Phase A: Webhook Interception, Phase B: Context-Optimized Token Stripping (+3 more)

### Community 9 - "SQLiteStoreBase"
Cohesion: 0.08
Nodes (19): SQLiteStoreBase, LogRepositoryMixin, MessageRepositoryMixin, RepositoryRepositoryMixin, SourceRepositoryMixin, MessageRecord, MessageSourceRecord, RepositoryRecord (+11 more)

### Community 10 - "local-data.ts"
Cohesion: 0.12
Nodes (12): Draft, drafts, Integration, integrations, localData, repositories, Repository, Status (+4 more)

### Community 11 - "Project Commands"
Cohesion: 0.33
Nodes (5): Agent Test Flow, Backend, Frontend, Ollama, Project Commands

### Community 12 - "Backend"
Cohesion: 0.40
Nodes (4): Backend, Endpoints, Run, Test

### Community 21 - "TopicRecord"
Cohesion: 0.39
Nodes (3): TopicRepositoryMixin, TopicRecord, TopicStatus

### Community 22 - "search_web"
Cohesion: 0.43
Nodes (4): fetch_source_content(), _resolve_duckduckgo_url(), search_web(), SearchResult

## Knowledge Gaps
- **99 isolated node(s):** `Settings`, `$schema`, `style`, `rsc`, `tsx` (+94 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SQLiteStore` connect `SQLiteStoreBase` to `main.py`, `agent.py`, `TopicRecord`?**
  _High betweenness centrality (0.026) - this node is a cross-community bridge._
- **Why does `create_agent_graph()` connect `models.py` to `agent.py`?**
  _High betweenness centrality (0.014) - this node is a cross-community bridge._
- **What connects `Backend application package.`, `Settings`, `Database package for backend persistence.` to the rest of the system?**
  _102 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `models.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1431451612903226 - nodes in this community are weakly interconnected._
- **Should `dashboard.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.09574468085106383 - nodes in this community are weakly interconnected._
- **Should `dependencies` be split into smaller, more focused modules?**
  _Cohesion score 0.06451612903225806 - nodes in this community are weakly interconnected._
- **Should `main.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07020408163265306 - nodes in this community are weakly interconnected._