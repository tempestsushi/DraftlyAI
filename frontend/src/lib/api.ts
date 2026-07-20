export type TopicStatus =
  | "pending"
  | "searching"
  | "drafting"
  | "review"
  | "complete"
  | "error";

export type Topic = {
  id: string;
  topic: string;
  status: TopicStatus;
  response_content: string | null;
  conversation_summary: string | null;
  created_at: string;
  updated_at?: string;
};

export type ChatMessageRecord = {
  id: string;
  topic_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  created_at: string;
};

export type MessageSource = {
  id: string;
  topic_id: string;
  message_id: string;
  title: string;
  url: string;
  domain: string | null;
  snippet: string | null;
  created_at: string;
};

export type TerminalLog = {
  id: string;
  topic_id: string | null;
  source: "ollama" | "web_search" | "web_fetch" | "linkedin" | "system";
  message: string;
  created_at: string;
};

export type Draft = {
  id: string;
  topic_id: string | null;
  source_message_id: string | null;
  title: string;
  content: string;
  source: "research";
  status: "pending" | "approved" | "rejected" | "published";
  linkedin_post_url: string | null;
  posted_at: string | null;
  created_at: string;
  updated_at?: string;
};

export type DraftVersion = {
  id: string;
  draft_id: string;
  version_number: number;
  content: string;
  reason: "created" | "edited" | "regenerated";
  created_at: string;
};

export type DraftImage = {
  id: string;
  draft_id: string;
  topic_id: string | null;
  title: string;
  image_url: string;
  thumbnail_url: string | null;
  source_url: string;
  source_domain: string | null;
  provider: string;
  width: number | null;
  height: number | null;
  created_at: string;
};

export type ImageResult = {
  title: string;
  image_url: string;
  thumbnail_url: string | null;
  source_url: string;
  source_domain: string | null;
  provider: string;
  width: number | null;
  height: number | null;
  score: number;
};

export type ImageUseCase =
  | "linkedin_post_illustration"
  | "blog_hero"
  | "technical_concept"
  | "abstract_topic"
  | "product_mockup";

export type DraftOptions = {
  tone: "professional" | "casual" | "thought_leadership";
  length: "short" | "medium" | "long";
  include_cta: boolean;
  include_hashtags: boolean;
};

export type ResearchDepth = "quick" | "moderate" | "deep";

export type Integration = {
  id: string;
  type: "linkedin_publish";
  name: string;
  status: "connected" | "disconnected" | "active" | "inactive";
  connected_at: string | null;
};

export type LinkedInStatus = {
  connected: boolean;
  name: string | null;
  email: string | null;
  picture_url: string | null;
  connected_at: string | null;
  expires_at: string | null;
};

export type StreamHandlers = {
  onStatus?: (payload: { topicId: string; state: TopicStatus }) => void;
  onUserMessage?: (payload: ChatMessageRecord) => void;
  onLog?: (payload: TerminalLog) => void;
  onToolStart?: (payload: TerminalLog) => void;
  onToolResult?: (payload: { topicId: string; source: string; message: string }) => void;
  onHeartbeat?: (payload: { topicId: string; state: string }) => void;
  onAnswerChunk?: (payload: { topicId: string; text: string }) => void;
  onDraftChunk?: (payload: { topicId: string; text: string }) => void;
  onDone?: (payload: {
    topicId: string;
    state: TopicStatus;
    assistantMessageId?: string;
    response?: string;
    draft: Draft | null;
    sources?: MessageSource[];
    error?: string | null;
  }) => void;
  onError?: () => void;
};

const API_BASE = (import.meta.env.VITE_BACKEND_URL as string | undefined) ?? "http://127.0.0.1:8001";

