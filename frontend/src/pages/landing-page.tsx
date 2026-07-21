import { ArrowRight, Bot, Database, Layers3 } from "lucide-react";

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
      <header className="fixed left-0 right-0 top-0 z-30 border-b border-border/70 bg-background/85 backdrop-blur">
        <div className="mx-auto flex h-14 w-full max-w-6xl items-center justify-between px-4">
          <button
            type="button"
            onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
            className="flex items-center gap-2 text-sm font-semibold text-foreground"
          >
            <span className="flex h-7 w-7 items-center justify-center rounded-md bg-primary/10 text-primary">
              D
            </span>
            Draftly
          </button>
          <nav className="hidden items-center gap-6 text-xs text-muted-foreground sm:flex">
            <button
              type="button"
              onClick={() => document.getElementById("draftly-workflow")?.scrollIntoView({ behavior: "smooth" })}
              className="transition hover:text-foreground"
            >
              Workflow
            </button>
            <button
              type="button"
              onClick={() => document.getElementById("draftly-start")?.scrollIntoView({ behavior: "smooth" })}
              className="transition hover:text-foreground"
            >
              Start
            </button>
          </nav>
          <Button size="sm" className="h-8 px-3 text-xs" onClick={onStartChat}>
            Open chat
          </Button>
        </div>
      </header>

      <section className="mx-auto flex min-h-screen w-full max-w-6xl flex-col items-center justify-center px-4 pb-16 pt-24 text-center">
        <p className="mb-5 rounded-full border border-border bg-card px-3 py-1 font-mono text-xs uppercase tracking-wider text-muted-foreground">
          Chat-to-LinkedIn drafting workspace
        </p>
        <h1 className="max-w-5xl text-5xl font-semibold tracking-normal text-foreground sm:text-7xl lg:text-8xl">
          Research ideas and turn them into posts.
        </h1>
        <p className="mt-6 max-w-2xl text-base leading-8 text-muted-foreground sm:text-lg">
          Draftly answers your topic first like a chat assistant, then helps you
          create, edit, attach images, and publish LinkedIn drafts from the best answer.
        </p>
        <div className="mt-9 flex flex-col items-center gap-3 sm:flex-row">
          <Button size="lg" className="h-12 gap-2 px-6" onClick={onStartChat}>
            Start with chat
            <ArrowRight className="h-4 w-4" />
          </Button>
          <Button
            size="lg"
            variant="outline"
            className="h-12 px-6"
            onClick={() => document.getElementById("draftly-workflow")?.scrollIntoView({ behavior: "smooth" })}
          >
            See how it works
          </Button>
        </div>
      </section>

      <section
        id="draftly-workflow"
        className="mx-auto flex min-h-screen w-full max-w-6xl flex-col justify-center px-4 py-20"
      >
        <div className="mb-8 max-w-2xl">
          <p className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
            How it is implemented
          </p>
          <h2 className="mt-3 text-4xl font-semibold tracking-normal text-foreground">
            A focused model workflow for useful LinkedIn drafts
          </h2>
          <p className="mt-3 text-sm leading-7 text-muted-foreground">
            The app is built as a backend-driven agent flow, not a direct
            frontend-to-model call. That keeps research, memory, draft creation,
            image storage, and LinkedIn controls in one reliable place.
          </p>
        </div>

        <div className="grid gap-px overflow-hidden border border-border bg-border md:grid-cols-3">
          {implementationCards.map((card) => {
            const Icon = card.icon;
            return (
              <article key={card.title} className="bg-card p-5">
                <div className="mb-5 flex h-10 w-10 items-center justify-center rounded-md bg-primary/10 text-primary">
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

      <section
        id="draftly-start"
        className="mx-auto flex min-h-screen w-full max-w-6xl flex-col items-center justify-center px-4 py-20 text-center"
      >
        <p className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
          Start
        </p>
        <h2 className="mt-3 max-w-3xl text-4xl font-semibold tracking-normal text-foreground sm:text-5xl">
          Ask the first question and build from the answer
        </h2>
        <p className="mt-4 max-w-xl text-sm leading-7 text-muted-foreground">
          Start with a topic you want to understand, a link you want explained,
          or an idea you want shaped into a post.
        </p>
        <Button className="mt-8 h-12 gap-2 px-6" onClick={onStartChat}>
          Start chatting
          <ArrowRight className="h-4 w-4" />
        </Button>
      </section>
    </div>
  );
}
