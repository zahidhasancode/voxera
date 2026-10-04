export function HeroMock() {
  return (
    <div className="overflow-hidden rounded-2xl border border-border bg-card shadow-soft-xl">
      <div className="flex items-center gap-2 border-b border-border bg-muted/30 px-4 py-3">
        <span className="h-2.5 w-2.5 rounded-full bg-destructive/60" />
        <span className="h-2.5 w-2.5 rounded-full bg-warning/60" />
        <span className="h-2.5 w-2.5 rounded-full bg-success/60" />
        <span className="ml-2 text-2xs text-muted-foreground">VOXERA console — illustration, not a live session</span>
      </div>
      <div className="grid gap-0 lg:grid-cols-5">
        <div className="hidden border-r border-border bg-muted/20 p-4 lg:col-span-1 lg:block">
          {["Overview", "Agents", "Knowledge", "Developer"].map((item, i) => (
            <div
              key={item}
              className={`mb-1 rounded-lg px-3 py-2 text-xs ${i === 1 ? "bg-primary-muted text-primary-muted-foreground font-medium" : "text-muted-foreground"}`}
            >
              {item}
            </div>
          ))}
        </div>
        <div className="lg:col-span-4 p-6 sm:p-8">
          <div className="mb-6 flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground">Support Agent</p>
              <p className="text-sm font-semibold text-foreground">Example conversation</p>
            </div>
            <span className="rounded-full bg-success-muted px-2.5 py-0.5 text-2xs font-medium text-success animate-pulse-soft">
              Listening
            </span>
          </div>
          <div className="space-y-4">
            <div className="flex justify-end">
              <div className="max-w-[80%] rounded-2xl rounded-tr-sm bg-primary px-4 py-3 text-sm text-primary-foreground">
                I need to check my order status for #48291
              </div>
            </div>
            <div className="flex justify-start">
              <div className="max-w-[80%] rounded-2xl rounded-tl-sm border border-border bg-muted/50 px-4 py-3 text-sm text-foreground">
                <span className="text-primary">Sure, let me look that up for you.</span>
                <span className="inline-block w-0.5 h-4 ml-0.5 bg-primary animate-pulse align-middle" />
              </div>
            </div>
          </div>
          <div className="mt-8 flex items-end justify-center gap-1 h-12">
            {Array.from({ length: 24 }).map((_, i) => (
              <div
                key={i}
                className="w-1 rounded-full bg-primary/40 animate-pulse-soft"
                style={{
                  height: `${12 + Math.sin(i * 0.8) * 16 + 8}px`,
                  animationDelay: `${i * 50}ms`,
                }}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