function debugStream(eventName: string, payload: unknown) {
  if (window.localStorage.getItem("draftly_debug_stream") === "1") {
    console.debug(`[Draftly stream] ${eventName}`, payload);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export const api = {
  listTopics() {
    return request<Topic[]>("/api/topics");
  },

  getTopic(topicId: string) {
    return request<Topic>(`/api/topics/${topicId}`);
  },

  listTopicMessages(topicId: string) {
    return request<ChatMessageRecord[]>(`/api/topics/${topicId}/messages`);
  },

  updateTopicMessage(topicId: string, messageId: string, content: string) {
    return request<ChatMessageRecord>(`/api/topics/${topicId}/messages/${messageId}`, {
      method: "PATCH",
      body: JSON.stringify({ content }),
    });
  },

  listTopicSources(topicId: string) {
    return request<MessageSource[]>(`/api/topics/${topicId}/sources`);
  },

  createTopicDraft(topicId: string, messageId?: string, title?: string, options?: Partial<DraftOptions>) {
    return request<Draft>(`/api/topics/${topicId}/draft`, {
      method: "POST",
      body: JSON.stringify({
        title,
        message_id: messageId,
        tone: options?.tone ?? "professional",
        length: options?.length ?? "medium",
        include_cta: options?.include_cta ?? true,
        include_hashtags: options?.include_hashtags ?? true,
      }),
    });
  },

  deleteTopic(topicId: string) {
    return request<{ ok: boolean }>(`/api/topics/${topicId}`, {
      method: "DELETE",
    });
  },

  listLogs(topicId?: string) {
    const query = topicId ? `?topic_id=${encodeURIComponent(topicId)}` : "";
    return request<TerminalLog[]>(`/api/logs${query}`);
  },

  listDrafts(topicId?: string) {
    const query = topicId ? `?topic_id=${encodeURIComponent(topicId)}` : "";
    return request<Draft[]>(`/api/drafts${query}`);
  },

  getDraft(draftId: string) {
    return request<Draft>(`/api/drafts/${draftId}`);
  },

  updateDraft(draftId: string, values: { content?: string; status?: Draft["status"]; clear_linkedin_post?: boolean }) {
    return request<Draft>(`/api/drafts/${draftId}`, {
      method: "PATCH",
      body: JSON.stringify(values),
    });
  },

  listDraftVersions(draftId: string) {
    return request<DraftVersion[]>(`/api/drafts/${draftId}/versions`);
  },

  regenerateDraft(draftId: string, options: DraftOptions) {
    return request<Draft>(`/api/drafts/${draftId}/regenerate`, {
      method: "POST",
      body: JSON.stringify(options),
    });
  },

  generateImages(prompt: string, useCase: ImageUseCase, count = 1) {
    return request<ImageResult[]>("/api/images/generate", {
      method: "POST",
      body: JSON.stringify({ prompt, use_case: useCase, count }),
    });
  },

  getDraftImage(draftId: string) {
    return request<DraftImage | null>(`/api/drafts/${draftId}/image`);
  },

  listDraftImages(draftId: string) {
    return request<DraftImage[]>(`/api/drafts/${draftId}/images`);
  },

  saveDraftImage(draftId: string, image: ImageResult) {
    return request<DraftImage>(`/api/drafts/${draftId}/images`, {
      method: "POST",
      body: JSON.stringify(image),
    });
  },

  deleteDraftImageById(draftId: string, imageId: string) {
    return request<{ deleted: boolean }>(`/api/drafts/${draftId}/images/${imageId}`, {
      method: "DELETE",
    });
  },

  deleteDraftImage(draftId: string) {
    return request<{ deleted: boolean }>(`/api/drafts/${draftId}/image`, {
      method: "DELETE",
    });
  },

  publishDraft(draftId: string) {
    return request<{
      ok: boolean;
      status: "published" | "failed";
      draft_id: string;
      published_at: string | null;
      linkedin_post_url: string | null;
      message: string;
    }>("/api/linkedin/publish", {
      method: "POST",
      body: JSON.stringify({ draft_id: draftId }),
    });
  },

  linkedInConnectUrl() {
    return `${API_BASE}/api/linkedin/connect`;
  },

  getLinkedInStatus() {
    return request<LinkedInStatus>("/api/linkedin/status");
  },

  disconnectLinkedIn() {
    return request<LinkedInStatus>("/api/linkedin/disconnect", {
      method: "POST",
    });
  },

  listIntegrations() {
    return request<Integration[]>("/api/integrations");
  },

  updateIntegration(
    integrationId: string,
    values: { status: Integration["status"]; connected_at: string | null }
  ) {
    return request<Integration>(`/api/integrations/${integrationId}`, {
      method: "PATCH",
      body: JSON.stringify(values),
    });
  },

  streamTopic(
    topic: string,
    handlers: StreamHandlers,
    topicId?: string | null,
    researchDepth: ResearchDepth = "moderate",
    regenerateMessageId?: string | null,
    responseStyle?: string | null,
    replaceUserMessageId?: string | null
  ) {
    const url = new URL(`${API_BASE}/api/agent/stream`);
    url.searchParams.set("topic", topic);
    if (topicId) {
      url.searchParams.set("topic_id", topicId);
    }
    url.searchParams.set("research_depth", researchDepth);
    if (regenerateMessageId) {
      url.searchParams.set("regenerate_message_id", regenerateMessageId);
    }
    if (replaceUserMessageId) {
      url.searchParams.set("replace_user_message_id", replaceUserMessageId);
    }
    if (responseStyle) {
      url.searchParams.set("response_style", responseStyle);
    }
    const stream = new EventSource(url);

    stream.addEventListener("status", (event) => {
      const payload = JSON.parse((event as MessageEvent).data);
      debugStream("status", payload);
      handlers.onStatus?.(payload);
    });
    stream.addEventListener("user_message", (event) => {
      const payload = JSON.parse((event as MessageEvent).data);
      debugStream("user_message", payload);
      handlers.onUserMessage?.(payload);
    });
    stream.addEventListener("log", (event) => {
      const payload = JSON.parse((event as MessageEvent).data);
      debugStream("log", payload);
      handlers.onLog?.(payload);
    });
    stream.addEventListener("tool_start", (event) => {
      const payload = JSON.parse((event as MessageEvent).data);
      debugStream("tool_start", payload);
      handlers.onToolStart?.(payload);
    });
    stream.addEventListener("tool_result", (event) => {
      const payload = JSON.parse((event as MessageEvent).data);
      debugStream("tool_result", payload);
      handlers.onToolResult?.(payload);
    });
    stream.addEventListener("heartbeat", (event) => {
      const payload = JSON.parse((event as MessageEvent).data);
      debugStream("heartbeat", payload);
      handlers.onHeartbeat?.(payload);
    });
    stream.addEventListener("answer_chunk", (event) => {
      const payload = JSON.parse((event as MessageEvent).data);
      debugStream("answer_chunk", payload);
      handlers.onAnswerChunk?.(payload);
    });
    stream.addEventListener("draft_chunk", (event) => {
      const payload = JSON.parse((event as MessageEvent).data);
      debugStream("draft_chunk", payload);
      handlers.onDraftChunk?.(payload);
      handlers.onAnswerChunk?.(payload);
    });
    stream.addEventListener("done", (event) => {
      const payload = JSON.parse((event as MessageEvent).data);
      debugStream("done", payload);
      handlers.onDone?.(payload);
      stream.close();
    });
    stream.onerror = () => {
      debugStream("error", { readyState: stream.readyState });
      handlers.onError?.();
      stream.close();
    };

    return stream;
  },
};
