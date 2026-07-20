"use client";

import * as React from "react";

import { Button } from "@/components/ui/button";
import { type ResearchDepth } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Mic, Paperclip, Plus, Send, Square } from "lucide-react";

export function ChatComposer({
  textareaRef,
  input,
  isThinking,
  onInputChange,
  onKeyDown,
  onSend,
  onCancel,
  researchDepth,
  setResearchDepth,
  researchDepthOptions,
}: {
  textareaRef: React.RefObject<HTMLTextAreaElement>;
  input: string;
  isThinking: boolean;
  onInputChange: (event: React.ChangeEvent<HTMLTextAreaElement>) => void;
  onKeyDown: (event: React.KeyboardEvent<HTMLTextAreaElement>) => void;
  onSend: () => void;
  onCancel: () => void;
  researchDepth: ResearchDepth;
  setResearchDepth: (depth: ResearchDepth) => void;
  researchDepthOptions: Array<{ value: ResearchDepth; label: string; hint: string }>;
}) {
  return (
    <div className="shrink-0 border-t border-border/70 bg-background/95 backdrop-blur">
      <div className="mx-auto flex w-full max-w-4xl flex-col gap-3 px-4 pb-4 pt-3 lg:px-8">
        <div className="rounded-[1.75rem] border border-border bg-[hsl(225,11%,14%)] px-3 py-3 shadow-[0_-1px_0_rgba(255,255,255,0.02)]">
          <textarea
            ref={textareaRef}
            rows={1}
            value={input}
            onChange={onInputChange}
            onKeyDown={onKeyDown}
            placeholder="Ask anything"
            disabled={isThinking}
            className="w-full resize-none bg-transparent px-2 py-2 text-[15px] leading-7 text-foreground placeholder:text-muted-foreground/70 focus:outline-none disabled:opacity-50"
            style={{ minHeight: "44px", maxHeight: "160px" }}
          />
          <div className="mt-2 flex flex-wrap items-center gap-1">
            <Button variant="ghost" size="icon" className="h-9 w-9 rounded-full text-muted-foreground hover:text-foreground">
              <Plus className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="icon" className="h-9 w-9 rounded-full text-muted-foreground hover:text-foreground">
              <Paperclip className="h-4 w-4" />
            </Button>
            <div className="order-last mt-1 flex w-full items-center gap-1 rounded-full border border-border/70 bg-background/30 p-1 sm:order-none sm:ml-auto sm:mt-0 sm:w-auto">
              {researchDepthOptions.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  disabled={isThinking}
                  title={option.hint}
                  onClick={() => setResearchDepth(option.value)}
                  className={cn(
                    "flex-1 rounded-full px-3 py-1.5 text-xs transition-colors sm:flex-none",
                    researchDepth === option.value ? "bg-accent text-foreground" : "text-muted-foreground hover:text-foreground",
                    isThinking && "cursor-not-allowed opacity-50"
                  )}
                >
                  {option.label}
                </button>
              ))}
            </div>
            <Button variant="ghost" size="icon" className="h-9 w-9 rounded-full text-muted-foreground hover:text-foreground">
              <Mic className="h-4 w-4" />
            </Button>
            <Button
              onClick={isThinking ? onCancel : onSend}
              disabled={!isThinking && !input.trim()}
              size="icon"
              className="h-10 w-10 rounded-full bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-30"
            >
              {isThinking ? <Square className="h-4 w-4 fill-current" /> : <Send className="h-4 w-4" />}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
