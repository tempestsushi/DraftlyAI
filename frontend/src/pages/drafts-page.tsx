"use client";

import { useDraftQueue } from "@/components/draft-queue";
import { PageShell } from "@/components/page-shell";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  CheckCircle2,
  XCircle,
  Edit2,
  History,
  ExternalLink,
  Loader2,
  FileText,
  Clock,
  RefreshCw,
  Image as ImageIcon,
  Link2,
  Trash2,
  Send,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { type DraftOptions } from "@/lib/api";
import { ROUTES } from "@/lib/routes";

function formatDraftPreview(content: string) {
  return content
    .split(/\n{2,}/)
    .map((block) => block.trim())
    .filter(Boolean);
}

function DraftOptionSelect({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: Array<{ value: string; label: string }>;
  onChange: (value: string) => void;
}) {
  return (
    <label className="flex flex-col gap-1 text-[11px] text-muted-foreground">
      {label}
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="h-9 border border-border bg-background px-2 text-xs text-foreground outline-none focus:ring-1 focus:ring-primary/50"
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

function ToggleChip({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "h-8 border px-3 text-xs transition-colors",
        active
          ? "border-primary/50 bg-primary/10 text-primary"
          : "border-border bg-background/60 text-muted-foreground hover:text-foreground",
      )}
    >
      {label}: {active ? "On" : "Off"}
    </button>
  );
}

