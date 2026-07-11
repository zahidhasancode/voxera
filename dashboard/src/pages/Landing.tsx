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
import { HeroMock } from "@/components/landing/HeroMock";
import { ArchitectureDiagram } from "@/components/landing/ArchitectureDiagram";

const CAPABILITIES = [
  {
    title: "Voice-first AI",
    description: "Real-time speech-to-speech with sub-400ms first-token latency and natural turn-taking. Built for contact centers and self-service.",
    icon: Mic,
  },
  {
    title: "Knowledge integration",
    description: "Connect docs, FAQs, and CRM. Every answer stays accurate, on-brand, and within your compliance boundaries.",
    icon: BookOpen,
  },
  {
    title: "Secure deployment",
    description: "SOC 2 aligned. On-prem, VPC, and hybrid options for banking, healthcare, and regulated industries.",
    icon: Lock,
  },
  {
    title: "Analytics & usage",
    description: "Conversation insights, latency metrics, and flexible per-seat or usage-based billing with clear reporting.",
    icon: BarChart3,
  },
];

const HOW_IT_WORKS = [
  {
    step: "01",
    title: "Connect",
    description: "Integrate via Twilio, SIP, or WebRTC. Point your existing telephony or contact center to VOXERA in minutes.",
  },
  {
    step: "02",
    title: "Configure",
    description: "Add agents, knowledge sources, and prompts. Set voice, escalation, and handoff rules per use case.",
  },
  {
    step: "03",
    title: "Go live",
    description: "Deploy to production. Monitor performance, iterate on prompts, and scale from a single dashboard.",
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

const PRICING = [
  { name: "Starter", price: "$99", period: "/mo", features: ["1,000 voice min", "3 agents", "Email support", "Standard latency"], cta: "Start trial", highlighted: false },
  { name: "Pro", price: "$499", period: "/mo", features: ["10,000 voice min", "Unlimited agents", "Priority support", "Sub-400ms SLA", "Analytics"], cta: "Request demo", highlighted: true },
  { name: "Enterprise", price: "Custom", period: "", features: ["Unlimited usage", "VPC / on-prem", "Dedicated support", "Custom SLA", "SSO & SAML"], cta: "Contact sales", highlighted: false },
];

const LOGOS = ["Acme Corp", "Northwind", "Globex", "Initech", "Umbrella"];

const CONTAINER = "mx-auto max-w-content px-4 sm:px-6 lg:px-8";
const EYEBROW = "text-xs font-medium uppercase tracking-widest text-muted-foreground";
const HEADING = "font-semibold tracking-tight text-foreground";
const BODY = "text-muted-foreground";

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
            <Link to="/login">
              <Button variant="ghost" size="sm">
                Log in
              </Button>
            </Link>
            <Link to="/login">
              <Button size="sm" className="gap-1.5">
                Request Demo
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="border-b border-border bg-background-subtle/50">
        <div className={`${CONTAINER} pt-20 pb-16 sm:pt-28 sm:pb-24 lg:pt-32 lg:pb-30`}>
          <p className={EYEBROW}>Enterprise voice AI</p>
          <h1 className={`${HEADING} mt-3 text-4xl sm:text-5xl lg:text-display-lg`}>
            Customer support that scales. In real time.
          </h1>
          <p className={`${BODY} mt-6 max-w-narrow text-lg sm:text-xl`}>
            Low-latency, full-duplex voice AI for contact centers and self-service. Sub-400ms first token, natural barge-in, and enterprise-grade security.
          </p>
          <div className="mt-10 flex flex-wrap items-center gap-4">
            <Link to="/login">
              <Button size="lg" className="gap-2 min-w-[180px]">
                Request Demo
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <a href="#how-it-works">
              <Button variant="secondary" size="lg" className="border-accent-muted bg-accent-muted/30 text-accent-muted-foreground hover:bg-accent-muted/50 dark:bg-accent-muted/20 dark:text-accent-muted-foreground dark:hover:bg-accent-muted/30">
                How it works
              </Button>
            </a>
          </div>
          <div className="mt-16 lg:mt-22 animate-fade-in-up">
            <HeroMock />
          </div>
        </div>
      </section>

      {/* Social proof */}
      <section className="border-b border-border py-10">
        <div className={`${CONTAINER}`}>
          <p className="text-center text-2xs font-medium uppercase tracking-widest text-muted-foreground">
            Trusted by forward-thinking teams
          </p>
          <div className="mt-6 flex flex-wrap items-center justify-center gap-x-10 gap-y-4">
            {LOGOS.map((name) => (
              <span key={name} className="text-sm font-semibold text-muted-foreground/60">
                {name}
              </span>
            ))}
          </div>
        </div>
      </section>

      <section className="border-b border-border bg-primary-muted/20 dark:bg-primary-muted/10">
        <div className={`${CONTAINER} py-12`}>
          <div className="grid grid-cols-2 gap-x-8 gap-y-8 md:grid-cols-4">
            {METRICS.map(({ value, label }, i) => (
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

      {/* Capabilities */}
      <section className="border-b border-border">
        <div className={`${CONTAINER} py-20 sm:py-24 lg:py-30`}>
          <p className={EYEBROW}>Platform</p>
          <h2 className={`${HEADING} mt-2 text-3xl sm:text-4xl`}>Capabilities</h2>
          <p className={`${BODY} mt-4 max-w-2xl text-base`}>
            Everything you need to deploy and operate voice AI at enterprise scale.
          </p>
          <div className="mt-14 grid gap-8 sm:grid-cols-2">
            {CAPABILITIES.map(({ title, description, icon: Icon }) => (
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

      {/* How it works */}
      <section id="how-it-works" className="border-b border-border bg-card/30">
        <div className={`${CONTAINER} py-20 sm:py-24 lg:py-30`}>
          <p className={EYEBROW}>Process</p>
          <h2 className={`${HEADING} mt-2 text-3xl sm:text-4xl`}>How it works</h2>
          <p className={`${BODY} mt-4 max-w-2xl text-base`}>
            Three steps from integration to production.
          </p>
          <div className="mt-16 grid gap-12 sm:grid-cols-3">
            {HOW_IT_WORKS.map(({ step, title, description }) => (
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
        </div>
      </section>

      {/* Industries */}
      <section className="border-b border-border">
        <div className={`${CONTAINER} py-20 sm:py-24 lg:py-30`}>
          <p className={EYEBROW}>Industries</p>
          <h2 className={`${HEADING} mt-2 text-3xl sm:text-4xl`}>Built for every sector</h2>
          <p className={`${BODY} mt-4 max-w-2xl text-base`}>
            Voice automation that fits your compliance and use cases.
          </p>
          <div className="mt-14 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {INDUSTRIES.map(({ name, icon: Icon, description }) => (
              <div
                key={name}
                className="flex gap-5 rounded-2xl border border-border bg-card p-6 transition-shadow hover:shadow-soft"
              >
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-accent-muted/50 dark:bg-accent-muted/30">
                  <Icon className="h-5 w-5 text-accent-muted-foreground" />
                </div>
                <div>
                  <h3 className="font-semibold text-foreground">{name}</h3>
                  <p className="mt-2 text-sm text-muted-foreground">{description}</p>
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
          <h2 className={`${HEADING} mt-2 text-3xl sm:text-4xl`}>Architecture</h2>
          <p className={`${BODY} mt-4 max-w-2xl text-base`}>
            Telephony and WebRTC in, streaming STT and LLM, TTS out. Full duplex with native barge-in.
          </p>
          <ArchitectureDiagram />
        </div>
      </section>

      {/* Demo / video */}
      <section className="border-b border-border">
        <div className={`${CONTAINER} py-20 sm:py-24 lg:py-30`}>
          <p className={EYEBROW}>Demo</p>
          <h2 className={`${HEADING} mt-2 text-3xl sm:text-4xl`}>See it in action</h2>
          <p className={`${BODY} mt-4 max-w-2xl text-base`}>
            A short walkthrough of the platform and a sample conversation.
          </p>
          <div className="mt-14 overflow-hidden rounded-2xl border border-border bg-card shadow-soft-lg">
            <div className="flex aspect-video flex-col items-center justify-center gap-4 bg-muted/20 p-8">
              <p className="max-w-md text-center text-sm text-muted-foreground">
                Experience real-time voice AI with streaming STT, LLM, and TTS — try the live demo.
              </p>
              <a href="http://localhost:5174" target="_blank" rel="noopener noreferrer">
                <Button size="lg" className="gap-2">
                  <Play className="h-4 w-4" />
                  Open voice demo
                </Button>
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="border-b border-border">
        <div className={`${CONTAINER} py-20 sm:py-24 lg:py-30`}>
          <p className={EYEBROW}>Pricing</p>
          <h2 className={`${HEADING} mt-2 text-3xl sm:text-4xl`}>Plans that scale with you</h2>
          <p className={`${BODY} mt-4 max-w-2xl text-base`}>
            Start with a trial, grow to enterprise. Usage-based billing available on all plans.
          </p>
          <div className="mt-14 grid gap-6 lg:grid-cols-3">
            {PRICING.map((plan) => (
              <div
                key={plan.name}
                className={`flex flex-col rounded-2xl border p-8 ${
                  plan.highlighted
                    ? "border-primary bg-primary-muted/20 shadow-soft-lg"
                    : "border-border bg-card"
                }`}
              >
                <h3 className="text-lg font-semibold text-foreground">{plan.name}</h3>
                <p className="mt-4">
                  <span className="text-4xl font-semibold tracking-tight text-foreground">{plan.price}</span>
                  <span className="text-muted-foreground">{plan.period}</span>
                </p>
                <ul className="mt-6 flex-1 space-y-3">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-center gap-2 text-sm text-muted-foreground">
                      <span className="h-1.5 w-1.5 rounded-full bg-primary" />
                      {f}
                    </li>
                  ))}
                </ul>
                <Link to="/login" className="mt-8 block">
                  <Button
                    variant={plan.highlighted ? "primary" : "outline"}
                    className="w-full"
                  >
                    {plan.cta}
                  </Button>
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="border-b border-border bg-background-subtle/60 dark:bg-background-subtle/40">
        <div className={`${CONTAINER} py-20 sm:py-24 lg:py-30`}>
          <div className="mx-auto max-w-2xl text-center">
            <h2 className={`${HEADING} text-3xl sm:text-4xl`}>Ready to get started?</h2>
            <p className={`${BODY} mt-5 text-lg`}>
              Talk to our team for a custom demo and pricing tailored to your use case.
            </p>
            <div className="mt-10">
              <Link to="/login">
                <Button size="lg" className="gap-2 min-w-[200px]">
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
        <div className={`${CONTAINER} py-14`}>
          <div className="grid gap-12 sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <Link to="/" className="flex items-center gap-3 font-semibold text-foreground">
                <Shield className="h-6 w-6 text-primary" />
                VOXERA
              </Link>
              <p className="mt-4 text-sm text-muted-foreground">
                Enterprise voice AI for customer support.
              </p>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-foreground">Product</h4>
              <ul className="mt-4 space-y-3 text-sm text-muted-foreground">
                <li><a href="#how-it-works" className="hover:text-foreground">How it works</a></li>
                <li><a href="#architecture" className="hover:text-foreground">Architecture</a></li>
                <li><Link to="/login" className="hover:text-foreground">Request Demo</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-foreground">Company</h4>
              <ul className="mt-4 space-y-3 text-sm text-muted-foreground">
                <li><Link to="/login" className="hover:text-foreground">Log in</Link></li>
                <li><a href="#" className="hover:text-foreground">Contact</a></li>
                <li><a href="#" className="hover:text-foreground">Status</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-foreground">Legal</h4>
              <ul className="mt-4 space-y-3 text-sm text-muted-foreground">
                <li><a href="#" className="hover:text-foreground">Privacy</a></li>
                <li><a href="#" className="hover:text-foreground">Terms</a></li>
              </ul>
            </div>
          </div>
          <div className="mt-14 pt-8 border-t border-border flex flex-col sm:flex-row items-center justify-between gap-4">
            <p className="text-sm text-muted-foreground">
              © {new Date().getFullYear()} VOXERA. All rights reserved.
            </p>
            <p className="text-2xs text-muted-foreground">
              Enterprise voice automation platform.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
