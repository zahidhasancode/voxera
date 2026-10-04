import {
  BookOpen,
  Github,
  Hand,
  Layers,
  Mic,
  Plug,
  Repeat,
  Shield,
  Timer,
} from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/Button";
import { ThemeToggle } from "@/components/ui/ThemeToggle";
import { HeroMock } from "@/components/landing/HeroMock";
import { ArchitectureDiagram } from "@/components/landing/ArchitectureDiagram";
import { README_URL, REPO_URL } from "@/projectLinks";

const WHAT_WORKS = [
  {
    title: "Streaming pipeline",
    description:
      "Speech-to-text, a language model, and text-to-speech run as one streaming pipeline over a WebSocket. Partial results are passed on as they are produced.",
    icon: Mic,
  },
  {
    title: "Turn-taking",
    description:
      "A turn state machine tracks whether the user or the agent is speaking and decides when a user turn is complete.",
    icon: Repeat,
  },
  {
    title: "Barge-in",
    description:
      "Speaking while the agent is replying cancels the language-model and speech output in flight, and the agent goes back to listening.",
    icon: Hand,
  },
  {
    title: "Pluggable providers",
    description:
      "Providers sit behind a common interface and can be swapped: Deepgram, OpenAI, Anthropic, Groq, and ElevenLabs. You bring your own API keys.",
    icon: Plug,
  },
  {
    title: "Bounded queues",
    description:
      "Audio moves through fixed-size queues. Under backpressure the oldest frame is dropped, so the receive loop is not blocked.",
    icon: Layers,
  },
  {
    title: "Benchmark script",
    description:
      "Latency is measured with the benchmark in the repository; see the README. No figures are quoted on this page.",
    icon: Timer,
  },
];

const RUN_LOCALLY = [
  {
    step: "01",
    title: "Clone",
    description: "Get the source from GitHub. The README lists the prerequisites and the setup steps.",
  },
  {
    step: "02",
    title: "Start the backend",
    description: "Add your own provider API keys and start the API server on your machine.",
  },
  {
    step: "03",
    title: "Talk to it",
    description: "Open the browser client, speak, and interrupt the agent in the middle of a reply.",
  },
];

const HIGHLIGHTS = [
  { value: "Streaming", label: "Speech in, speech out" },
  { value: "Full duplex", label: "Audio both ways on one WebSocket" },
  { value: "Interruptible", label: "Barge-in cancels the reply" },
  { value: "Pluggable", label: "Swappable providers" },
];

const CONTAINER = "mx-auto max-w-content px-4 sm:px-6 lg:px-8";
const EYEBROW = "text-xs font-medium uppercase tracking-widest text-muted-foreground";
const HEADING = "font-semibold tracking-tight text-foreground";
const BODY = "text-muted-foreground";
const EXTERNAL = { target: "_blank", rel: "noopener noreferrer" } as const;

