"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { api, type Topic } from "@/lib/api";
import { ROUTES, type AppRoute } from "@/lib/routes";
import {
  LayoutDashboard,
  FileText,
  Settings,
  Image as ImageIcon,
  Home,
  MessageSquare,
  Loader2,
  Trash2,
} from "lucide-react";

const NAV_ITEMS = [
  { id: ROUTES.landing, label: "Home", icon: Home },
  { id: ROUTES.chat, label: "New Chat", icon: LayoutDashboard },
  { id: ROUTES.drafts, label: "Draft Queue", icon: FileText },
  { id: ROUTES.images, label: "Images", icon: ImageIcon },
  { id: ROUTES.settings, label: "Settings", icon: Settings },
];

function timeAgo(dateStr: string) {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

interface SidebarProps {
  activeRoute: AppRoute;
  onNavigate: (route: AppRoute) => void;
  activeTopicId: string | null;
  topicsVersion: number;
  onSelectTopic: (id: string) => void;
  onDeleteTopic: (id: string) => void;
  onNewChat: () => void;
}

export function Sidebar({
  activeRoute,
  onNavigate,
  activeTopicId,
  topicsVersion,
  onSelectTopic,
  onDeleteTopic,
  onNewChat,
}: SidebarProps) {
  const [topics, setTopics] = React.useState<Topic[]>([]);
  const [loadingTopics, setLoadingTopics] = React.useState(true);
  const [deletingTopicId, setDeletingTopicId] = React.useState<string | null>(
    null,
  );

  React.useEffect(() => {
    void fetchTopics();
  }, [topicsVersion]);

  async function fetchTopics() {
    const data = await api.listTopics();
    setTopics(data);
    setLoadingTopics(false);
  }

  async function handleDeleteTopic(topicId: string) {
    setDeletingTopicId(topicId);
    try {
      await api.deleteTopic(topicId);
      setTopics((current) => current.filter((topic) => topic.id !== topicId));
      onDeleteTopic(topicId);
    } finally {
      setDeletingTopicId(null);
    }
  }

  const statusDot: Record<string, string> = {
    complete: "bg-green-500",
    searching: "bg-amber-400 animate-pulse",
    drafting: "bg-blue-400 animate-pulse",
    review: "bg-emerald-400",
    pending: "bg-muted-foreground/40",
    error: "bg-red-500",
  };

  return (
    <>
      {/* ── Desktop sidebar ── */}
      <aside className="fixed left-0 top-0 z-40 hidden h-screen w-56 flex-col border-r border-border bg-card lg:flex">
        {/* Brand */}
        <div className="flex h-12 shrink-0 items-center gap-2.5 border-b border-border px-4">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary/10">
            <FileText className="h-3.5 w-3.5 text-primary" />
          </div>
          <span className="font-semibold text-sm">Draftly</span>
          <span className="ml-auto h-1.5 w-1.5 rounded-full bg-green-500" />
        </div>

        {/* Nav */}
        <div className="shrink-0 space-y-0.5 p-2">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = activeRoute === item.id && activeTopicId === null;
            return (
              <Button
                key={item.id}
                variant="ghost"
                className={cn(
                  "w-full justify-start gap-2.5 rounded-xl h-8 px-2.5 text-xs font-medium transition-all",
                  isActive
                    ? "bg-primary/10 text-primary hover:bg-primary/15"
                    : "text-muted-foreground hover:bg-accent hover:text-foreground",
                )}
                onClick={() => {
                  onNavigate(item.id);
                  if (item.id === ROUTES.chat) onNewChat();
                }}
              >
                <Icon className="h-3.5 w-3.5 shrink-0" />
                {item.label}
              </Button>
            );
          })}
        </div>

        <div className="mx-3 my-1 border-t border-border" />

        {/* Previous Chats */}
        <div className="flex flex-1 flex-col overflow-hidden">
          <div className="shrink-0 px-4 pb-1.5">
            <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground/60">
              Recent Chats
            </span>
          </div>

          <ScrollArea className="flex-1 px-2">
            {loadingTopics ? (
              <div className="flex items-center justify-center py-6">
                <Loader2 className="h-4 w-4 animate-spin text-muted-foreground/40" />
              </div>
            ) : topics.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 text-center">
                <MessageSquare className="h-6 w-6 text-muted-foreground/20 mb-2" />
                <p className="text-[11px] text-muted-foreground/50">
                  No chats yet
                </p>
              </div>
            ) : (
              <div className="space-y-0.5 pb-4">
                {topics.map((topic) => {
                  const isSelected =
                    activeTopicId === topic.id &&
                    activeRoute === ROUTES.chat;
                  return (
                    <div
                      key={topic.id}
                      className={cn(
                        "group flex items-start gap-2 rounded-xl border px-2 py-2 transition-all",
                        isSelected
                          ? "bg-primary/10 border-primary/20"
                          : "border-transparent hover:bg-accent",
                      )}
                    >
                      <button
                        type="button"
                        onClick={() => {
                          onSelectTopic(topic.id);
                        }}
                        className="flex min-w-0 flex-1 items-start gap-2 text-left"
                      >
                        <span
                          className={cn(
                            "mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full",
                            statusDot[topic.status] || "bg-muted-foreground/40",
                          )}
                        />
                        <div className="flex-1 min-w-0">
                          <p
                            className={cn(
                              "text-xs font-medium leading-snug line-clamp-2",
                              isSelected
                                ? "text-primary"
                                : "text-foreground/80 group-hover:text-foreground",
                            )}
                          >
                            {topic.topic}
                          </p>
                          <p className="mt-0.5 font-mono text-[10px] text-muted-foreground/50">
                            {timeAgo(topic.created_at)}
                          </p>
                        </div>
                      </button>
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7 shrink-0 rounded-lg text-muted-foreground opacity-0 transition-opacity hover:text-destructive group-hover:opacity-100 focus-visible:opacity-100"
                        disabled={deletingTopicId === topic.id}
                        onClick={() => void handleDeleteTopic(topic.id)}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  );
                })}
              </div>
            )}
          </ScrollArea>
        </div>
      </aside>

      {/* ── Mobile bottom nav ── */}
      <nav className="fixed bottom-0 left-0 right-0 z-50 flex h-14 items-center justify-around border-t border-border bg-card lg:hidden">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = activeRoute === item.id;
          return (
            <Button
              key={item.id}
              variant="ghost"
              className={cn(
                "flex flex-col items-center gap-1 h-auto py-1.5 px-3",
                isActive ? "text-primary" : "text-muted-foreground",
              )}
              onClick={() => {
                onNavigate(item.id);
                if (item.id === ROUTES.chat) onNewChat();
              }}
            >
              <Icon className="h-5 w-5" />
            </Button>
          );
        })}
      </nav>
    </>
  );
}
