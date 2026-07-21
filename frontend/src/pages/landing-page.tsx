import { ArrowDown, Bot, Database, Layers3 } from "lucide-react";

import { Button } from "@/components/ui/button";

type LandingPageProps = {
  onStartChat: () => void;
};

const implementationCards = [
  {
    title: "Gemini chat model",
    description:
      "Draftly answers conversationally first, then turns the useful answer into a LinkedIn-ready draft only when you ask for it.",
    icon: Bot,
  },
  {
    title: "Research pipeline",
    description:
      "For current or source-heavy questions, the backend searches, ranks pages, extracts useful content, and sends compact evidence to the model.",
    icon: Layers3,
  },
  {
    title: "Supabase persistence",
    description:
      "Chats, drafts, LinkedIn connection state, and draft images are stored so your work survives refreshes and app restarts.",
    icon: Database,
  },
];

export function LandingPage({ onStartChat }: LandingPageProps) {
  return (
    <div className="h-full overflow-y-auto bg-background">
      <section className="mx-auto flex min-h-screen w-full max-w-5xl flex-col items-center justify-center px-4 py-16 text-center">
        <div className="draftly-glow-pill mb-5">
          <h1 className="relative z-10 px-9 py-4 text-5xl font-semibold tracking-normal text-foreground sm:px-12 sm:text-6xl">
            Draftly AI
          </h1>
        </div>
        <h2 className="text-3xl font-semibold tracking-normal text-foreground">
          Research first. Draft after.
        </h2>
        <p className="mt-4 max-w-xl text-sm leading-7 text-muted-foreground sm:text-base">
          Ask about a topic, article, tool, or project. Draftly gives you a clear
          chat answer first, then helps you turn it into a polished LinkedIn post.
        </p>
        <button
          type="button"
          onClick={() => document.getElementById("draftly-model-section")?.scrollIntoView({ behavior: "smooth" })}
          className="mt-9 inline-flex h-10 w-10 items-center justify-center rounded-full border border-border bg-card text-muted-foreground transition hover:border-primary/50 hover:text-foreground"
          aria-label="See how Draftly works"
        >
          <ArrowDown className="h-4 w-4" />
        </button>
      </section>

      <section
        id="draftly-model-section"
        className="mx-auto flex min-h-screen w-full max-w-5xl flex-col justify-center px-4 py-16"
      >
        <div className="mb-7 max-w-2xl">
          <p className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
            How it is implemented
          </p>
          <h2 className="mt-3 text-3xl font-semibold tracking-normal text-foreground">
            A focused model workflow for useful LinkedIn drafts
          </h2>
          <p className="mt-3 text-sm leading-7 text-muted-foreground">
            The app is built as a backend-driven agent flow, not a direct
            frontend-to-model call. That keeps research, memory, draft creation,
            image storage, and LinkedIn controls in one reliable place.
          </p>
        </div>

        <div className="grid gap-3 md:grid-cols-3">
          {implementationCards.map((card) => {
            const Icon = card.icon;
            return (
              <article key={card.title} className="border border-border bg-card p-4">
                <div className="mb-4 flex h-9 w-9 items-center justify-center rounded-md bg-primary/10 text-primary">
                  <Icon className="h-4 w-4" />
                </div>
                <h3 className="text-sm font-semibold text-foreground">{card.title}</h3>
                <p className="mt-2 text-xs leading-6 text-muted-foreground">
                  {card.description}
                </p>
              </article>
            );
          })}
        </div>
      </section>

      <section className="mx-auto flex min-h-screen w-full max-w-5xl flex-col items-center justify-center px-4 py-16 text-center">
        <p className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
          Start
        </p>
        <h2 className="mt-3 max-w-2xl text-3xl font-semibold tracking-normal text-foreground">
          Ask the first question and build from the answer
        </h2>
        <p className="mt-4 max-w-xl text-sm leading-7 text-muted-foreground">
          Start with a topic you want to understand, a link you want explained,
          or an idea you want shaped into a post.
        </p>
        <Button className="mt-8 h-11 px-6" onClick={onStartChat}>
          Start chatting
        </Button>
      </section>
    </div>
  );
}
