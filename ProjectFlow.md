# Draftly Project Flow

## 1. System Overview

Draftly is a local-first LinkedIn drafting assistant.

- **Frontend:** Vite, React, and TypeScript. It provides the chat UI, draft queue, settings, and LinkedIn publishing controls.
- **Backend:** FastAPI with SQLite persistence. It manages chats, messages, drafts, source records, settings-backed model configuration, and Server-Sent Events streaming.
- **Agent Runtime:** LangChain/LangGraph coordinates prompt routing, web research, source fetching, local evidence building, conversation memory, and Gemini/Ollama response generation.

## 2. Chat And Research Flow

1. The user asks a question in the chat.
2. The frontend opens an EventSource stream to `/api/agent/stream`.
3. The backend classifies the request as a conversational answer, draft request, rewrite, or research-first answer.
4. For research requests, the agent creates search queries, retrieves sources, fetches text pages, builds compact evidence, and streams the final answer back into the chat.
5. The answer is saved with its messages, source records, and conversation memory.

## 3. Draft Flow

1. The user creates a draft from a specific saved chat answer.
2. The backend converts the answer into a LinkedIn-style post using the selected tone, length, CTA, and hashtag settings.
3. The draft is saved in the Draft Queue.
4. The user can edit, regenerate, approve, reject, or publish later.
5. Draft versions are stored so edits and regenerations remain traceable.

## 4. LinkedIn Publishing Flow

1. The user connects LinkedIn from Settings.
2. Approved drafts can be published through the backend publishing route.
3. The backend sends the post content to LinkedIn using the configured access token.
4. Draftly stores publish status, timestamp, and the published post URL when available.
