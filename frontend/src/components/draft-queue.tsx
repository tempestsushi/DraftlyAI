"use client";

import * as React from "react";

import { api, type Draft, type DraftImage, type DraftOptions, type DraftVersion } from "@/lib/api";

const DEFAULT_REGENERATE_OPTIONS: DraftOptions = {
  tone: "professional",
  length: "medium",
  include_cta: true,
  include_hashtags: true,
};

export function useDraftQueue() {
  const [drafts, setDrafts] = React.useState<Draft[]>([]);
  const [selectedDraft, setSelectedDraft] = React.useState<Draft | null>(null);
  const [draftVersions, setDraftVersions] = React.useState<DraftVersion[]>([]);
  const [draftImages, setDraftImages] = React.useState<DraftImage[]>([]);
  const [editing, setEditing] = React.useState<string | null>(null);
  const [editContent, setEditContent] = React.useState("");
  const [regenerateOptions, setRegenerateOptions] = React.useState<DraftOptions>(DEFAULT_REGENERATE_OPTIONS);
  const [isApproving, setIsApproving] = React.useState<string | null>(null);
  const [isRejecting, setIsRejecting] = React.useState<string | null>(null);
  const [isPublishing, setIsPublishing] = React.useState<string | null>(null);
  const [isRegenerating, setIsRegenerating] = React.useState<string | null>(null);
  const [regenerateError, setRegenerateError] = React.useState<string | null>(null);
  const [publishError, setPublishError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(true);

  const loadDrafts = React.useCallback(async () => {
    setLoading(true);
    const data = await api.listDrafts();
    setDrafts(data);
    setLoading(false);
  }, []);

  React.useEffect(() => {
    void loadDrafts();
  }, [loadDrafts]);

  React.useEffect(() => {
    if (!selectedDraft) {
      setDraftVersions([]);
      setDraftImages([]);
      return;
    }
    void api.listDraftVersions(selectedDraft.id).then(setDraftVersions);
    void api.listDraftImages(selectedDraft.id).then(setDraftImages);
  }, [selectedDraft?.id]);

  function selectDraft(draft: Draft) {
    setSelectedDraft(draft);
    setEditing(null);
    setEditContent("");
  }

  async function handleApprove(draft: Draft) {
    setIsApproving(draft.id);
    setPublishError(null);
    try {
      const updated = await api.updateDraft(draft.id, { status: "approved" });
      setSelectedDraft(updated);
      await loadDrafts();
    } finally {
      setIsApproving(null);
    }
  }

  async function handleReject(draft: Draft) {
    setIsRejecting(draft.id);
    setPublishError(null);
    try {
      const updated = await api.updateDraft(draft.id, { status: "rejected" });
      setSelectedDraft(updated);
      await loadDrafts();
    } finally {
      setIsRejecting(null);
    }
  }

  async function handleSaveEdit(draft: Draft) {
    const updated = await api.updateDraft(draft.id, {
      content: editContent,
      clear_linkedin_post: draft.status === "published",
    });
    setSelectedDraft(updated);
    setEditing(null);
    await loadDrafts();
    setDraftVersions(await api.listDraftVersions(draft.id));
  }

  async function handleRegenerateDraft(draft: Draft) {
    setIsRegenerating(draft.id);
    setRegenerateError(null);
    try {
      const updated = await api.regenerateDraft(draft.id, regenerateOptions);
      setSelectedDraft(updated);
      setEditing(null);
      setEditContent("");
      await loadDrafts();
      setDraftVersions(await api.listDraftVersions(draft.id));
    } catch (error) {
      setRegenerateError(error instanceof Error ? error.message : "Draft regeneration failed.");
    } finally {
      setIsRegenerating(null);
    }
  }

  async function handlePublishDraft(draft: Draft) {
    const confirmed = window.confirm("This will publish the draft publicly to LinkedIn. Continue?");
    if (!confirmed) {
      return;
    }
    setIsPublishing(draft.id);
    setPublishError(null);
    try {
      await api.publishDraft(draft.id);
      const updated = await api.getDraft(draft.id);
      setSelectedDraft(updated);
      await loadDrafts();
    } catch (error) {
      setPublishError(error instanceof Error ? error.message : "LinkedIn publishing failed.");
    } finally {
      setIsPublishing(null);
    }
  }

  function updateRegenerateOptions(patch: Partial<DraftOptions>) {
    setRegenerateOptions((current) => ({ ...current, ...patch }));
  }

  async function handleDeleteImage(draft: Draft) {
    await api.deleteDraftImage(draft.id);
    setDraftImages([]);
  }

  return {
    drafts,
    selectedDraft,
    setSelectedDraft: selectDraft,
    draftVersions,
    draftImages,
    editing,
    setEditing,
    editContent,
    setEditContent,
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
    pendingDrafts: drafts.filter((draft) => draft.status === "pending"),
    processedDrafts: drafts.filter((draft) => draft.status !== "pending"),
  };
}
