const boxes = [
  { label: "Client", sub: "Browser / Phone" },
  { label: "WebSocket", sub: "PCM16 + JSON" },
  { label: "STT", sub: "Streaming" },
  { label: "LLM", sub: "Token stream" },
  { label: "TTS", sub: "PCM16 out" },
];

export function ArchitectureDiagram() {
  return (
    <div className="overflow-x-auto rounded-2xl border border-border bg-background p-6 sm:p-10">
      <div className="flex min-w-[640px] items-center justify-between gap-2">
        {boxes.map((box, i) => (
          <div key={box.label} className="flex flex-1 items-center gap-2">
            <div className="flex-1 rounded-xl border border-border bg-card p-4 text-center shadow-soft">
              <p className="text-sm font-semibold text-foreground">{box.label}</p>
              <p className="mt-1 text-2xs text-muted-foreground">{box.sub}</p>
            </div>
            {i < boxes.length - 1 && (
              <svg className="h-4 w-6 shrink-0 text-primary" viewBox="0 0 24 16" fill="none" aria-hidden>
                <path d="M0 8h18M14 3l5 5-5 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            )}
          </div>
        ))}
      </div>
      <div className="mt-8 grid gap-4 sm:grid-cols-3">
        {[
          { title: "Turn-taking", desc: "User/system turn state machine" },
          { title: "Barge-in", desc: "Cancel LLM + TTS on interrupt" },
          { title: "Bounded queues", desc: "20ms frame cadence, drop-oldest" },
        ].map(({ title, desc }) => (
          <div key={title} className="rounded-lg border border-border bg-primary-muted/20 px-4 py-3">
            <p className="text-sm font-medium text-primary-muted-foreground">{title}</p>
            <p className="mt-1 text-2xs text-muted-foreground">{desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
