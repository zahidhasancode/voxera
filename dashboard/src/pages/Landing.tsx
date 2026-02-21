import {
  ArrowRight,
  BarChart3,
  BookOpen,
  Building2,
  CreditCard,
  Heart,
  Lock,
  Mic,
  Play,
  ShoppingCart,
  Shield,
} from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/Button";
import { ThemeToggle } from "@/components/ui/ThemeToggle";

const CAPABILITIES = [
  {
    title: "Voice-first AI",
    description: "Real-time speech-to-speech with sub-400ms latency and natural turn-taking.",
    icon: Mic,
  },
  {
    title: "Knowledge integration",
    description: "Connect docs, FAQs, and CRM so every answer is accurate and on-brand.",
    icon: BookOpen,
  },
  {
    title: "Secure deployment",
    description: "SOC 2 aligned. On-prem, VPC, and hybrid options for regulated industries.",
    icon: Lock,
  },
  {
    title: "Analytics & usage",
    description: "Conversation insights, latency metrics, and per-seat or usage-based billing.",
    icon: BarChart3,
  },
];

const HOW_IT_WORKS = [
  {
    step: "1",
    title: "Connect",
    description: "Integrate via Twilio, SIP, or WebRTC. Point your existing telephony or contact center to VOXERA.",
  },
  {
    step: "2",
    title: "Configure",
    description: "Add agents, knowledge sources, and prompts. Set voice and escalation rules per use case.",
  },
  {
    step: "3",
    title: "Go live",
    description: "Deploy in minutes. Monitor performance and iterate from a single dashboard.",
  },
];

const METRICS = [
  { value: "<400ms", label: "First token latency" },
  { value: "Full duplex", label: "Real-time streaming" },
  { value: "Interruptible", label: "Natural barge-in" },
  { value: "Multi-tenant", label: "Enterprise isolation" },
];

const INDUSTRIES = [
  { name: "Banking", icon: CreditCard, description: "Compliant voice support and IVR replacement" },
  { name: "Healthcare", icon: Heart, description: "Patient outreach and appointment automation" },
  { name: "Ecommerce", icon: ShoppingCart, description: "Order status and returns via voice" },
  { name: "Telecom", icon: Mic, description: "Customer care and retention at scale" },
  { name: "SaaS", icon: Building2, description: "Support deflection and product guidance" },
];

const SECTION_CLASS = "mx-auto max-w-6xl px-4 sm:px-6";
const SECTION_TITLE = "text-2xl font-semibold tracking-tight text-foreground sm:text-3xl";
const SECTION_SUBTITLE = "mt-3 text-muted-foreground max-w-2xl";

