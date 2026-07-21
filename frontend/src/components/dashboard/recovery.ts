import { type ResearchDepth } from "@/lib/api";

export function recoveryDelayMs(depth: ResearchDepth) {
  if (depth === "quick") return 5000;
  if (depth === "moderate") return 8000;
  return 12000;
}

