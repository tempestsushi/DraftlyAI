import { type DraftOptions } from "@/lib/api";

export type ChatbotTone = "balanced" | "teacher" | "concise" | "technical";

export type ChatbotSettings = {
  tone: ChatbotTone;
};

export const CHATBOT_TONE_OPTIONS: Array<{ value: ChatbotTone; label: string; description: string }> = [
  {
    value: "balanced",
    label: "Balanced",
    description: "Clear, conversational answers with practical structure.",
  },
  {
    value: "teacher",
    label: "Teacher",
    description: "Explains step by step with simple examples.",
  },
  {
    value: "concise",
    label: "Concise",
    description: "Shorter answers that get to the point quickly.",
  },
  {
    value: "technical",
    label: "Technical",
    description: "More implementation detail, tradeoffs, and exact terminology.",
  },
];

export const DEFAULT_CHATBOT_SETTINGS: ChatbotSettings = {
  tone: "balanced",
};

const STORAGE_KEY = "draftly_chatbot_settings";
const LEGACY_STORAGE_KEY = "linkedin_ai_chatbot_settings";

export function loadChatbotSettings(): ChatbotSettings {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY) ?? window.localStorage.getItem(LEGACY_STORAGE_KEY);
    if (!raw) return DEFAULT_CHATBOT_SETTINGS;
    const parsed = JSON.parse(raw) as Partial<ChatbotSettings>;
    return {
      tone: CHATBOT_TONE_OPTIONS.some((option) => option.value === parsed.tone)
        ? parsed.tone as ChatbotTone
        : DEFAULT_CHATBOT_SETTINGS.tone,
    };
  } catch {
    return DEFAULT_CHATBOT_SETTINGS;
  }
}

export function saveChatbotSettings(settings: ChatbotSettings) {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
}

export function toneToResponseStyle(tone: ChatbotTone): string {
  switch (tone) {
    case "teacher":
      return "Use a patient teaching style. Explain step by step, define jargon, and include simple examples.";
    case "concise":
      return "Be concise. Answer directly, avoid long setup, and use compact bullets only when useful.";
    case "technical":
      return "Use a technical style. Include implementation details, tradeoffs, precise terminology, and practical caveats.";
    case "balanced":
    default:
      return "Use a balanced conversational style with clear structure and practical examples.";
  }
}

export const DEFAULT_DRAFT_OPTIONS: DraftOptions = {
  tone: "professional",
  length: "medium",
  include_cta: true,
  include_hashtags: true,
};
