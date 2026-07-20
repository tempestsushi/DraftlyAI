"use client";

import * as React from "react";
import { Sidebar } from "@/components/sidebar";
import { ROUTES, normalizeRoute, type AppRoute } from "@/lib/routes";

const CommandCenterPage = React.lazy(() =>
  import("@/pages/command-center").then((module) => ({ default: module.CommandCenterPage }))
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
  if (normalizeRoute(window.location.pathname) !== ROUTES.commandCenter) {
    return null;
  }
  return new URLSearchParams(window.location.search).get("chat");
}

function commandCenterUrl(topicId?: string | null) {
  return topicId ? `${ROUTES.commandCenter}?chat=${encodeURIComponent(topicId)}` : ROUTES.commandCenter;
}

function normalizeBrowserUrl() {
  if (window.location.pathname.replace(/\/+$/, "") !== "/command-center") {
    return;
  }
  window.history.replaceState({}, "", `${ROUTES.commandCenter}${window.location.search}`);
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
    const nextUrl = commandCenterUrl(id);
    if (`${window.location.pathname}${window.location.search}` !== nextUrl) {
      window.history.pushState({}, "", nextUrl);
    }
    setActiveRoute(ROUTES.commandCenter);
  }

  function handleNewChat() {
    setActiveTopicId(null);
    setShouldLoadActiveTopic(false);
    navigate(ROUTES.commandCenter);
  }

  function handleTopicCreated(id: string | null) {
    setActiveTopicId(id);
    setShouldLoadActiveTopic(Boolean(id));
    if (id && activeRoute === ROUTES.commandCenter) {
      const nextUrl = commandCenterUrl(id);
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
      navigate(ROUTES.commandCenter);
    }
    refreshTopics();
  }

  const renderView = () => {
    switch (activeRoute) {
      case ROUTES.commandCenter:
        return (
          <CommandCenterPage
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
        return (
          <CommandCenterPage
            topicId={null}
            shouldLoadTopic={false}
            onTopicCreated={handleTopicCreated}
            onTopicActivity={refreshTopics}
          />
        );
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