export function DraftsPage() {
  const {
    selectedDraft,
    setSelectedDraft,
    editing,
    setEditing,
    editContent,
    setEditContent,
    draftVersions,
    draftImages,
    regenerateOptions,
    updateRegenerateOptions,
    isApproving,
    isRejecting,
    isPublishing,
    isRegenerating,
    regenerateError,
    publishError,
    loading,
    handleApprove,
    handleReject,
    handlePublishDraft,
    handleSaveEdit,
    handleRegenerateDraft,
    handleDeleteImage,
    pendingDrafts,
    processedDrafts,
  } = useDraftQueue();

  function openImagePicker(draftId: string) {
    window.history.pushState({}, "", `${ROUTES.images}?draft=${encodeURIComponent(draftId)}`);
    window.dispatchEvent(new Event("popstate"));
  }

  return (
    <PageShell
      title="Draft Queue"
      flush
      headerAction={
        <Badge
          variant="secondary"
          className="border-0 bg-primary/10 font-mono text-xs text-primary"
        >
          {pendingDrafts.length} pending
        </Badge>
      }
    >
      <div className="flex h-full flex-col">
        <div
          className="flex flex-1 flex-col lg:flex-row"
          style={{ minHeight: 0 }}
        >
          <div className="flex min-h-[270px] w-full flex-col overflow-hidden border-b border-border bg-card lg:min-h-0 lg:w-64 lg:border-b-0 lg:border-r xl:w-72">
            <div className="border-b border-border px-4 py-2.5">
              <span className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
                Pending
              </span>
            </div>

            <div className="flex-1 overflow-y-auto">
              {loading ? (
                <div className="flex items-center justify-center p-8">
                  <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                </div>
              ) : pendingDrafts.length === 0 ? (
                <div className="flex flex-col items-center justify-center p-8 text-center">
                  <FileText className="mb-2 h-8 w-8 text-muted-foreground/30" />
                  <p className="text-xs text-muted-foreground">
                    No pending drafts
                  </p>
                </div>
              ) : (
                <div className="space-y-1.5 p-2">
                  {pendingDrafts.map((draft) => (
                    <button
                      key={draft.id}
                      onClick={() => setSelectedDraft(draft)}
                      className={cn(
                        "group w-full border px-2.5 py-2.5 text-left transition-all",
                        selectedDraft?.id === draft.id
                          ? "border-primary/30 bg-primary/10"
                          : "border-transparent hover:bg-accent",
                      )}
                    >
                      <p className="mb-1.5 line-clamp-2 text-xs font-medium leading-snug text-foreground/85 group-hover:text-foreground">
                        {draft.content.split("\n")[0]}
                      </p>
                      <div className="flex items-center gap-1.5">
                        <span className="bg-secondary px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
                          {draft.source_message_id ? "Chat answer" : "Research"}
                        </span>
                        <span className="flex items-center gap-1 text-[10px] text-muted-foreground">
                          <Clock className="h-2.5 w-2.5" />
                          {new Date(draft.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {processedDrafts.length > 0 && (
              <>
                <div className="border-t border-border px-4 py-2.5">
                  <span className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
                    Processed
                  </span>
                </div>
                <div className="max-h-48 overflow-y-auto space-y-1.5 p-2">
                  {processedDrafts.slice(0, 5).map((draft) => (
                    <button
                      key={draft.id}
                      type="button"
                      onClick={() => setSelectedDraft(draft)}
                      className="flex items-center gap-2 border border-transparent px-3 py-2 hover:bg-accent"
                    >
                      <div className="min-w-0 flex-1">
                        <p className="line-clamp-1 text-xs text-muted-foreground">
                          {draft.content.split("\n")[0]}
                        </p>
                      </div>
                      <span
                        className={cn(
                          "h-1.5 w-1.5 shrink-0 rounded-full",
                          draft.status === "approved"
                            ? "bg-green-500"
                            : draft.status === "rejected"
                              ? "bg-red-500"
                              : "bg-muted-foreground",
                        )}
                      />
                      {draft.linkedin_post_url && (
                        <a
                          href={draft.linkedin_post_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          onClick={(event) => event.stopPropagation()}
                        >
                          <ExternalLink className="h-3 w-3 text-muted-foreground hover:text-primary" />
                        </a>
                      )}
                    </button>
                  ))}
                </div>
              </>
            )}
          </div>

          <div className="flex min-h-[420px] flex-1 flex-col overflow-hidden bg-card">
            {!selectedDraft ? (
              <div className="flex flex-1 flex-col items-center justify-center p-8 text-center">
                <div className="mb-4 flex h-12 w-12 items-center justify-center border border-border bg-muted/50">
                  <FileText className="h-5 w-5 text-muted-foreground/40" />
                </div>
                <p className="text-sm text-muted-foreground">
                  Select a draft to preview
                </p>
                <p className="mt-1 text-xs text-muted-foreground/60">
                  Review and approve before posting
                </p>
              </div>
            ) : (
              <>
                <div className="flex h-12 shrink-0 items-center gap-2.5 border-b border-border px-4">
                  <div className="flex h-5 w-5 items-center justify-center border border-border bg-primary/10">
                    <FileText className="h-3 w-3 text-primary" />
                  </div>
                  <span className="text-xs font-medium">Draftly Draft</span>
                  {selectedDraft.source_message_id && (
                    <span className="bg-secondary px-2 py-0.5 text-[10px] text-muted-foreground">
                      From answer {selectedDraft.source_message_id.slice(0, 8)}
                    </span>
                  )}
                  <span className="ml-auto bg-primary/10 px-2 py-0.5 text-[9px] font-medium text-primary">
                    {selectedDraft.status}
                  </span>
                </div>

                <div className="flex-1 overflow-y-auto">
                  <div className="mx-auto flex max-w-5xl flex-col">
                    {editing === selectedDraft.id ? (
                      <textarea
                        value={editContent}
                        onChange={(event) => setEditContent(event.target.value)}
                        className="h-[460px] min-h-[300px] w-full resize-none border-b border-border bg-secondary/30 px-4 py-3 text-sm leading-relaxed text-foreground/90 focus:outline-none focus:ring-1 focus:ring-primary/50"
                      />
                    ) : (
                      <div className="border-b border-border bg-[hsl(225,11%,14%)] p-5 sm:p-7">
                        <div className="mx-auto max-w-3xl space-y-4">
                          {formatDraftPreview(selectedDraft.content).map(
                            (block, index) => (
                              <p
                                key={`${selectedDraft.id}-${index}`}
                                className="whitespace-pre-wrap text-[15px] leading-7 text-foreground/90 sm:text-base sm:leading-8"
                              >
                                {block}
                              </p>
                            ),
                          )}
                        </div>
                      </div>
                    )}

                    <div className="border-b border-border bg-secondary/10 p-3 sm:p-4">
                      <div className="mb-3 flex items-center gap-2 text-xs font-medium">
                        <ImageIcon className="h-3.5 w-3.5 text-primary" />
                        Post image
                      </div>

                      {draftImages.length > 0 ? (
                        <div className="mb-3 border border-border bg-background/50 p-2">
                          <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
                            {draftImages.map((image) => (
                              <div key={image.id} className="flex gap-2">
                                <img
                                  src={image.thumbnail_url ?? image.image_url}
                                  alt={image.title}
                                  className="h-16 w-24 shrink-0 object-cover"
                                />
                                <div className="min-w-0 flex-1">
                                  <p className="line-clamp-2 text-[11px] font-medium text-foreground">
                                    {image.title}
                                  </p>
                                  <a
                                    href={image.source_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="mt-1 inline-flex items-center gap-1 text-[10px] text-primary hover:underline"
                                  >
                                    <Link2 className="h-3 w-3" />
                                    {image.source_domain ?? "Open source"}
                                  </a>
                                </div>
                              </div>
                            ))}
                          </div>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="mt-2 h-8 gap-1.5 text-xs text-muted-foreground"
                            onClick={() => void handleDeleteImage(selectedDraft)}
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                            Remove all
                          </Button>
                        </div>
                      ) : (
                        <p className="mb-3 text-xs text-muted-foreground">
                          No image selected for this draft.
                        </p>
                      )}

                      <Button
                        size="sm"
                        variant="secondary"
                        className="h-9 gap-1.5 text-xs"
                        onClick={() => openImagePicker(selectedDraft.id)}
                      >
                        <ImageIcon className="h-3.5 w-3.5" />
                        {draftImages.length > 0 ? "Add/change images" : "Choose images"}
                      </Button>
                    </div>

                    <div className="grid border-b border-border xl:grid-cols-[minmax(0,1.35fr)_minmax(260px,0.65fr)]">
                      <div className="border-b border-border bg-secondary/20 p-3 sm:p-4 xl:border-b-0 xl:border-r">
                        <div className="mb-3 flex items-center gap-2 text-xs font-medium">
                          <RefreshCw className="h-3.5 w-3.5 text-primary" />
                          Regenerate this draft
                        </div>
                        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-[1fr_1fr_auto] xl:items-end">
                          <DraftOptionSelect
                            label="Tone"
                            value={regenerateOptions.tone}
                            options={[
                              { value: "professional", label: "Professional" },
                              { value: "casual", label: "Casual" },
                              {
                                value: "thought_leadership",
                                label: "Thought leadership",
                              },
                            ]}
                            onChange={(value) =>
                              updateRegenerateOptions({
                                tone: value as DraftOptions["tone"],
                              })
                            }
                          />
                          <DraftOptionSelect
                            label="Length"
                            value={regenerateOptions.length}
                            options={[
                              { value: "short", label: "Short" },
                              { value: "medium", label: "Medium" },
                              { value: "long", label: "Long" },
                            ]}
                            onChange={(value) =>
                              updateRegenerateOptions({
                                length: value as DraftOptions["length"],
                              })
                            }
                          />
                          <div className="flex flex-wrap items-center gap-2 sm:col-span-2 xl:col-span-1">
                            <ToggleChip
                              label="CTA"
                              active={regenerateOptions.include_cta}
                              onClick={() =>
                                updateRegenerateOptions({
                                  include_cta: !regenerateOptions.include_cta,
                                })
                              }
                            />
                            <ToggleChip
                              label="Hashtags"
                              active={regenerateOptions.include_hashtags}
                              onClick={() =>
                                updateRegenerateOptions({
                                  include_hashtags:
                                    !regenerateOptions.include_hashtags,
                                })
                              }
                            />
                          </div>
                          <Button
                            size="sm"
                            onClick={() =>
                              void handleRegenerateDraft(selectedDraft)
                            }
                            disabled={isRegenerating === selectedDraft.id}
                            className="h-9 text-xs sm:col-span-2 xl:col-span-3"
                          >
                            {isRegenerating === selectedDraft.id ? (
                              <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />
                            ) : (
                              <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
                            )}
                            Regenerate
                          </Button>
                          {regenerateError && (
                            <p className="text-xs text-destructive sm:col-span-2 xl:col-span-3">
                              {regenerateError}
                            </p>
                          )}
                        </div>
                      </div>

                      <div className="bg-secondary/20 p-3">
                        <div className="mb-3 flex items-center gap-2 text-xs font-medium">
                          <History className="h-3.5 w-3.5 text-primary" />
                          Versions
                        </div>
                        <div className="space-y-2">
                          {draftVersions.map((version) => (
                            <div
                              key={version.id}
                              className="border border-border/70 bg-background/50 px-2 py-2"
                            >
                              <div className="flex items-center justify-between text-[11px]">
                                <span className="font-medium text-foreground">
                                  v{version.version_number}
                                </span>
                                <span className="capitalize text-muted-foreground">
                                  {version.reason}
                                </span>
                              </div>
                              <p className="mt-1 line-clamp-2 text-[11px] leading-4 text-muted-foreground">
                                {version.content}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="shrink-0 border-t border-border p-3">
                  {editing === selectedDraft.id ? (
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        onClick={() => void handleSaveEdit(selectedDraft)}
                        className="h-9 flex-1 text-xs"
                      >
                        Save Changes
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => setEditing(null)}
                        className="h-9 text-xs"
                      >
                        Cancel
                      </Button>
                    </div>
                  ) : (
                    <div className="flex flex-col gap-2">
                      {publishError && (
                        <p className="text-xs text-destructive">{publishError}</p>
                      )}
                      {selectedDraft.linkedin_post_url && (
                        <a
                          href={selectedDraft.linkedin_post_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex h-9 items-center justify-center gap-1.5 border border-primary/40 bg-primary/10 px-3 text-xs font-medium text-primary hover:bg-primary/15"
                        >
                          <ExternalLink className="h-3.5 w-3.5" />
                          Open LinkedIn post
                        </a>
                      )}
                      {selectedDraft.status === "published" && (
                        <p className="text-xs text-muted-foreground">
                          Edit this draft to clear the old LinkedIn link and repost it as a new post.
                        </p>
                      )}
                      <div className="flex gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-9 flex-1 gap-1.5 text-xs"
                        onClick={() => {
                          setEditing(selectedDraft.id);
                          setEditContent(selectedDraft.content);
                        }}
                      >
                        <Edit2 className="h-3.5 w-3.5" />
                        Edit
                      </Button>
                      {selectedDraft.status !== "published" && (
                        <Button
                          variant="destructive"
                          size="sm"
                          className="h-9 flex-1 gap-1.5 border-0 bg-red-500/10 text-xs text-red-400 hover:bg-red-500/20"
                          onClick={() => void handleReject(selectedDraft)}
                          disabled={isRejecting === selectedDraft.id}
                        >
                          {isRejecting === selectedDraft.id ? (
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          ) : (
                            <XCircle className="h-3.5 w-3.5" />
                          )}
                          Reject
                        </Button>
                      )}
                      {selectedDraft.status === "pending" && (
                        <Button
                          size="sm"
                          className="h-9 flex-1 gap-1.5 text-xs"
                          onClick={() => void handleApprove(selectedDraft)}
                          disabled={isApproving === selectedDraft.id}
                        >
                          {isApproving === selectedDraft.id ? (
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          ) : (
                            <CheckCircle2 className="h-3.5 w-3.5" />
                          )}
                          Approve
                        </Button>
                      )}
                      {selectedDraft.status === "approved" && (
                        <Button
                          size="sm"
                          className="h-9 flex-1 gap-1.5 text-xs"
                          onClick={() => void handlePublishDraft(selectedDraft)}
                          disabled={isPublishing === selectedDraft.id}
                        >
                          {isPublishing === selectedDraft.id ? (
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          ) : (
                            <Send className="h-3.5 w-3.5" />
                          )}
                          Post to LinkedIn
                        </Button>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </PageShell>
  );
}
