"use client";

import * as React from "react";
import {
  ArrowLeft,
  CheckCircle2,
  Clock,
  ExternalLink,
  FileText,
  Image as ImageIcon,
  Link2,
  Loader2,
  Wand2,
  Trash2,
} from "lucide-react";

import { PageShell } from "@/components/page-shell";
import { Button } from "@/components/ui/button";
import { api, type Draft, type DraftImage, type ImageResult, type ImageUseCase, type Topic } from "@/lib/api";
import { ROUTES } from "@/lib/routes";
import { cn } from "@/lib/utils";

function draftIdFromUrl() {
  return new URLSearchParams(window.location.search).get("draft");
}

function navigateTo(url: string) {
  window.history.pushState({}, "", url);
  window.dispatchEvent(new Event("popstate"));
}

function setDraftUrl(draftId: string) {
  window.history.replaceState({}, "", `${ROUTES.images}?draft=${encodeURIComponent(draftId)}`);
}

function buildImageQuery(draft: Draft, topic: Topic | null) {
  const base = topic?.topic || draft.title || draft.content;
  const cleaned = base
    .replace(/[^\w\s+#.-]/g, " ")
    .split(/\s+/)
    .filter((word) => word.length > 2)
    .slice(0, 12)
    .join(" ");
  return `${cleaned} professional visual illustration`.trim();
}

const IMAGE_USE_CASE_OPTIONS: Array<{ value: ImageUseCase; label: string }> = [
  { value: "linkedin_post_illustration", label: "LinkedIn illustration" },
  { value: "blog_hero", label: "Blog hero" },
  { value: "technical_concept", label: "Technical concept" },
  { value: "abstract_topic", label: "Abstract topic" },
  { value: "product_mockup", label: "Product/mockup visual" },
];

export function ImagesPage() {
  const draftId = draftIdFromUrl();
  const [drafts, setDrafts] = React.useState<Draft[]>([]);
  const [draft, setDraft] = React.useState<Draft | null>(null);
  const [topic, setTopic] = React.useState<Topic | null>(null);
  const [selectedImages, setSelectedImages] = React.useState<DraftImage[]>([]);
  const [query, setQuery] = React.useState("");
  const [useCase, setUseCase] = React.useState<ImageUseCase>("linkedin_post_illustration");
  const [results, setResults] = React.useState<ImageResult[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [loadingDrafts, setLoadingDrafts] = React.useState(true);
  const [searching, setSearching] = React.useState(false);
  const [savingUrl, setSavingUrl] = React.useState<string | null>(null);
  const [error, setError] = React.useState("");
  const [lastSearchQuery, setLastSearchQuery] = React.useState("");
  const [searchPage, setSearchPage] = React.useState(0);
  const [searchSets, setSearchSets] = React.useState<Record<string, ImageResult[][]>>({});

  React.useEffect(() => {
    void loadDrafts();
  }, []);

  React.useEffect(() => {
    if (!draftId) {
      setLoading(false);
      return;
    }
    void loadDraftContext(draftId);
  }, [draftId]);

  async function loadDrafts() {
    setLoadingDrafts(true);
    try {
      const loadedDrafts = await api.listDrafts();
      setDrafts(loadedDrafts);
      if (!draftId && loadedDrafts.length > 0) {
        await selectDraft(loadedDrafts[0], { updateUrl: true });
      }
    } finally {
      setLoadingDrafts(false);
    }
  }

  async function selectDraft(nextDraft: Draft, options: { updateUrl?: boolean } = {}) {
    if (options.updateUrl) {
      setDraftUrl(nextDraft.id);
    }
    setResults([]);
    setLastSearchQuery("");
    setSearchPage(0);
    setSearchSets({});
    await loadDraftContext(nextDraft.id);
  }

  async function loadDraftContext(id: string) {
    setLoading(true);
    setError("");
    try {
      const loadedDraft = await api.getDraft(id);
      const [loadedImages, loadedTopic] = await Promise.all([
        api.listDraftImages(id),
        loadedDraft.topic_id ? api.getTopic(loadedDraft.topic_id).catch(() => null) : Promise.resolve(null),
      ]);
      setDraft(loadedDraft);
      setSelectedImages(loadedImages);
      setTopic(loadedTopic);
      setQuery(buildImageQuery(loadedDraft, loadedTopic));
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Could not load draft image picker.");
    } finally {
      setLoading(false);
    }
  }

  function generationKey(prompt: string, selectedUseCase: ImageUseCase) {
    return `${selectedUseCase}:${prompt}`;
  }

  async function loadImageSet(searchQuery: string, page: number) {
    const key = generationKey(searchQuery, useCase);
    const cached = searchSets[key]?.[page];
    if (cached) {
      setResults(cached);
      setLastSearchQuery(searchQuery);
      setSearchPage(page);
      return;
    }

    const nextResults = await api.generateImages(searchQuery, useCase, 1);
    setSearchSets((current) => {
      const querySets = [...(current[key] ?? [])];
      querySets[page] = nextResults;
      return { ...current, [key]: querySets };
    });
    setResults(nextResults);
    setLastSearchQuery(searchQuery);
    setSearchPage(page);
  }

  async function handleSearch() {
    const searchQuery = query.trim();
    if (!searchQuery) return;
    const nextPage = searchQuery === lastSearchQuery ? searchPage + 1 : 0;
    setSearching(true);
    setError("");
    try {
      await loadImageSet(searchQuery, nextPage);
    } catch (searchError) {
      setError(searchError instanceof Error ? searchError.message : "Image generation failed.");
    } finally {
      setSearching(false);
    }
  }

  async function handleMoveSet(direction: -1 | 1) {
    const searchQuery = lastSearchQuery || query.trim();
    if (!searchQuery) return;
    const nextPage = Math.max(0, searchPage + direction);
    if (nextPage === searchPage) return;
    setSearching(true);
    setError("");
    try {
      await loadImageSet(searchQuery, nextPage);
    } catch (searchError) {
      setError(searchError instanceof Error ? searchError.message : "Image generation failed.");
    } finally {
      setSearching(false);
    }
  }

  async function handleUseImage(image: ImageResult) {
    if (!draft) return;
    setSavingUrl(image.image_url);
    setError("");
    try {
      const saved = await api.saveDraftImage(draft.id, image);
      setSelectedImages((current) =>
        current.some((item) => item.id === saved.id || item.image_url === saved.image_url)
          ? current
          : [...current, saved],
      );
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Could not save selected image.");
    } finally {
      setSavingUrl(null);
    }
  }

  async function handleRemoveImage(imageId: string) {
    if (!draft) return;
    await api.deleteDraftImageById(draft.id, imageId);
    setSelectedImages((current) => current.filter((image) => image.id !== imageId));
  }

  const headerAction = (
    <Button
      size="sm"
      variant="ghost"
      className="h-8 gap-1.5 text-xs"
      onClick={() => navigateTo(ROUTES.drafts)}
    >
      <ArrowLeft className="h-3.5 w-3.5" />
      Drafts
    </Button>
  );

  const pendingDrafts = drafts.filter((item) => item.status === "pending");
  const processedDrafts = drafts.filter((item) => item.status !== "pending");

  return (
    <PageShell title="Image Picker" headerAction={headerAction} flush>
      <div className="flex h-full flex-col lg:flex-row">
        <div className="flex min-h-[270px] w-full flex-col overflow-hidden border-b border-border bg-card lg:min-h-0 lg:w-64 lg:border-b-0 lg:border-r xl:w-72">
          <div className="border-b border-border px-4 py-2.5">
            <span className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
              Pending
            </span>
          </div>

          <div className="flex-1 overflow-y-auto">
            {loadingDrafts ? (
              <div className="flex items-center justify-center p-8">
                <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
              </div>
            ) : pendingDrafts.length === 0 ? (
              <div className="flex flex-col items-center justify-center p-8 text-center">
                <FileText className="mb-2 h-8 w-8 text-muted-foreground/30" />
                <p className="text-xs text-muted-foreground">No pending drafts</p>
              </div>
            ) : (
              <div className="space-y-1.5 p-2">
                {pendingDrafts.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => void selectDraft(item, { updateUrl: true })}
                    className={cn(
                      "group w-full border px-2.5 py-2.5 text-left transition-all",
                      draft?.id === item.id
                        ? "border-primary/30 bg-primary/10"
                        : "border-transparent hover:bg-accent",
                    )}
                  >
                    <p className="mb-1.5 line-clamp-2 text-xs font-medium leading-snug text-foreground/85 group-hover:text-foreground">
                      {item.content.split("\n")[0]}
                    </p>
                    <div className="flex items-center gap-1.5">
                      <span className="bg-secondary px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
                        {item.source_message_id ? "Chat answer" : "Research"}
                      </span>
                      <span className="flex items-center gap-1 text-[10px] text-muted-foreground">
                        <Clock className="h-2.5 w-2.5" />
                        {new Date(item.created_at).toLocaleDateString()}
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
              <div className="max-h-48 space-y-1.5 overflow-y-auto p-2">
                {processedDrafts.slice(0, 5).map((item) => (
                  <button
                    key={item.id}
                    onClick={() => void selectDraft(item, { updateUrl: true })}
                    className={cn(
                      "w-full border px-3 py-2 text-left transition-all",
                      draft?.id === item.id
                        ? "border-primary/30 bg-primary/10"
                        : "border-transparent hover:bg-accent",
                    )}
                  >
                    <p className="line-clamp-1 text-xs text-muted-foreground">
                      {item.content.split("\n")[0]}
                    </p>
                  </button>
                ))}
              </div>
            </>
          )}
        </div>

        <div className="flex min-h-[420px] flex-1 flex-col overflow-y-auto bg-background p-4 lg:p-5">
          {loading ? (
            <div className="flex flex-1 items-center justify-center">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          ) : !draft ? (
            <div className="flex flex-1 flex-col items-center justify-center text-center">
              <ImageIcon className="mb-3 h-8 w-8 text-muted-foreground/30" />
              <p className="text-sm text-muted-foreground">Select a draft to choose an image.</p>
            </div>
          ) : (
            <div className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-4">
          <div className="border border-border bg-card p-4">
            <div className="mb-3 flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
              <div className="min-w-0">
                <p className="text-sm font-medium text-foreground">Generate image for draft</p>
                <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">
                  {topic?.topic || draft.content.split("\n")[0]}
                </p>
              </div>
              {selectedImages.length > 0 && (
                <span className="inline-flex items-center gap-1.5 bg-primary/10 px-2 py-1 text-[11px] text-primary">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  {selectedImages.length} selected
                </span>
              )}
            </div>

            {selectedImages.length > 0 && (
              <div className="mb-4 border border-border bg-background/50 p-3">
                <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                  {selectedImages.map((image) => (
                    <div key={image.id} className="flex gap-2">
                      <img
                        src={image.thumbnail_url ?? image.image_url}
                        alt={image.title}
                        className="h-20 w-28 shrink-0 object-cover"
                      />
                      <div className="min-w-0 flex-1">
                        <p className="line-clamp-2 text-xs font-medium">{image.title}</p>
                        <a
                          href={image.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="mt-1 inline-flex items-center gap-1 text-[11px] text-primary hover:underline"
                        >
                          <Link2 className="h-3 w-3" />
                  {image.source_domain ?? "Generated image"}
                        </a>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="mt-1 h-7 gap-1.5 px-1 text-[11px] text-muted-foreground"
                          onClick={() => void handleRemoveImage(image.id)}
                        >
                          <Trash2 className="h-3 w-3" />
                          Remove
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="grid gap-2 lg:grid-cols-[minmax(0,1fr)_220px_auto]">
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") void handleSearch();
                }}
                className="h-10 flex-1 border border-border bg-background px-3 text-sm outline-none focus:ring-1 focus:ring-primary/50"
                placeholder="Describe the image you want to generate..."
              />
              <select
                value={useCase}
                onChange={(event) => {
                  setUseCase(event.target.value as ImageUseCase);
                  setResults([]);
                  setLastSearchQuery("");
                  setSearchPage(0);
                }}
                className="h-10 border border-border bg-background px-3 text-sm text-foreground outline-none focus:ring-1 focus:ring-primary/50"
              >
                {IMAGE_USE_CASE_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <Button className="h-10 gap-1.5 text-sm" onClick={() => void handleSearch()} disabled={searching}>
                {searching ? <Loader2 className="h-4 w-4 animate-spin" /> : <Wand2 className="h-4 w-4" />}
                {query.trim() && query.trim() === lastSearchQuery ? "Regenerate image" : "Generate image"}
              </Button>
            </div>

            {lastSearchQuery && (
              <div className="mt-2 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-[11px] text-muted-foreground">
                  Showing generated image {searchPage + 1}. Regenerate to create a different image.
                </p>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="ghost"
                    className="h-8 gap-1.5 text-xs"
                    disabled={searchPage === 0 || searching}
                    onClick={() => void handleMoveSet(-1)}
                  >
                    Previous set
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    className="h-8 gap-1.5 text-xs"
                    disabled={searching}
                    onClick={() => void handleMoveSet(1)}
                  >
                    Next set
                  </Button>
                </div>
              </div>
            )}

            {error && <p className="mt-2 text-xs text-red-400">{error}</p>}
          </div>

          {results.length === 0 ? (
            <div className="flex flex-1 flex-col items-center justify-center border border-border bg-card p-10 text-center">
              <ImageIcon className="mb-3 h-9 w-9 text-muted-foreground/25" />
              <p className="text-sm text-muted-foreground">Generate an image for this draft.</p>
            </div>
          ) : (
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              {results.map((image) => {
                const selectedMatch = selectedImages.find((item) => item.image_url === image.image_url);
                const isSelected = Boolean(selectedMatch);
                return (
                  <div key={image.image_url} className="overflow-hidden border border-border bg-card">
                    <img
                      src={image.thumbnail_url ?? image.image_url}
                      alt={image.title}
                      className="aspect-video w-full object-cover"
                      loading="lazy"
                    />
                    <div className="space-y-3 p-3">
                      <p className="line-clamp-2 text-xs font-medium leading-5">{image.title}</p>
                      <div className="flex items-center justify-between gap-2">
                        <a
                          href={image.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex min-w-0 items-center gap-1 truncate text-[11px] text-primary hover:underline"
                        >
                          <ExternalLink className="h-3 w-3 shrink-0" />
                          <span className="truncate">{image.source_domain ?? "source"}</span>
                        </a>
                        <Button
                          size="sm"
                          className="h-8 shrink-0 px-3 text-xs"
                          variant={isSelected ? "secondary" : "default"}
                          onClick={() =>
                            selectedMatch
                              ? void handleRemoveImage(selectedMatch.id)
                              : void handleUseImage(image)
                          }
                          disabled={savingUrl === image.image_url}
                        >
                          {savingUrl === image.image_url ? (
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          ) : isSelected ? (
                            "Remove"
                          ) : (
                            "Add"
                          )}
                        </Button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
            </div>
          )}
        </div>
      </div>
    </PageShell>
  );
}
