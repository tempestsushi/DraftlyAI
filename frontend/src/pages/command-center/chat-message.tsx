"use client";

import * as React from "react";
import { Pencil, RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { type DraftOptions, type MessageSource, type ResearchDepth } from "@/lib/api";
import { cn } from "@/lib/utils";

import { type CommandCenterMessage } from "@/components/dashboard";

const INLINE_DEPTH_OPTIONS: Array<{ label: string; value: ResearchDepth }> = [
  { label: "Quick", value: "quick" },
  { label: "Moderate", value: "moderate" },
  { label: "Deep", value: "deep" },
];

function AssistantBlock({
  children,
  canCreateDraft,
  hasDraft,
  onCreateDraft,
  onRegenerate,
  isCreatingDraft,
  sources,
  draftOptions,
  onUpdateDraftOptions,
  messageId,
  isStreaming,
}: {
  children: React.ReactNode;
  canCreateDraft?: boolean;
  hasDraft?: boolean;
  onCreateDraft?: () => void;
  onRegenerate?: (depth: ResearchDepth) => void;
  isCreatingDraft?: boolean;
  sources?: MessageSource[];
  draftOptions?: DraftOptions;
  onUpdateDraftOptions?: (messageId: string, patch: Partial<DraftOptions>) => void;
  messageId?: string;
  isStreaming?: boolean;
}) {
  const [regenerateDepth, setRegenerateDepth] = React.useState<ResearchDepth>("moderate");

  return (
    <div className="min-w-0 flex-1">
      <div className="text-[15px] leading-8 text-foreground/92">
        {isStreaming && (
          <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-border bg-secondary/30 px-3 py-1 text-xs text-muted-foreground">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-primary" />
            Generating
          </div>
        )}
        {children}
        {isStreaming && <span className="ml-1 inline-block h-5 w-1 translate-y-1 animate-pulse rounded bg-primary/80" />}
        {sources && sources.length > 0 && <CitationLinks sources={sources} />}
      </div>
      {(canCreateDraft || hasDraft || onRegenerate) && (
        <div className="mt-4 space-y-3">
          {canCreateDraft && draftOptions && onUpdateDraftOptions && messageId && (
            <DraftControls options={draftOptions} onChange={(patch) => onUpdateDraftOptions(messageId, patch)} />
          )}
          <div className="flex items-center gap-2">
            {onRegenerate && (
              <div className="flex flex-wrap items-center gap-2">
                <DepthSelect value={regenerateDepth} onChange={setRegenerateDepth} ariaLabel="Regeneration depth" />
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => onRegenerate(regenerateDepth)}
                  className="h-8 rounded-full px-3 text-xs"
                  title="Regenerate answer"
                >
                  <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
                  Regenerate
                </Button>
              </div>
            )}
            {canCreateDraft && onCreateDraft && (
              <Button size="sm" onClick={onCreateDraft} disabled={isCreatingDraft} className="rounded-full px-4 text-xs">
                {isCreatingDraft ? "Creating draft..." : "Create draft from this answer"}
              </Button>
            )}
            {hasDraft && (
              <span className="rounded-full border border-border bg-secondary/40 px-3 py-1 text-xs text-muted-foreground">
                Draft saved for this answer
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function InlineMarkdown({ text }: { text: string }) {
  const parts: React.ReactNode[] = [];
  const pattern = /(\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)|`([^`]+)`|\*\*([^*]+)\*\*|__([^_]+)__|\*([^*\n]+)\*)/g;
  let cursor = 0;
  let match: RegExpExecArray | null;

  while ((match = pattern.exec(text)) !== null) {
    if (match.index > cursor) {
      parts.push(text.slice(cursor, match.index));
    }

    const [raw, , linkText, linkUrl, codeText, boldText, altBoldText, italicText] = match;
    const key = `${match.index}-${raw}`;
    if (linkText && linkUrl) {
      parts.push(
        <a key={key} href={linkUrl} target="_blank" rel="noreferrer" className="text-primary underline underline-offset-4">
          {linkText}
        </a>
      );
    } else if (codeText) {
      parts.push(
        <code key={key} className="rounded bg-secondary/60 px-1.5 py-0.5 text-[0.92em] text-foreground">
          {codeText}
        </code>
      );
    } else if (boldText || altBoldText) {
      parts.push(
        <strong key={key} className="font-semibold text-foreground">
          {boldText || altBoldText}
        </strong>
      );
    } else if (italicText) {
      parts.push(
        <em key={key} className="italic">
          {italicText}
        </em>
      );
    }
    cursor = match.index + raw.length;
  }

  if (cursor < text.length) {
    parts.push(text.slice(cursor));
  }

  return <>{parts}</>;
}

function MarkdownContent({ text }: { text: string }) {
  const lines = text.replace(/\r\n/g, "\n").split("\n");
  const blocks: React.ReactNode[] = [];
  let index = 0;

  while (index < lines.length) {
    const line = lines[index].trim();
    if (!line) {
      index += 1;
      continue;
    }

    if (line.startsWith("```")) {
      const language = line.slice(3).trim();
      const codeLines: string[] = [];
      index += 1;
      while (index < lines.length && !lines[index].trim().startsWith("```")) {
        codeLines.push(lines[index]);
        index += 1;
      }
      if (index < lines.length) index += 1;
      blocks.push(
        <div key={`code-${index}`} className="my-4 overflow-hidden rounded-xl border border-border bg-[hsl(225,11%,10%)]">
          {language && (
            <div className="border-b border-border bg-secondary/30 px-3 py-1.5 font-mono text-[11px] text-muted-foreground">
              {language}
            </div>
          )}
          <pre className="overflow-x-auto p-3 text-sm leading-6">
            <code>{codeLines.join("\n")}</code>
          </pre>
        </div>
      );
      continue;
    }

    if (isTableStart(lines, index)) {
      const tableLines: string[] = [];
      while (index < lines.length && lines[index].includes("|") && lines[index].trim()) {
        tableLines.push(lines[index]);
        index += 1;
      }
      blocks.push(<MarkdownTable key={`table-${index}`} lines={tableLines} />);
      continue;
    }

    const heading = /^(#{1,3})\s+(.+)$/.exec(line);
    if (heading) {
      const level = heading[1].length;
      const className =
        level === 1
          ? "mt-5 text-2xl font-semibold leading-9 text-foreground first:mt-0"
          : level === 2
            ? "mt-5 text-xl font-semibold leading-8 text-foreground first:mt-0"
            : "mt-4 text-base font-semibold leading-7 text-foreground first:mt-0";
      blocks.push(
        <div key={`heading-${index}`} className={className}>
          <InlineMarkdown text={heading[2]} />
        </div>
      );
      index += 1;
      continue;
    }

    if (/^[-*]\s+/.test(line)) {
      const items: string[] = [];
      while (index < lines.length && /^[-*]\s+/.test(lines[index].trim())) {
        items.push(lines[index].trim().replace(/^[-*]\s+/, ""));
        index += 1;
      }
      blocks.push(
        <ul key={`ul-${index}`} className="my-3 list-disc space-y-1 pl-5">
          {items.map((item, itemIndex) => (
            <li key={itemIndex}>
              <InlineMarkdown text={item} />
            </li>
          ))}
        </ul>
      );
      continue;
    }

    if (/^\d+[.)]\s+/.test(line)) {
      const items: string[] = [];
      while (index < lines.length && /^\d+[.)]\s+/.test(lines[index].trim())) {
        items.push(lines[index].trim().replace(/^\d+[.)]\s+/, ""));
        index += 1;
      }
      blocks.push(
        <ol key={`ol-${index}`} className="my-3 list-decimal space-y-1 pl-5">
          {items.map((item, itemIndex) => (
            <li key={itemIndex}>
              <InlineMarkdown text={item} />
            </li>
          ))}
        </ol>
      );
      continue;
    }

    const paragraphLines = [line];
    index += 1;
    while (
      index < lines.length &&
      lines[index].trim() &&
      !/^(#{1,3})\s+/.test(lines[index].trim()) &&
      !/^[-*]\s+/.test(lines[index].trim()) &&
      !/^\d+[.)]\s+/.test(lines[index].trim())
    ) {
      paragraphLines.push(lines[index].trim());
      index += 1;
    }

    blocks.push(
      <p key={`p-${index}`} className="my-3 first:mt-0 last:mb-0">
        <InlineMarkdown text={paragraphLines.join(" ")} />
      </p>
    );
  }

  return <div className="max-w-none">{blocks}</div>;
}

