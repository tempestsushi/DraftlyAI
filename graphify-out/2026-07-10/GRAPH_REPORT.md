# Graph Report - LinkedInAi  (2026-07-10)

## Corpus Check
- 61 files · ~12,113 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 315 nodes · 547 edges · 19 communities (14 shown, 5 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS · INFERRED: 2 edges (avg confidence: 0.65)
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
- [[_COMMUNITY_Project Commands|Project Commands]]
- [[_COMMUNITY_Backend|Backend]]
- [[_COMMUNITY___init__.py|__init__.py]]
- [[_COMMUNITY___init__.py|__init__.py]]
- [[_COMMUNITY___init__.py|__init__.py]]
- [[_COMMUNITY_tailwind.config.ts|tailwind.config.ts]]

## God Nodes (most connected - your core abstractions)
1. `cn()` - 15 edges
2. `SQLiteStore` - 14 edges
3. `compilerOptions` - 14 edges
4. `AgentGraph` - 12 edges
5. `DraftRecord` - 12 edges
6. `SQLiteStoreBase` - 10 edges
7. `utc_now()` - 9 edges
8. `TopicRecord` - 9 edges
9. `RepositoryRecord` - 9 edges
10. `IntegrationRecord` - 9 edges

## Surprising Connections (you probably didn't know these)
- `AgentGraph` --uses--> `AgentState`  [INFERRED]
  backend/app/agents/graph.py → backend/app/agents/state.py
- `create_agent_graph()` --indirect_call--> `AgentState`  [INFERRED]
  backend/app/agents/graph.py → backend/app/agents/state.py
- `SQLiteStore` --inherits--> `SQLiteStoreBase`  [EXTRACTED]
  backend/app/store.py → backend/app/db/base.py
- `SQLiteStore` --inherits--> `IntegrationRepositoryMixin`  [EXTRACTED]
  backend/app/store.py → backend/app/db/integrations.py
- `stream_agent_run()` --references--> `SQLiteStore`  [EXTRACTED]
  backend/app/services/agent.py → backend/app/store.py

## Import Cycles
- None detected.

## Communities (19 total, 5 thin omitted)

### Community 0 - "models.py"
Cohesion: 0.09
Nodes (29): DraftRepositoryMixin, LogRepositoryMixin, RepositoryRepositoryMixin, TopicRepositoryMixin, AgentStreamPayload, DraftRecord, DraftStatus, GitHubSyncRequest (+21 more)

### Community 1 - "dashboard.tsx"
Cohesion: 0.06
Nodes (42): AGENT_INTRO, Dashboard(), DashboardProps, LogGroupBubble(), Message, QUICK_REPLIES, SOURCE_COLORS_LOCAL, SOURCE_LABELS_LOCAL (+34 more)

### Community 2 - "dependencies"
Cohesion: 0.06
Nodes (30): dependencies, autoprefixer, class-variance-authority, clsx, lucide-react, postcss, @radix-ui/react-dialog, @radix-ui/react-label (+22 more)

### Community 3 - "main.py"
Cohesion: 0.08
Nodes (16): Settings, IntegrationRepositoryMixin, initialize_schema(), Connection, Connection, seed_integrations(), lifespan(), DraftUpdateRequest (+8 more)

### Community 4 - "agent.py"
Cohesion: 0.11
Nodes (15): AgentGraph, create_agent_graph(), AgentIntent, classify_request(), RoutingDecision, AgentState, chunk_text(), sse_event() (+7 more)

### Community 5 - "compilerOptions"
Cohesion: 0.11
Nodes (17): compilerOptions, allowJs, esModuleInterop, isolatedModules, jsx, lib, module, moduleResolution (+9 more)

### Community 6 - "components.json"
Cohesion: 0.12
Nodes (16): aliases, components, hooks, lib, ui, utils, rsc, $schema (+8 more)

### Community 7 - "local-data.ts"
Cohesion: 0.12
Nodes (12): Draft, drafts, Integration, integrations, localData, repositories, Repository, Status (+4 more)

### Community 8 - "Comprehensive System Architecture Walkthrough: In-App LinkedIn AI Automation Bot"
Cohesion: 0.17
Nodes (11): 1. System Overview & Physical Boundaries, 2. Trigger Flow 1: On-Demand Research & Drafting, 3. Trigger Flow 2: Automated Portfolio & GitHub Sync, 4. The Final Publishing Destination (LinkedIn Core API), Comprehensive System Architecture Walkthrough: In-App LinkedIn AI Automation Bot, Phase A: Request and Handshake, Phase A: Webhook Interception, Phase B: Context-Optimized Token Stripping (+3 more)

### Community 11 - "Project Commands"
Cohesion: 0.33
Nodes (5): Agent Test Flow, Backend, Frontend, Ollama, Project Commands

### Community 12 - "Backend"
Cohesion: 0.50
Nodes (3): Backend, Endpoints, Run

## Knowledge Gaps
- **102 isolated node(s):** `Settings`, `$schema`, `style`, `rsc`, `tsx` (+97 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SQLiteStore` connect `models.py` to `SQLiteStoreBase`, `main.py`, `agent.py`?**
  _High betweenness centrality (0.019) - this node is a cross-community bridge._
- **What connects `Backend application package.`, `Settings`, `Database package for backend persistence.` to the rest of the system?**
  _105 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `models.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08821548821548822 - nodes in this community are weakly interconnected._
- **Should `dashboard.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.06448087431693988 - nodes in this community are weakly interconnected._
- **Should `dependencies` be split into smaller, more focused modules?**
  _Cohesion score 0.06451612903225806 - nodes in this community are weakly interconnected._
- **Should `main.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08292682926829269 - nodes in this community are weakly interconnected._
- **Should `agent.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10873440285204991 - nodes in this community are weakly interconnected._