export function Landing() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Nav */}
      <header className="sticky top-0 z-40 border-b border-border/80 bg-background/95 backdrop-blur-sm">
        <div className={`${CONTAINER} flex h-16 items-center justify-between`}>
          <Link
            to="/"
            className="flex items-center gap-3 font-semibold text-foreground transition-opacity hover:opacity-90"
          >
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary">
              <Shield className="h-5 w-5 text-primary-foreground" />
            </span>
            <span className="text-lg">VOXERA</span>
          </Link>
          <div className="flex items-center gap-2 sm:gap-4">
            <ThemeToggle />
            <Link to="/login" title="Requires the backend running locally">
              <Button variant="ghost" size="sm">
                Open console
              </Button>
            </Link>
            <a href={REPO_URL} {...EXTERNAL}>
              <Button size="sm" className="gap-1.5">
                <Github className="h-4 w-4" />
                View on GitHub
              </Button>
            </a>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="border-b border-border bg-background-subtle/50">
        <div className={`${CONTAINER} pt-20 pb-16 sm:pt-28 sm:pb-24 lg:pt-32 lg:pb-30`}>
          <p className={EYEBROW}>Real-time voice-agent prototype</p>
          <h1 className={`${HEADING} mt-3 text-4xl sm:text-5xl lg:text-display-lg`}>
            A streaming voice agent you can interrupt.
          </h1>
          <p className={`${BODY} mt-6 max-w-narrow text-lg sm:text-xl`}>
            VOXERA is a personal project with its source on GitHub: streaming speech-to-text, a language model, and
            text-to-speech over WebSockets, with turn-taking and barge-in. It is a prototype, not a commercial product.
          </p>
          <p className="mt-4 text-sm font-medium text-foreground">Built by MD Zahid Hasan</p>
          <div className="mt-10 flex flex-wrap items-center gap-4">
            <a href={REPO_URL} {...EXTERNAL}>
              <Button size="lg" className="gap-2 min-w-[180px]">
                <Github className="h-4 w-4" />
                View on GitHub
              </Button>
            </a>
            <a href={README_URL} {...EXTERNAL}>
              <Button variant="secondary" size="lg" className="gap-2 border-accent-muted bg-accent-muted/30 text-accent-muted-foreground hover:bg-accent-muted/50 dark:bg-accent-muted/20 dark:text-accent-muted-foreground dark:hover:bg-accent-muted/30">
                <BookOpen className="h-4 w-4" />
                Run the demo locally
              </Button>
            </a>
          </div>
          <p className="mt-4 text-sm text-muted-foreground">
            <Link to="/login" className="underline underline-offset-4 hover:text-foreground">
              Open console
            </Link>{" "}
            (requires the backend running locally)
          </p>
          <div className="mt-16 lg:mt-22 animate-fade-in-up">
            <HeroMock />
          </div>
        </div>
      </section>

      <section className="border-b border-border bg-primary-muted/20 dark:bg-primary-muted/10">
        <div className={`${CONTAINER} py-12`}>
          <div className="grid grid-cols-2 gap-x-8 gap-y-8 md:grid-cols-4">
            {HIGHLIGHTS.map(({ value, label }, i) => (
              <div key={label}>
                <div className={`text-2xl font-semibold tracking-tight sm:text-3xl ${
                  i === 0 ? "text-primary" : i === 1 ? "text-success" : "text-foreground"
                }`}>{value}</div>
                <div className="mt-1 text-sm text-muted-foreground">{label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* What works */}
      <section id="what-works" className="border-b border-border">
        <div className={`${CONTAINER} py-20 sm:py-24 lg:py-30`}>
          <p className={EYEBROW}>Status</p>
          <h2 className={`${HEADING} mt-2 text-3xl sm:text-4xl`}>What works</h2>
          <p className={`${BODY} mt-4 max-w-2xl text-base`}>
            The parts of the voice core that are implemented in the repository today.
          </p>
          <div className="mt-14 grid gap-8 sm:grid-cols-2">
            {WHAT_WORKS.map(({ title, description, icon: Icon }) => (
              <div
                key={title}
                className="group flex gap-5 rounded-2xl border border-border bg-card p-8 transition-shadow hover:shadow-soft-lg"
              >
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-primary-muted">
                  <Icon className="h-6 w-6 text-primary-muted-foreground" />
                </div>
                <div>
                  <h3 className="font-semibold text-foreground">{title}</h3>
                  <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Architecture */}
      <section id="architecture" className="border-b border-border bg-card/30">
        <div className={`${CONTAINER} py-20 sm:py-24 lg:py-30`}>
          <p className={EYEBROW}>Technical</p>
          <h2 className={`${HEADING} mt-2 text-3xl sm:text-4xl`}>How it is built</h2>
          <p className={`${BODY} mt-4 max-w-2xl text-base`}>
            Audio in over a WebSocket, streaming speech-to-text and language model, synthesized speech out. Full duplex with barge-in.
          </p>
          <ArchitectureDiagram />
        </div>
      </section>

      {/* Run locally */}
      <section id="run-locally" className="border-b border-border">
        <div className={`${CONTAINER} py-20 sm:py-24 lg:py-30`}>
          <p className={EYEBROW}>Try it</p>
          <h2 className={`${HEADING} mt-2 text-3xl sm:text-4xl`}>Run it locally</h2>
          <p className={`${BODY} mt-4 max-w-2xl text-base`}>
            There is no hosted demo. The voice agent runs on your own machine with your own provider keys.
          </p>
          <div className="mt-16 grid gap-12 sm:grid-cols-3">
            {RUN_LOCALLY.map(({ step, title, description }) => (
              <div key={step} className="relative">
                <span className="text-sm font-semibold tabular-nums text-primary">{step}</span>
                <h3 className="mt-4 text-xl font-semibold text-foreground">{title}</h3>
                <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{description}</p>
                {step !== "03" && (
                  <div className="absolute -right-6 top-8 hidden text-muted-foreground/50 sm:block">→</div>
                )}
              </div>
            ))}
          </div>
          <div className="mt-12">
            <a href={README_URL} {...EXTERNAL}>
              <Button variant="outline" size="lg" className="gap-2">
                <BookOpen className="h-4 w-4" />
                Run the demo locally
              </Button>
            </a>
          </div>
        </div>
      </section>

      {/* Admin console */}
      <section id="console" className="border-b border-border bg-card/30">
        <div className={`${CONTAINER} py-20 sm:py-24 lg:py-30`}>
          <p className={EYEBROW}>Admin console</p>
          <h2 className={`${HEADING} mt-2 text-3xl sm:text-4xl`}>A UI prototype</h2>
          <p className={`${BODY} mt-4 max-w-2xl text-base`}>
            This site also contains an admin console for agents, calls, and usage. It is a user-interface prototype and
            needs the backend API running locally. This hosted page has no backend, so signing in here does not work.
          </p>
          <div className="mt-10">
            <Link to="/login">
              <Button variant="outline" size="lg">
                Open console (local backend required)
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="border-b border-border bg-background-subtle/60 dark:bg-background-subtle/40">
        <div className={`${CONTAINER} py-20 sm:py-24 lg:py-30`}>
          <div className="mx-auto max-w-2xl text-center">
            <h2 className={`${HEADING} text-3xl sm:text-4xl`}>Read the code</h2>
            <p className={`${BODY} mt-5 text-lg`}>
              The source, the setup instructions, and the benchmark are in the repository.
            </p>
            <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
              <a href={REPO_URL} {...EXTERNAL}>
                <Button size="lg" className="gap-2 min-w-[200px]">
                  <Github className="h-4 w-4" />
                  View on GitHub
                </Button>
              </a>
              <a href={README_URL} {...EXTERNAL}>
                <Button variant="outline" size="lg" className="gap-2 min-w-[200px]">
                  <BookOpen className="h-4 w-4" />
                  Run the demo locally
                </Button>
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border">
        <div className={`${CONTAINER} py-14`}>
          <div className="grid gap-12 sm:grid-cols-2 lg:grid-cols-3">
            <div>
              <Link to="/" className="flex items-center gap-3 font-semibold text-foreground">
                <Shield className="h-6 w-6 text-primary" />
                VOXERA
              </Link>
              <p className="mt-4 text-sm text-muted-foreground">
                Real-time voice-agent prototype.
              </p>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-foreground">On this page</h4>
              <ul className="mt-4 space-y-3 text-sm text-muted-foreground">
                <li><a href="#what-works" className="hover:text-foreground">What works</a></li>
                <li><a href="#architecture" className="hover:text-foreground">How it is built</a></li>
                <li><a href="#run-locally" className="hover:text-foreground">Run it locally</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-foreground">Project</h4>
              <ul className="mt-4 space-y-3 text-sm text-muted-foreground">
                <li><a href={REPO_URL} {...EXTERNAL} className="hover:text-foreground">GitHub repository</a></li>
                <li><a href={README_URL} {...EXTERNAL} className="hover:text-foreground">README</a></li>
                <li><Link to="/login" className="hover:text-foreground">Open console (local backend required)</Link></li>
              </ul>
            </div>
          </div>
          <div className="mt-14 pt-8 border-t border-border flex flex-col sm:flex-row items-center justify-between gap-4">
            <p className="text-sm text-muted-foreground">
              Built by MD Zahid Hasan
            </p>
            <p className="text-2xs text-muted-foreground">
              Personal project. Not a commercial product.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
