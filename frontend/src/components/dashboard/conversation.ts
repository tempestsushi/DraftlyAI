import {
  type ChatMessageRecord,
  type Draft,
  type MessageSource,
  type TerminalLog,
  type Topic,
} from "@/lib/api";

import { AGENT_INTRO } from "./constants";
import { type CommandCenterMessage } from "./types";

export function isIntroOnly(messages: CommandCenterMessage[]) {
  return messages.length <= 1 && messages.every((message) => message.id === AGENT_INTRO.id);
}

export function buildConversationMessages({
  topic,
  drafts,
  threadMessages,
  messageSources,
  logs,
}: {
  topic: Topic;
  drafts: Draft[];
  threadMessages: ChatMessageRecord[];
  messageSources: MessageSource[];
  logs: TerminalLog[];
}): CommandCenterMessage[] {
  const draftByMessageId = new Map(
    drafts
      .filter((draft) => draft.source_message_id)
      .map((draft) => [draft.source_message_id as string, draft])
  );
  const sourcesByMessageId = new Map<string, MessageSource[]>();
  for (const source of messageSources) {
    const list = sourcesByMessageId.get(source.message_id) ?? [];
    list.push(source);
    sourcesByMessageId.set(source.message_id, list);
  }

  const latestDraft = drafts[0] ?? null;
  const lastAssistantMessageId = [...threadMessages].reverse().find((message) => message.role === "assistant")?.id;
  const hasAssistantMessage = Boolean(lastAssistantMessageId);
  const reconstructed: CommandCenterMessage[] = [AGENT_INTRO];

  if (threadMessages.length > 0) {
    reconstructed.push(
      ...threadMessages
        .filter((message) => message.role !== "system")
        .map((message: ChatMessageRecord): CommandCenterMessage => ({
          id: message.id,
          role: message.role === "assistant" ? "agent" : "user",
          content: message.content,
          timestamp: new Date(message.created_at),
          topicId: topic.id,
          draft: message.role === "assistant" ? draftByMessageId.get(message.id) ?? null : null,
          canCreateDraft: message.role === "assistant" ? !draftByMessageId.has(message.id) : false,
          sources: message.role === "assistant" ? sourcesByMessageId.get(message.id) ?? [] : [],
        }))
    );

    if (!hasAssistantMessage && topic.response_content) {
      reconstructed.push({
        id: `answer-fallback-${topic.id}`,
        role: "agent",
        content: topic.response_content,
        timestamp: new Date(topic.updated_at ?? topic.created_at),
        topicId: topic.id,
        draft: latestDraft,
        canCreateDraft: !latestDraft,
        sources: [],
      });
    }
  } else {
    reconstructed.push({
      id: `user-${topic.id}`,
      role: "user",
      content: topic.topic,
      timestamp: new Date(topic.created_at),
      topicId: topic.id,
    });
    if (topic.response_content) {
      reconstructed.push({
        id: `answer-${topic.id}`,
        role: "agent",
        content: topic.response_content,
        timestamp: new Date(topic.updated_at ?? topic.created_at),
        topicId: topic.id,
        draft: latestDraft,
        canCreateDraft: !latestDraft,
        sources: [],
      });
    }
  }

  if (topic.status === "error") {
    const latestErrorLog = [...logs]
      .reverse()
      .find((log) => log.source === "system" && log.message.startsWith("Agent run failed:"));
    reconstructed.push({
      id: `err-${topic.id}`,
      role: "agent",
      content:
        latestErrorLog?.message.replace(/^Agent run failed:\s*/, "") ||
        "Something went wrong while processing this topic. You can try submitting it again.",
      timestamp: new Date(topic.created_at),
    });
  }

  return reconstructed;
}

