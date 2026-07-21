export const ROUTES = {
  landing: "/",
  chat: "/chat",
  drafts: "/drafts",
  images: "/images",
  settings: "/settings",
} as const;

export type AppRoute = (typeof ROUTES)[keyof typeof ROUTES];

export function normalizeRoute(pathname: string): AppRoute {
  const cleanPath = pathname.replace(/\/+$/, "") || ROUTES.landing;
  if (cleanPath.startsWith(`${ROUTES.chat}/`)) {
    return ROUTES.chat;
  }
  switch (cleanPath) {
    case ROUTES.landing:
    case ROUTES.chat:
    case "/command-center":
    case ROUTES.drafts:
    case ROUTES.images:
    case ROUTES.settings:
      return cleanPath === "/command-center" ? ROUTES.chat : cleanPath;
    default:
      return ROUTES.landing;
  }
}

export function routeLabel(route: AppRoute): string {
  switch (route) {
    case ROUTES.landing:
      return "Home";
    case ROUTES.chat:
      return "New Chat";
    case ROUTES.drafts:
      return "Draft Queue";
    case ROUTES.images:
      return "Images";
    case ROUTES.settings:
      return "Settings";
  }
}
