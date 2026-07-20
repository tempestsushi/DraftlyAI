"use client";

import * as React from "react";
import { Bot, Check, Link2, Loader2, Settings, Unlink } from "lucide-react";

import { PageShell } from "@/components/page-shell";
import { Button } from "@/components/ui/button";
import { api, type Integration, type LinkedInStatus } from "@/lib/api";
import {
  CHATBOT_TONE_OPTIONS,
  DEFAULT_CHATBOT_SETTINGS,
  loadChatbotSettings,
  saveChatbotSettings,
  type ChatbotSettings,
} from "@/lib/settings";
import { cn } from "@/lib/utils";

export function SettingsPage() {
  const [chatbotSettings, setChatbotSettings] = React.useState<ChatbotSettings>(DEFAULT_CHATBOT_SETTINGS);
  const [integrations, setIntegrations] = React.useState<Integration[]>([]);
  const [linkedInStatus, setLinkedInStatus] = React.useState<LinkedInStatus | null>(null);
  const [loadingIntegrations, setLoadingIntegrations] = React.useState(true);
  const [savingTone, setSavingTone] = React.useState(false);
  const [savingLinkedIn, setSavingLinkedIn] = React.useState(false);
  const [linkedInMessage, setLinkedInMessage] = React.useState("");

  React.useEffect(() => {
    setChatbotSettings(loadChatbotSettings());
    const params = new URLSearchParams(window.location.search);
    if (params.get("linkedin") === "connected") {
      setLinkedInMessage("LinkedIn connected successfully.");
    } else if (params.get("linkedin") === "error") {
      setLinkedInMessage(params.get("message") || "LinkedIn connection failed.");
    }
    void loadLinkedInConnection();
  }, []);

  const linkedIn = integrations.find((integration) => integration.type === "linkedin_publish") ?? null;
  const isLinked = linkedInStatus?.connected || linkedIn?.status === "connected";

  async function loadLinkedInConnection() {
    setLoadingIntegrations(true);
    try {
      const [nextIntegrations, status] = await Promise.all([
        api.listIntegrations(),
        api.getLinkedInStatus(),
      ]);
      setIntegrations(nextIntegrations);
      setLinkedInStatus(status);
    } finally {
      setLoadingIntegrations(false);
    }
  }

  function updateTone(tone: ChatbotSettings["tone"]) {
    const next = { ...chatbotSettings, tone };
    setChatbotSettings(next);
    setSavingTone(true);
    saveChatbotSettings(next);
    window.setTimeout(() => setSavingTone(false), 500);
  }

  async function updateLinkedInConnection(connect: boolean) {
    setSavingLinkedIn(true);
    setLinkedInMessage("");
    if (connect) {
      window.location.href = api.linkedInConnectUrl();
      return;
    }
    try {
      await api.disconnectLinkedIn();
      await loadLinkedInConnection();
      setLinkedInMessage("LinkedIn disconnected.");
    } finally {
      setSavingLinkedIn(false);
    }
  }

  return (
    <PageShell title="Settings">
      <div className="flex h-full flex-col gap-3">
        <div className="flex items-center gap-3 rounded-2xl border border-border bg-card px-4 py-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-primary/10">
            <Settings className="h-4 w-4 text-primary" />
          </div>
          <div>
            <h1 className="text-sm font-semibold">Settings</h1>
            <p className="text-xs text-muted-foreground">Tune the assistant and manage LinkedIn publishing</p>
          </div>
        </div>

        <div className="grid flex-1 gap-3 lg:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.8fr)]">
          <section className="rounded-2xl border border-border bg-card">
            <div className="flex items-center gap-2 border-b border-border px-4 py-3">
              <Bot className="h-4 w-4 text-primary" />
              <div>
                <h2 className="text-sm font-medium">Chatbot Tune</h2>
                <p className="text-xs text-muted-foreground">New answers will follow this response style.</p>
              </div>
              {savingTone && <span className="ml-auto text-xs text-muted-foreground">Saved</span>}
            </div>

            <div className="grid gap-2 p-4 md:grid-cols-2">
              {CHATBOT_TONE_OPTIONS.map((option) => {
                const active = chatbotSettings.tone === option.value;
                return (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => updateTone(option.value)}
                    className={cn(
                      "rounded-xl border p-4 text-left transition-colors",
                      active ? "border-primary/40 bg-primary/10" : "border-border bg-secondary/20 hover:bg-accent"
                    )}
                  >
                    <div className="mb-2 flex items-center gap-2">
                      <span className={cn("h-2 w-2 rounded-full", active ? "bg-primary" : "bg-muted-foreground/40")} />
                      <span className="text-sm font-medium">{option.label}</span>
                      {active && <Check className="ml-auto h-4 w-4 text-primary" />}
                    </div>
                    <p className="text-xs leading-5 text-muted-foreground">{option.description}</p>
                  </button>
                );
              })}
            </div>
          </section>

          <section className="rounded-2xl border border-border bg-card">
            <div className="flex items-center gap-2 border-b border-border px-4 py-3">
              <Link2 className="h-4 w-4 text-primary" />
              <div>
                <h2 className="text-sm font-medium">LinkedIn Connection</h2>
                <p className="text-xs text-muted-foreground">Use this for the publishing flow later.</p>
              </div>
            </div>

            <div className="space-y-4 p-4">
              <div className="rounded-xl border border-border bg-secondary/20 p-4">
                <div className="mb-2 flex items-center justify-between">
                  <span className="text-sm font-medium">LinkedIn Publish</span>
                  {loadingIntegrations ? (
                    <span className="h-6 w-20 rounded-full skeleton-shimmer" />
                  ) : (
                    <span
                      className={cn(
                        "rounded-full px-2 py-1 text-[11px]",
                        isLinked ? "bg-green-500/10 text-green-400" : "bg-muted text-muted-foreground"
                      )}
                    >
                      {isLinked ? "Connected" : "Not linked"}
                    </span>
                  )}
                </div>
                <p className="text-xs leading-5 text-muted-foreground">
                  Connect your LinkedIn account with OAuth so Draftly can publish approved posts when you choose.
                </p>
                {linkedInStatus?.connected && (
                  <div className="mt-3 flex items-center gap-3 border-t border-border pt-3">
                    {linkedInStatus.picture_url ? (
                      <img
                        src={linkedInStatus.picture_url}
                        alt=""
                        className="h-9 w-9 rounded-full object-cover"
                      />
                    ) : (
                      <div className="h-9 w-9 rounded-full bg-primary/10" />
                    )}
                    <div className="min-w-0">
                      <p className="truncate text-xs font-medium text-foreground">
                        {linkedInStatus.name || "LinkedIn account"}
                      </p>
                      {linkedInStatus.email && (
                        <p className="truncate text-[11px] text-muted-foreground">{linkedInStatus.email}</p>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {linkedInMessage && (
                <p className={cn("text-xs", linkedInMessage.includes("failed") ? "text-red-400" : "text-green-400")}>
                  {linkedInMessage}
                </p>
              )}

              <Button
                className="w-full rounded-xl"
                variant={isLinked ? "outline" : "default"}
                disabled={loadingIntegrations || savingLinkedIn}
                onClick={() => void updateLinkedInConnection(!isLinked)}
              >
                {savingLinkedIn ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : isLinked ? (
                  <Unlink className="mr-2 h-4 w-4" />
                ) : (
                  <Link2 className="mr-2 h-4 w-4" />
                )}
                {isLinked ? "Unlink LinkedIn" : "Link LinkedIn"}
              </Button>
            </div>
          </section>
        </div>
      </div>
    </PageShell>
  );
}
