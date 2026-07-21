"use client";

import * as React from "react";

import { api, type DraftOptions, type ResearchDepth } from "@/lib/api";
import { loadChatbotSettings, toneToResponseStyle } from "@/lib/settings";

import { AGENT_INTRO, DEFAULT_DRAFT_OPTIONS } from "./constants";
import { buildConversationMessages, isIntroOnly } from "./conversation";
import { recoveryDelayMs } from "./recovery";
import { type CommandCenterMessage } from "./types";

interface UseDashboardProps {
  topicId: string | null;
  shouldLoadTopic: boolean;
  onTopicCreated: (topicId: string | null) => void;
  onTopicActivity: () => void;
}

export function useDashboard({ topicId, shouldLoadTopic, onTopicCreated, onTopicActivity }: UseDashboardProps) {
  const [messages, setMessages] = React.useState<CommandCenterMessage[]>([AGENT_INTRO]);
  const [input, setInput] = React.useState("");
  const [isThinking, setIsThinking] = React.useState(false);
  const [isLoadingConversation, setIsLoadingConversation] = React.useState(false);
  const [showWelcome, setShowWelcome] = React.useState(true);
  const [activeStream, setActiveStream] = React.useState<EventSource | null>(null);
  const [creatingDraftMessageId, setCreatingDraftMessageId] = React.useState<string | null>(null);
  const [draftOptionsByMessageId, setDraftOptionsByMessageId] = React.useState<Record<string, DraftOptions>>({});
  const [researchDepth, setResearchDepth] = React.useState<ResearchDepth>("moderate");
  const [responseStyle, setResponseStyle] = React.useState(() => toneToResponseStyle(loadChatbotSettings().tone));
  const scrollRef = React.useRef<HTMLDivElement>(null);
  const textareaRef = React.useRef<HTMLTextAreaElement>(null);
  const prevTopicIdRef = React.useRef<string | null>(null);
  const prevShouldLoadTopicRef = React.useRef(false);
  const isStreamingRef = React.useRef(false);
  const cancelRequestedRef = React.useRef(false);
  const activeStreamRef = React.useRef<EventSource | null>(null);
  const activeTopicIdRef = React.useRef<string | null>(topicId);
  const activePromptRef = React.useRef("");
  const activeUserMessageIdRef = React.useRef<string | null>(null);
  const activePlaceholderIdRef = React.useRef<string | null>(null);

  React.useEffect(() => {
    if (topicId === prevTopicIdRef.current && shouldLoadTopic === prevShouldLoadTopicRef.current) {
      return;
    }

    if (isStreamingRef.current) {
      prevTopicIdRef.current = topicId;
      prevShouldLoadTopicRef.current = shouldLoadTopic;
      return;
    }

    prevTopicIdRef.current = topicId;
    prevShouldLoadTopicRef.current = shouldLoadTopic;

    if (!topicId || !shouldLoadTopic) {
      setIsLoadingConversation(false);
      setMessages([AGENT_INTRO]);
      setShowWelcome(true);
      setInput("");
      return;
    }

    void loadTopicConversation(topicId);
  }, [topicId, shouldLoadTopic]);

  React.useEffect(() => {
    activeTopicIdRef.current = topicId;
  }, [topicId]);

  React.useEffect(() => {
    const syncSettings = () => setResponseStyle(toneToResponseStyle(loadChatbotSettings().tone));
    window.addEventListener("storage", syncSettings);
    window.addEventListener("focus", syncSettings);
    return () => {
      window.removeEventListener("storage", syncSettings);
      window.removeEventListener("focus", syncSettings);
    };
  }, []);

  React.useEffect(() => {
    activeStreamRef.current = activeStream;
  }, [activeStream]);

  React.useEffect(() => {
    return () => {
      isStreamingRef.current = false;
      activeStream?.close();
    };
  }, [activeStream]);

  React.useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  React.useEffect(() => {
    if (!isThinking) {
      return;
    }

    let intervalId: number | undefined;
    const timeoutId = window.setTimeout(() => {
      intervalId = window.setInterval(() => {
        void recoverCompletedStream(activeTopicIdRef.current).then((recovered) => {
          if (!recovered) {
            return;
          }
          finishRecoveredStream();
        });
      }, 3000);
    }, recoveryDelayMs(researchDepth));

    return () => {
      window.clearTimeout(timeoutId);
      if (intervalId !== undefined) {
        window.clearInterval(intervalId);
      }
    };
  }, [isThinking, researchDepth]);

  function finishRecoveredStream() {
    isStreamingRef.current = false;
    setIsThinking(false);
    setActiveStream((stream) => {
      stream?.close();
      return null;
    });
  }

  async function loadTopicConversation(id: string) {
    const shouldShowSkeleton = !isStreamingRef.current && isIntroOnly(messages);
    if (shouldShowSkeleton) {
      setIsLoadingConversation(true);
    }
    try {
      const [topic, drafts, threadMessages, messageSources, logs] = await Promise.all([
        api.getTopic(id),
        api.listDrafts(id),
        api.listTopicMessages(id),
        api.listTopicSources(id),
        api.listLogs(id),
      ]);
      const reconstructed = buildConversationMessages({
        topic,
        drafts,
        threadMessages,
        messageSources,
        logs,
      });

      if (!isStreamingRef.current) {
        setMessages(reconstructed);
        setShowWelcome(false);
      }
    } finally {
      if (shouldShowSkeleton) {
        setIsLoadingConversation(false);
      }
    }
  }

  async function recoverCompletedStream(id: string | null): Promise<boolean> {
    if (!id) {
      return false;
    }

    try {
      const topic = await api.getTopic(id);
      if (topic.status === "complete" || topic.status === "review" || topic.status === "error") {
        await loadTopicConversation(id);
        onTopicActivity();
        return true;
      }
    } catch {
      return false;
    }

    return false;
  }

  function updateDraftOptions(messageId: string, patch: Partial<DraftOptions>) {
    setDraftOptionsByMessageId((prev) => ({
      ...prev,
      [messageId]: {
        ...(prev[messageId] ?? DEFAULT_DRAFT_OPTIONS),
        ...patch,
      },
    }));
  }

  async function handleCreateDraft(topicIdValue: string, messageId: string) {
    setCreatingDraftMessageId(messageId);
    try {
      await api.createTopicDraft(
        topicIdValue,
        messageId,
        undefined,
        draftOptionsByMessageId[messageId] ?? DEFAULT_DRAFT_OPTIONS
      );
      await loadTopicConversation(topicIdValue);
      onTopicActivity();
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          id: `draft-error-${crypto.randomUUID()}`,
          role: "agent",
          content:
            error instanceof Error ? `I couldn't save that draft: ${error.message}` : "I couldn't save that draft.",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setCreatingDraftMessageId(null);
    }
  }

  function handleCancelGeneration() {
    cancelRequestedRef.current = true;
    activeStreamRef.current?.close();
    activeStreamRef.current = null;
    isStreamingRef.current = false;
    setIsThinking(false);
    setActiveStream(null);
    setInput(activePromptRef.current);
    window.setTimeout(() => textareaRef.current?.focus(), 0);
    setMessages((prev) =>
      prev.map((message) => {
        if (message.id === activePlaceholderIdRef.current) {
          return {
            ...message,
            content: message.content || "Generation stopped. Edit your prompt below and send again.",
            isStreaming: false,
            canCreateDraft: false,
          };
        }
        if (message.id === activeUserMessageIdRef.current) {
          return { ...message, canEditPrompt: true };
        }
        return message;
      })
    );
  }

  function startAnswerStream({
    prompt,
    placeholderId,
    regenerateMessageId,
    replaceUserMessageId,
    depth,
  }: {
    prompt: string;
    placeholderId: string;
    regenerateMessageId?: string;
    replaceUserMessageId?: string;
    depth?: ResearchDepth;
  }) {
    const selectedDepth = depth ?? researchDepth;
    cancelRequestedRef.current = false;
    if (selectedDepth !== researchDepth) {
      setResearchDepth(selectedDepth);
    }
    setIsThinking(true);
    isStreamingRef.current = true;
    activePromptRef.current = prompt;
    activePlaceholderIdRef.current = placeholderId;
    activeStreamRef.current?.close();
    activeStream?.close();

    const stream = api.streamTopic(
      prompt,
      {
        onStatus: ({ topicId: streamedTopicId }) => {
          activeTopicIdRef.current = streamedTopicId;
          onTopicCreated(streamedTopicId);
        },
        onUserMessage: (savedMessage) => {
          activeTopicIdRef.current = savedMessage.topic_id;
          onTopicCreated(savedMessage.topic_id);
          setMessages((prev) =>
            prev.map((message) =>
              message.id === activeUserMessageIdRef.current || message.id === savedMessage.id
                ? {
                    ...message,
                    id: savedMessage.id,
                    content: savedMessage.content,
                    topicId: savedMessage.topic_id,
                  }
                : message
            )
          );
          activeUserMessageIdRef.current = savedMessage.id;
        },
        onLog: () => {},
        onToolStart: () => {},
        onToolResult: () => {},
        onAnswerChunk: ({ text }) => {
          setMessages((prev) => {
            let found = false;
            const next = prev.map((msg) => {
              if (msg.id !== placeholderId) return msg;
              found = true;
              return { ...msg, content: `${msg.content}${text}`, isStreaming: true };
            });
            if (found) return next;
            return [
              ...prev,
              {
                id: placeholderId,
                role: "agent",
                content: text,
                timestamp: new Date(),
                canCreateDraft: false,
                isStreaming: true,
              },
            ];
          });
        },
        onDone: ({ topicId: streamedTopicId, assistantMessageId, response, draft, sources, state, error }) => {
          activeTopicIdRef.current = streamedTopicId;
          onTopicCreated(streamedTopicId);
          onTopicActivity();
          isStreamingRef.current = false;
          setIsThinking(false);
          setActiveStream(null);
          activeStreamRef.current = null;
          setMessages((prev) => {
            let found = false;
            const next = prev.map((msg) => {
              if (msg.id === placeholderId) {
                found = true;
                const failed = state === "error";
                return {
                  ...msg,
                  id: assistantMessageId ?? msg.id,
                  content: failed ? error || "Something went wrong while processing that request." : response ?? "",
                  topicId: streamedTopicId,
                  canCreateDraft: failed ? false : !draft,
                  isStreaming: false,
                  draft,
                  sources: failed ? [] : sources ?? [],
                };
              }
              return msg;
            });
            if (found) return next;
            const failed = state === "error";
            return [
              ...prev,
              {
                id: assistantMessageId ?? placeholderId,
                role: "agent",
                content: failed ? error || "Something went wrong while processing that request." : response ?? "",
                timestamp: new Date(),
                topicId: streamedTopicId,
                canCreateDraft: failed ? false : !draft,
                isStreaming: false,
                draft,
                sources: failed ? [] : sources ?? [],
              },
            ];
          });
        },
        onError: async () => {
          if (cancelRequestedRef.current) {
            cancelRequestedRef.current = false;
            return;
          }
          const recovered = await recoverCompletedStream(activeTopicIdRef.current);
          isStreamingRef.current = false;
          setIsThinking(false);
          setActiveStream(null);
          activeStreamRef.current = null;
          if (recovered) {
            return;
          }
          onTopicActivity();
          setMessages((prev) =>
            prev.map((message) =>
              message.id === placeholderId
                ? {
                    ...message,
                    content: "The backend stream disconnected before finishing. Check that the FastAPI server is running on port 8001.",
                    isStreaming: false,
                    canCreateDraft: false,
                  }
                : message
            )
          );
        },
      },
      topicId ?? activeTopicIdRef.current,
      selectedDepth,
      regenerateMessageId,
      responseStyle,
      replaceUserMessageId
    );

    activeStreamRef.current = stream;
    setActiveStream(stream);
  }

  async function handleRegenerateAnswer(topicIdValue: string, messageId: string, depth: ResearchDepth = researchDepth) {
    if (isThinking) {
      return;
    }

    const answerMessageId = `regen-${crypto.randomUUID()}`;
    setShowWelcome(false);
    setMessages((prev) => [
      ...prev,
      {
        id: answerMessageId,
        role: "agent",
        content: "",
        timestamp: new Date(),
        canCreateDraft: false,
        isStreaming: true,
      },
    ]);
    activeTopicIdRef.current = topicIdValue;
    startAnswerStream({
      prompt: "Regenerate answer",
      placeholderId: answerMessageId,
      regenerateMessageId: messageId,
      depth,
    });
  }

  async function handleSend() {
    const trimmed = input.trim();
    if (!trimmed || isThinking) {
      return;
    }

    setShowWelcome(false);
    setInput("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }

    const userMsg: CommandCenterMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmed,
      timestamp: new Date(),
    };
    activeUserMessageIdRef.current = userMsg.id;

    const answerMessageId = `answer-${crypto.randomUUID()}`;

    setMessages((prev) => [
      ...prev,
      userMsg,
      {
        id: answerMessageId,
        role: "agent",
        content: "",
        timestamp: new Date(),
        canCreateDraft: false,
        isStreaming: true,
      },
    ]);

    startAnswerStream({
      prompt: trimmed,
      placeholderId: answerMessageId,
    });
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void handleSend();
    }
  }

  function handleInputChange(event: React.ChangeEvent<HTMLTextAreaElement>) {
    setInput(event.target.value);
    event.target.style.height = "auto";
    event.target.style.height = `${Math.min(event.target.scrollHeight, 120)}px`;
  }

  function handleEditPrompt(topicIdValue: string, messageId: string, prompt: string, depth: ResearchDepth = researchDepth) {
    const trimmed = prompt.trim();
    if (!trimmed || isThinking) {
      return;
    }

    const answerMessageId = `edit-answer-${crypto.randomUUID()}`;
    setShowWelcome(false);
    activeTopicIdRef.current = topicIdValue;
    activeUserMessageIdRef.current = messageId;
    setMessages((prev) => [
      ...prev.map((message) =>
        message.id === messageId
          ? {
              ...message,
              content: trimmed,
              topicId: topicIdValue,
            }
          : message
      ),
      {
        id: answerMessageId,
        role: "agent",
        content: "",
        timestamp: new Date(),
        canCreateDraft: false,
        isStreaming: true,
      },
    ]);
    startAnswerStream({
      prompt: trimmed,
      placeholderId: answerMessageId,
      replaceUserMessageId: messageId,
      depth,
    });
  }

  return {
    messages,
    input,
    setInput,
    isThinking,
    isLoadingConversation,
    showWelcome,
    creatingDraftMessageId,
    draftOptionsByMessageId,
    researchDepth,
    setResearchDepth,
    scrollRef,
    textareaRef,
    updateDraftOptions,
    handleCreateDraft,
    handleRegenerateAnswer,
    handleCancelGeneration,
    handleEditPrompt,
    handleSend,
    handleKeyDown,
    handleInputChange,
  };
}

