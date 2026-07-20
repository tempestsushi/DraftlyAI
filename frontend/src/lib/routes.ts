export const ROUTES = {
  commandCenter: "/chat",
  drafts: "/drafts",
  images: "/images",
  settings: "/settings",
} as const;

export type AppRoute = (typeof ROUTES)[keyof typeof ROUTES];

export function normalizeRoute(pathname: string): AppRoute {
  const cleanPath = pathname.replace(/\/+$/, "") || ROUTES.commandCenter;
  switch (cleanPath) {
    case ROUTES.commandCenter:
    case "/command-center":
    case ROUTES.drafts:
    case ROUTES.images:
    case ROUTES.settings:
      return cleanPath === "/command-center" ? ROUTES.commandCenter : cleanPath;
    default:
      return ROUTES.commandCenter;
  }
}

export function routeLabel(route: AppRoute): string {
  switch (route) {
    case ROUTES.commandCenter:
      return "New Chat";
    case ROUTES.drafts:
      return "Draft Queue";
    case ROUTES.images:
      return "Images";
    case ROUTES.settings:
      return "Settings";
  }
}
