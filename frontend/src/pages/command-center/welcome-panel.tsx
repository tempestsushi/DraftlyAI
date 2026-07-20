export function WelcomePanel() {
  return (
    <div className="bubble-in flex min-h-[42vh] flex-col items-center justify-center text-center">
      <div className="draftly-glow-pill mb-5">
        <h1 className="relative z-10 px-10 py-4 text-5xl font-semibold tracking-normal text-foreground sm:text-6xl">
          Draftly AI
        </h1>
      </div>
      <h2 className="text-3xl font-semibold tracking-normal text-foreground">
        How can I help?
      </h2>
      <p className="mt-3 max-w-md text-sm leading-7 text-muted-foreground">
        Ask about a topic or tool. I&apos;ll answer first, and you can create a
        draft after that.
      </p>
    </div>
  );
}
