import { type DraftOptions, type ResearchDepth } from "@/lib/api";

import { type CommandCenterMessage } from "./types";

export const DEFAULT_DRAFT_OPTIONS: DraftOptions = {
  tone: "professional",
  length: "medium",
  include_cta: true,
  include_hashtags: true,
};

export const RESEARCH_DEPTH_OPTIONS: Array<{
  value: ResearchDepth;
  label: string;
  hint: string;
}> = [
  { value: "quick", label: "Quick", hint: "1-2 sources, about 25-45s" },
  { value: "moderate", label: "Moderate", hint: "2-3 sources, about 45-75s" },
  { value: "deep", label: "Deep think", hint: "up to 5 sources, about 90-120s" },
];

export const AGENT_INTRO: CommandCenterMessage = {
  id: "intro",
  role: "agent",
  content:
    "Hi there. Ask about a topic or tool and I'll answer conversationally first. If you want, you can then turn the answer into a Draftly draft.",
  timestamp: new Date(),
};

