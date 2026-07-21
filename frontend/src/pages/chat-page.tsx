"use client";

import {
  AGENT_INTRO,
  DEFAULT_DRAFT_OPTIONS,
  RESEARCH_DEPTH_OPTIONS,
  useDashboard,
} from "@/components/dashboard";

import { ChatComposer } from "./command-center/chat-composer";
import { ChatMessage, ThinkingMessage } from "./command-center/chat-message";
import { WelcomePanel } from "./command-center/welcome-panel";

interface ChatPageProps {
  topicId: string | null;
  shouldLoadTopic: boolean;
  onTopicCreated: (topicId: string | null) => void;
  onTopicActivity: () => void;
}

export function ChatPage({
  topicId,
  shouldLoadTopic,
  onTopicCreated,
  onTopicActivity,
}: ChatPageProps) {
  const {
    messages,
    input,
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
  } = useDashboard({ topicId, shouldLoadTopic, onTopicCreated, onTopicActivity });
  const hasStreamingMessage = messages.some((message) => message.isStreaming);

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <div className="flex h-14 shrink-0 items-center justify-between border-b border-border px-4 lg:px-6">
        <div className="text-sm font-medium text-foreground">
          {topicId ? "Chat" : "New Chat"}
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span className="h-1.5 w-1.5 rounded-full bg-green-500" />
          Agent online
        </div>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto">
        <div className="mx-auto flex w-full max-w-4xl flex-col gap-6 px-3 pb-28 pt-6 sm:gap-8 sm:px-4 sm:pt-8 lg:px-8">
          {isLoadingConversation && !isThinking && !hasStreamingMessage ? (
            <ChatOpenSkeleton />
          ) : (
            <>
              {showWelcome && <WelcomePanel />}

              {messages.map((message) => (
                <ChatMessage
                  key={message.id}
                  message={message}
                  onCreateDraft={handleCreateDraft}
                  onRegenerate={handleRegenerateAnswer}
                  onEditPrompt={handleEditPrompt}
                  isCreatingDraft={creatingDraftMessageId === message.id}
                  draftOptions={draftOptionsByMessageId[message.id] ?? DEFAULT_DRAFT_OPTIONS}
                  onUpdateDraftOptions={updateDraftOptions}
                />
              ))}

              {isThinking && !messages.some((message) => message.isStreaming) && (
                <ThinkingMessage messageId={AGENT_INTRO.id}>
                  <div className="flex items-center gap-1.5 py-1">
                    <div className="typing-dot h-1.5 w-1.5 rounded-full bg-muted-foreground" />
                    <div className="typing-dot h-1.5 w-1.5 rounded-full bg-muted-foreground" />
                    <div className="typing-dot h-1.5 w-1.5 rounded-full bg-muted-foreground" />
                  </div>
                </ThinkingMessage>
              )}
            </>
          )}
        </div>
      </div>

      <ChatComposer
        textareaRef={textareaRef}
        input={input}
        isThinking={isThinking}
        onInputChange={handleInputChange}
        onKeyDown={handleKeyDown}
        onSend={() => void handleSend()}
        onCancel={handleCancelGeneration}
        researchDepth={researchDepth}
        setResearchDepth={setResearchDepth}
        researchDepthOptions={RESEARCH_DEPTH_OPTIONS}
      />
    </div>
  );
}

function ChatOpenSkeleton() {
  return (
    <div className="space-y-7">
      <div className="ml-auto h-12 w-2/3 max-w-md rounded-[1.6rem] skeleton-shimmer sm:w-80" />
      <div className="space-y-3">
        <div className="h-4 w-28 rounded-full skeleton-shimmer" />
        <div className="h-4 w-full rounded-full skeleton-shimmer" />
        <div className="h-4 w-11/12 rounded-full skeleton-shimmer" />
        <div className="h-4 w-8/12 rounded-full skeleton-shimmer" />
      </div>
      <div className="ml-auto h-12 w-1/2 max-w-sm rounded-[1.6rem] skeleton-shimmer sm:w-72" />
      <div className="space-y-3">
        <div className="h-4 w-32 rounded-full skeleton-shimmer" />
        <div className="h-4 w-full rounded-full skeleton-shimmer" />
        <div className="h-4 w-10/12 rounded-full skeleton-shimmer" />
      </div>
    </div>
  );
}