export function Landing() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Nav */}
      <nav className="sticky top-0 z-40 border-b border-border bg-background">
        <div className={`${SECTION_CLASS} flex h-14 items-center justify-between`}>
          <Link to="/" className="flex items-center gap-2 font-semibold text-foreground">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
              <Shield className="h-4 w-4 text-primary-foreground" />
            </span>
            VOXERA
          </Link>
          <div className="flex items-center gap-3">
            <ThemeToggle />
            <Link to="/login">
              <Button variant="ghost" size="sm">
                Log in
              </Button>
            </Link>
            <Link to="/login">
              <Button size="sm">Request Demo</Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="border-b border-border">
        <div className={`${SECTION_CLASS} py-16 sm:py-24`}>
          <div className="mx-auto max-w-3xl text-center">
            <h1 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl md:text-5xl">
              Enterprise voice AI for customer support
            </h1>
            <p className="mt-5 text-lg text-muted-foreground sm:text-xl">
              Low-latency, real-time conversations at scale. Full duplex streaming and interruptible voice so every interaction feels natural.
            </p>
            <div className="mt-10 flex flex-wrap items-center justify-center gap-3">
              <Link to="/login">
                <Button size="lg" className="gap-2">
                  Request Demo
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              <a href="#how-it-works">
                <Button variant="secondary" size="lg">
                  How it works
                </Button>
              </a>
            </div>
          </div>
          <div className="mt-14">
            <div className="overflow-hidden rounded-lg border border-border bg-card">
              <div className="flex aspect-video items-center justify-center bg-muted/40 text-muted-foreground">
                <span className="text-sm">Product mock</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Capabilities grid */}
      <section className="border-b border-border bg-card/30">
        <div className={`${SECTION_CLASS} py-16 sm:py-20`}>
          <h2 className={SECTION_TITLE}>Capabilities</h2>
          <p className={`${SECTION_SUBTITLE} mt-2`}>
            Everything you need to deploy and operate voice AI at enterprise scale.
          </p>
          <div className="mt-12 grid gap-8 sm:grid-cols-2">
            {CAPABILITIES.map(({ title, description, icon: Icon }) => (
              <div
                key={title}
                className="flex gap-4 rounded-lg border border-border bg-background p-6"
              >
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-border bg-card">
                  <Icon className="h-5 w-5 text-foreground" />
                </div>
                <div>
                  <h3 className="font-semibold text-foreground">{title}</h3>
                  <p className="mt-2 text-sm text-muted-foreground">{description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="border-b border-border">
        <div className={`${SECTION_CLASS} py-16 sm:py-20`}>
          <h2 className={SECTION_TITLE}>How it works</h2>
          <p className={SECTION_SUBTITLE}>
            Three steps from integration to production.
          </p>
          <div className="mt-12 grid gap-10 sm:grid-cols-3">
            {HOW_IT_WORKS.map(({ step, title, description }) => (
              <div key={step} className="flex flex-col">
                <span className="text-2xl font-semibold tabular-nums text-muted-foreground">
                  {step}
                </span>
                <h3 className="mt-4 font-semibold text-foreground">{title}</h3>
                <p className="mt-2 text-sm text-muted-foreground">{description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Performance metrics strip */}
      <section className="border-b border-border bg-card/30">
        <div className={`${SECTION_CLASS} py-10`}>
          <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
            {METRICS.map(({ value, label }) => (
              <div key={label}>
                <div className="font-semibold text-foreground">{value}</div>
                <div className="mt-1 text-sm text-muted-foreground">{label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Multi-industry use cases */}
      <section className="border-b border-border">
        <div className={`${SECTION_CLASS} py-16 sm:py-20`}>
          <h2 className={SECTION_TITLE}>Use cases by industry</h2>
          <p className={SECTION_SUBTITLE}>
            Voice automation built for compliance and complexity in your sector.
          </p>
          <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {INDUSTRIES.map(({ name, icon: Icon, description }) => (
              <div
                key={name}
                className="rounded-lg border border-border bg-card p-6"
              >
                <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-background">
                  <Icon className="h-4 w-4 text-foreground" />
                </div>
                <h3 className="mt-4 font-semibold text-foreground">{name}</h3>
                <p className="mt-2 text-sm text-muted-foreground">{description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Architecture diagram placeholder */}
      <section id="architecture" className="border-b border-border bg-card/30">
        <div className={`${SECTION_CLASS} py-16 sm:py-20`}>
          <h2 className={SECTION_TITLE}>Architecture</h2>
          <p className={SECTION_SUBTITLE}>
            Telephony and WebRTC in, streaming STT and LLM, TTS out. Full duplex with native barge-in.
          </p>
          <div className="mt-12 rounded-lg border border-border bg-background p-12">
            <div className="flex flex-col items-center justify-center gap-4 text-center text-muted-foreground">
              <div className="h-24 w-full max-w-md rounded border border-dashed border-border bg-card/50" />
              <span className="text-sm">Architecture diagram placeholder</span>
            </div>
          </div>
        </div>
      </section>

      {/* Demo / video section */}
      <section className="border-b border-border">
        <div className={`${SECTION_CLASS} py-16 sm:py-20`}>
          <h2 className={SECTION_TITLE}>See it in action</h2>
          <p className={SECTION_SUBTITLE}>
            A short walkthrough of the platform and a sample conversation.
          </p>
          <div className="mt-12 overflow-hidden rounded-lg border border-border bg-card">
            <div className="flex aspect-video items-center justify-center bg-muted/40">
              <button
                type="button"
                className="flex h-14 w-14 items-center justify-center rounded-full border border-border bg-background text-foreground transition-colors hover:bg-muted"
                aria-label="Play demo video"
              >
                <Play className="h-6 w-6 ml-0.5" />
              </button>
            </div>
            <p className="border-t border-border px-4 py-3 text-center text-sm text-muted-foreground">
              Demo / video placeholder
            </p>
          </div>
        </div>
      </section>

      {/* Contact / Request Demo CTA */}
      <section className="border-b border-border bg-card/30">
        <div className={`${SECTION_CLASS} py-16 sm:py-20`}>
          <div className="mx-auto max-w-2xl text-center">
            <h2 className={SECTION_TITLE}>Ready to get started?</h2>
            <p className="mt-4 text-muted-foreground">
              Talk to our team for a custom demo and pricing for your use case.
            </p>
            <div className="mt-10">
              <Link to="/login">
                <Button size="lg" className="gap-2">
                  Request Demo
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border">
        <div className={`${SECTION_CLASS} py-10`}>
          <div className="flex flex-col items-center justify-between gap-6 sm:flex-row">
            <Link to="/" className="flex items-center gap-2 font-semibold text-foreground">
              <Shield className="h-5 w-5 text-primary" />
              VOXERA
            </Link>
            <nav className="flex gap-8 text-sm text-muted-foreground" aria-label="Footer">
              <a href="#how-it-works" className="hover:text-foreground">How it works</a>
              <a href="#architecture" className="hover:text-foreground">Architecture</a>
              <Link to="/login" className="hover:text-foreground">Log in</Link>
              <Link to="/login" className="hover:text-foreground">Request Demo</Link>
            </nav>
          </div>
          <p className="mt-8 text-center text-sm text-muted-foreground sm:text-left">
            © {new Date().getFullYear()} VOXERA. Enterprise voice automation.
          </p>
        </div>
      </footer>
    </div>
  );
}