function isTableStart(lines: string[], index: number) {
  const current = lines[index]?.trim() ?? "";
  const next = lines[index + 1]?.trim() ?? "";
  return current.includes("|") && /^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?$/.test(next);
}

function splitTableRow(line: string) {
  return line
    .trim()
    .replace(/^\|/, "")
    .replace(/\|$/, "")
    .split("|")
    .map((cell) => cell.trim());
}

function MarkdownTable({ lines }: { lines: string[] }) {
  const headers = splitTableRow(lines[0] ?? "");
  const rows = lines.slice(2).map(splitTableRow);
  return (
    <div className="my-4 overflow-x-auto rounded-xl border border-border">
      <table className="min-w-full border-collapse text-left text-sm">
        <thead className="bg-secondary/40 text-xs text-muted-foreground">
          <tr>
            {headers.map((header, index) => (
              <th key={`${header}-${index}`} className="border-b border-border px-3 py-2 font-medium">
                <InlineMarkdown text={header} />
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr key={rowIndex} className="border-b border-border/60 last:border-0">
              {headers.map((_, cellIndex) => (
                <td key={cellIndex} className="px-3 py-2 align-top text-foreground/90">
                  <InlineMarkdown text={row[cellIndex] ?? ""} />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function UserBubble({
  children,
  onStartEdit,
}: {
  children: React.ReactNode;
  onStartEdit?: () => void;
}) {
  return (
    <div className="group flex justify-end">
      <div className="flex max-w-[min(78%,42rem)] flex-col items-end gap-1.5">
        <div className="rounded-[1.6rem] bg-[hsl(225,11%,14%)] px-4 py-3 text-[15px] leading-7 text-foreground/96 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.04)]">
          {children}
        </div>
        {onStartEdit && (
          <Button
            type="button"
            size="icon"
            variant="ghost"
            onClick={onStartEdit}
            className="h-8 w-8 rounded-full text-muted-foreground opacity-100 hover:text-foreground"
            title="Edit prompt"
            aria-label="Edit prompt"
          >
            <Pencil className="h-3.5 w-3.5" />
          </Button>
        )}
      </div>
    </div>
  );
}

function EditableUserPrompt({
  value,
  depth,
  onValueChange,
  onDepthChange,
  onCancel,
  onSubmit,
  disabled,
}: {
  value: string;
  depth: ResearchDepth;
  onValueChange: (value: string) => void;
  onDepthChange: (value: ResearchDepth) => void;
  onCancel: () => void;
  onSubmit: () => void;
  disabled?: boolean;
}) {
  return (
    <div className="flex justify-end">
      <div className="w-full max-w-[min(92%,42rem)] rounded-3xl border border-border bg-[hsl(225,11%,14%)] p-3 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.04)]">
        <textarea
          value={value}
          onChange={(event) => onValueChange(event.target.value)}
          className="min-h-24 w-full resize-none bg-transparent px-1 py-1 text-[15px] leading-7 text-foreground outline-none placeholder:text-muted-foreground"
          autoFocus
        />
        <div className="mt-3 flex flex-wrap items-center justify-end gap-2">
          <DepthSelect value={depth} onChange={onDepthChange} ariaLabel="Edited prompt depth" />
          <Button type="button" size="sm" variant="ghost" onClick={onCancel} className="rounded-full px-4 text-xs">
            Cancel
          </Button>
          <Button type="button" size="sm" onClick={onSubmit} disabled={disabled} className="rounded-full px-4 text-xs">
            Send
          </Button>
        </div>
      </div>
    </div>
  );
}

function DraftControls({
  options,
  onChange,
}: {
  options: DraftOptions;
  onChange: (patch: Partial<DraftOptions>) => void;
}) {
  return (
    <div className="rounded-2xl border border-border/70 bg-secondary/20 p-3">
      <div className="mb-2 text-xs font-medium text-foreground">Draft Options</div>
      <div className="flex flex-wrap gap-3">
        <OptionGroup
          label="Tone"
          value={options.tone}
          options={[
            { label: "Professional", value: "professional" },
            { label: "Casual", value: "casual" },
            { label: "Thought leadership", value: "thought_leadership" },
          ]}
          onChange={(value) => onChange({ tone: value as DraftOptions["tone"] })}
        />
        <OptionGroup
          label="Length"
          value={options.length}
          options={[
            { label: "Short", value: "short" },
            { label: "Medium", value: "medium" },
            { label: "Long", value: "long" },
          ]}
          onChange={(value) => onChange({ length: value as DraftOptions["length"] })}
        />
        <TogglePill label="CTA" active={options.include_cta} onClick={() => onChange({ include_cta: !options.include_cta })} />
        <TogglePill
          label="Hashtags"
          active={options.include_hashtags}
          onClick={() => onChange({ include_hashtags: !options.include_hashtags })}
        />
      </div>
    </div>
  );
}

function OptionGroup({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: Array<{ label: string; value: string }>;
  onChange: (value: string) => void;
}) {
  return (
    <div className="space-y-1">
      <div className="text-[11px] uppercase tracking-wide text-muted-foreground">{label}</div>
      <div className="flex flex-wrap gap-1.5">
        {options.map((option) => (
          <button
            key={option.value}
            type="button"
            onClick={() => onChange(option.value)}
            className={cn(
              "rounded-full border px-3 py-1 text-xs transition-colors",
              value === option.value ? "border-primary bg-primary/10 text-primary" : "border-border bg-background/40 text-muted-foreground hover:text-foreground"
            )}
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  );
}

function DepthSelect({
  value,
  onChange,
  ariaLabel,
}: {
  value: ResearchDepth;
  onChange: (value: ResearchDepth) => void;
  ariaLabel: string;
}) {
  return (
    <select
      value={value}
      onChange={(event) => onChange(event.target.value as ResearchDepth)}
      aria-label={ariaLabel}
      className="h-8 rounded-full border border-border bg-background/60 px-3 text-xs text-foreground outline-none transition-colors hover:border-primary/60"
    >
      {INLINE_DEPTH_OPTIONS.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  );
}

function TogglePill({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <div className="space-y-1">
      <div className="text-[11px] uppercase tracking-wide text-muted-foreground">{label}</div>
      <button
        type="button"
        onClick={onClick}
        className={cn(
          "rounded-full border px-3 py-1 text-xs transition-colors",
          active ? "border-primary bg-primary/10 text-primary" : "border-border bg-background/40 text-muted-foreground hover:text-foreground"
        )}
      >
        {active ? "On" : "Off"}
      </button>
    </div>
  );
}

function CitationLinks({ sources }: { sources: MessageSource[] }) {
  return (
    <span className="ml-1 inline-flex translate-y-[-0.18em] flex-wrap items-center gap-1 align-baseline">
      {sources.slice(0, 5).map((source, index) => (
        <a
          key={source.id}
          href={source.url}
          target="_blank"
          rel="noreferrer"
          title={`${source.title}${source.domain ? ` - ${source.domain}` : ""}`}
          aria-label={`Open source ${index + 1}: ${source.title}`}
          className="inline-flex h-5 min-w-5 items-center justify-center rounded-full border border-border/70 bg-secondary/40 px-1.5 text-[11px] font-medium leading-none text-muted-foreground transition-colors hover:border-primary/60 hover:bg-primary/10 hover:text-primary"
        >
          {index + 1}
        </a>
      ))}
    </span>
  );
}

export function ThinkingMessage({ children, messageId }: { children: React.ReactNode; messageId: string }) {
  return (
    <div className="bubble-in">
      <AssistantBlock messageId={messageId}>{children}</AssistantBlock>
    </div>
  );
}

export function ChatMessage({
  message,
  onCreateDraft,
  onRegenerate,
  onEditPrompt,
  isCreatingDraft,
  draftOptions,
  onUpdateDraftOptions,
}: {
  message: CommandCenterMessage;
  onCreateDraft: (topicId: string, messageId: string) => void;
  onRegenerate: (topicId: string, messageId: string, depth: ResearchDepth) => void;
  onEditPrompt: (topicId: string, messageId: string, prompt: string, depth: ResearchDepth) => void;
  isCreatingDraft: boolean;
  draftOptions: DraftOptions;
  onUpdateDraftOptions: (messageId: string, patch: Partial<DraftOptions>) => void;
}) {
  const [isEditing, setIsEditing] = React.useState(false);
  const [editValue, setEditValue] = React.useState(message.content);
  const [editDepth, setEditDepth] = React.useState<ResearchDepth>("moderate");

  React.useEffect(() => {
    if (!isEditing) {
      setEditValue(message.content);
    }
  }, [isEditing, message.content]);

  if (message.role === "agent") {
    const resolvedTopicId = typeof message.topicId === "string" ? message.topicId : null;
    return (
      <div className="bubble-in">
        <AssistantBlock
          canCreateDraft={message.canCreateDraft}
          hasDraft={Boolean(message.draft)}
          isCreatingDraft={isCreatingDraft}
          sources={message.sources}
          draftOptions={draftOptions}
          onUpdateDraftOptions={onUpdateDraftOptions}
          messageId={message.id}
          onCreateDraft={resolvedTopicId ? () => onCreateDraft(resolvedTopicId, message.id) : undefined}
          onRegenerate={resolvedTopicId ? (depth) => onRegenerate(resolvedTopicId, message.id, depth) : undefined}
          isStreaming={message.isStreaming}
        >
          {message.content ? (
            <MarkdownContent text={message.content} />
          ) : (
            <span className="text-muted-foreground">Preparing the answer...</span>
          )}
        </AssistantBlock>
      </div>
    );
  }

  const resolvedTopicId = typeof message.topicId === "string" ? message.topicId : null;
  if (isEditing && resolvedTopicId) {
    return (
      <div className="bubble-in">
        <EditableUserPrompt
          value={editValue}
          depth={editDepth}
          onValueChange={setEditValue}
          onDepthChange={setEditDepth}
          onCancel={() => {
            setEditValue(message.content);
            setIsEditing(false);
          }}
          onSubmit={() => {
            const trimmed = editValue.trim();
            if (!trimmed) {
              return;
            }
            setIsEditing(false);
            onEditPrompt(resolvedTopicId, message.id, trimmed, editDepth);
          }}
          disabled={!editValue.trim()}
        />
      </div>
    );
  }

  return (
    <div className="bubble-in">
      <UserBubble onStartEdit={resolvedTopicId ? () => setIsEditing(true) : undefined}>
        <p className="whitespace-pre-wrap">{message.content}</p>
      </UserBubble>
    </div>
  );
}
