"use client";

import * as React from "react";
import { Sidebar } from "@/components/sidebar";
import { ROUTES, normalizeRoute, type AppRoute } from "@/lib/routes";

const ChatPage = React.lazy(() =>
  import("@/pages/chat-page").then((module) => ({ default: module.ChatPage }))
);
const LandingPage = React.lazy(() =>
  import("@/pages/landing-page").then((module) => ({ default: module.LandingPage }))
);
const DraftsPage = React.lazy(() =>
  import("@/pages/drafts-page").then((module) => ({ default: module.DraftsPage }))
);
const ImagesPage = React.lazy(() =>
  import("@/pages/images-page").then((module) => ({ default: module.ImagesPage }))
);
const SettingsPage = React.lazy(() =>
  import("@/pages/settings-page").then((module) => ({ default: module.SettingsPage }))
);

function topicIdFromUrl() {
  if (normalizeRoute(window.location.pathname) !== ROUTES.chat) {
    return null;
  }
  const pathParts = window.location.pathname.replace(/\/+$/, "").split("/").filter(Boolean);
  if (pathParts[0] === "chat" && pathParts[1]) {
    return decodeURIComponent(pathParts[1]);
  }
  return new URLSearchParams(window.location.search).get("chat");
}

function chatUrl(topicId?: string | null) {
  return topicId ? `${ROUTES.chat}/${encodeURIComponent(topicId)}` : ROUTES.chat;
}

function normalizeBrowserUrl() {
  if (window.location.pathname.replace(/\/+$/, "") !== "/command-center") {
    if (window.location.pathname.replace(/\/+$/, "") === ROUTES.chat) {
      const queryTopicId = new URLSearchParams(window.location.search).get("chat");
      if (queryTopicId) {
        window.history.replaceState({}, "", chatUrl(queryTopicId));
      }
    }
    return;
  }
  const queryTopicId = new URLSearchParams(window.location.search).get("chat");
  window.history.replaceState({}, "", chatUrl(queryTopicId));
}

function PageFallback() {
  return (
    <div className="flex flex-1 flex-col gap-4 p-4 lg:p-5">
      <div className="h-12 rounded-2xl border border-border bg-card/70 skeleton-shimmer" />
      <div className="grid flex-1 gap-3 lg:grid-cols-[280px_minmax(0,1fr)]">
        <div className="rounded-2xl border border-border bg-card/70 skeleton-shimmer" />
        <div className="rounded-2xl border border-border bg-card/70 skeleton-shimmer" />
      </div>
    </div>
  );
}

export default function App() {
  const [activeRoute, setActiveRoute] = React.useState<AppRoute>(() =>
    normalizeRoute(window.location.pathname)
  );
  const [activeTopicId, setActiveTopicId] = React.useState<string | null>(() => topicIdFromUrl());
  const [shouldLoadActiveTopic, setShouldLoadActiveTopic] = React.useState(() => Boolean(topicIdFromUrl()));
  const [topicsVersion, setTopicsVersion] = React.useState(0);

  React.useEffect(() => {
    normalizeBrowserUrl();
  }, []);

  React.useEffect(() => {
    const handlePopState = () => {
      normalizeBrowserUrl();
      const nextRoute = normalizeRoute(window.location.pathname);
      const nextTopicId = topicIdFromUrl();
      setActiveRoute(nextRoute);
      setActiveTopicId(nextTopicId);
      setShouldLoadActiveTopic(Boolean(nextTopicId));
    };
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  function navigate(route: AppRoute) {
    if (window.location.pathname !== route) {
      window.history.pushState({}, "", route);
    }
    setActiveRoute(route);
  }

  function handleSelectTopic(id: string) {
    setActiveTopicId(id);
    setShouldLoadActiveTopic(true);
    const nextUrl = chatUrl(id);
    if (`${window.location.pathname}${window.location.search}` !== nextUrl) {
      window.history.pushState({}, "", nextUrl);
    }
    setActiveRoute(ROUTES.chat);
  }

  function handleNewChat() {
    setActiveTopicId(null);
    setShouldLoadActiveTopic(false);
    navigate(ROUTES.chat);
  }

  function handleTopicCreated(id: string | null) {
    setActiveTopicId(id);
    setShouldLoadActiveTopic(Boolean(id));
    if (id && activeRoute === ROUTES.chat) {
      const nextUrl = chatUrl(id);
      if (`${window.location.pathname}${window.location.search}` !== nextUrl) {
        window.history.replaceState({}, "", nextUrl);
      }
    }
  }

  function refreshTopics() {
    setTopicsVersion((current) => current + 1);
  }

  function handleDeleteTopic(topicId: string) {
    if (activeTopicId === topicId) {
      setActiveTopicId(null);
      setShouldLoadActiveTopic(false);
      navigate(ROUTES.chat);
    }
    refreshTopics();
  }

  const renderView = () => {
    switch (activeRoute) {
      case ROUTES.landing:
        return <LandingPage onStartChat={handleNewChat} />;
      case ROUTES.chat:
        return (
          <ChatPage
            topicId={activeTopicId}
            shouldLoadTopic={shouldLoadActiveTopic}
            onTopicCreated={handleTopicCreated}
            onTopicActivity={refreshTopics}
          />
        );
      case ROUTES.drafts:
        return <DraftsPage />;
      case ROUTES.images:
        return <ImagesPage />;
      case ROUTES.settings:
        return <SettingsPage />;
      default:
        return <LandingPage onStartChat={handleNewChat} />;
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar
        activeRoute={activeRoute}
        onNavigate={navigate}
        activeTopicId={activeTopicId}
        topicsVersion={topicsVersion}
        onSelectTopic={handleSelectTopic}
        onDeleteTopic={handleDeleteTopic}
        onNewChat={handleNewChat}
      />

      <main className="flex flex-1 flex-col pb-14 lg:pb-0 lg:pl-56">
        <React.Suspense fallback={<PageFallback />}>{renderView()}</React.Suspense>
      </main>
    </div>
  );
}
