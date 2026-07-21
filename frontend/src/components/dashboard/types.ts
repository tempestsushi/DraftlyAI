import { type Draft, type MessageSource } from "@/lib/api";

export type CommandCenterMessage = {
  id: string;
  role: "agent" | "user";
  content: string;
  timestamp: Date;
  topicId?: string | null;
  draft?: Draft | null;
  canCreateDraft?: boolean;
  canEditPrompt?: boolean;
  isStreaming?: boolean;
  sources?: MessageSource[];
};

