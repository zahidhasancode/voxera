import {
  CheckCircle2,
  FileCheck,
  Globe,
  Lock,
  Mail,
  MapPin,
  ShieldCheck,
} from "lucide-react";
import { useCallback, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { PageHeader } from "@/components/layout/PageHeader";

const REGIONS = [
  { id: "us-east", name: "US East (N. Virginia)", flag: "US", residency: "United States" },
  { id: "us-west", name: "US West (Oregon)", flag: "US", residency: "United States" },
  { id: "eu-west", name: "EU West (Ireland)", flag: "EU", residency: "European Union (GDPR)" },
  { id: "eu-central", name: "EU Central (Frankfurt)", flag: "EU", residency: "European Union (GDPR)" },
  { id: "uk", name: "UK (London)", flag: "UK", residency: "United Kingdom" },
  { id: "apac", name: "Asia Pacific (Singapore)", flag: "APAC", residency: "Singapore" },
];

const COMPLIANCE = [
  {
    id: "soc2",
    name: "SOC 2 Type II",
    description: "Audited security, availability, and confidentiality controls.",
    icon: ShieldCheck,
  },
  {
    id: "gdpr",
    name: "GDPR",
    description: "Data processing agreements and EU privacy compliance.",
    icon: FileCheck,
  },
  {
    id: "hipaa",
    name: "HIPAA",
    description: "Available under BAA for healthcare workloads.",
    icon: Lock,
  },
];

const SLA_ITEMS = [
  { label: "Uptime", value: "99.95%", sub: "Monthly guaranteed" },
  { label: "API response", value: "< 200 ms", sub: "P99 latency" },
  { label: "Support response", value: "< 1 hour", sub: "Critical severity" },
  { label: "Data backup", value: "Daily", sub: "Point-in-time recovery" },
];

export function Enterprise() {
  const [region, setRegion] = useState("us-east");
  const [ssoEnabled, setSsoEnabled] = useState(false);
  const [ssoEntityId, setSsoEntityId] = useState("");
  const [ssoSsoUrl, setSsoSsoUrl] = useState("");
  const [ssoCert, setSsoCert] = useState("");

  const [contactSubmitting, setContactSubmitting] = useState(false);
  const [contactSent, setContactSent] = useState(false);
  const [contactName, setContactName] = useState("");
  const [contactEmail, setContactEmail] = useState("");
  const [contactCompany, setContactCompany] = useState("");
  const [contactMessage, setContactMessage] = useState("");

  const handleContactSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      if (!contactEmail.trim()) return;
      setContactSubmitting(true);
      setTimeout(() => {
        setContactSubmitting(false);
        setContactSent(true);
        setContactName("");
        setContactEmail("");
        setContactCompany("");
        setContactMessage("");
      }, 800);
    },
    [contactEmail]
  );

  const selectedRegion = REGIONS.find((r) => r.id === region);

  return (
    <>
      <PageHeader
        title="Enterprise"
        description="SLA, SSO, data residency, and compliance for large organizations"
      />

      {/* Trust strip */}
      <div className="mb-8 flex flex-wrap items-center justify-center gap-6 rounded-xl border border-border bg-card px-6 py-4 text-sm text-muted-foreground">
        <span className="flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 text-emerald-500" />
          SOC 2 Type II
        </span>
        <span className="flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 text-emerald-500" />
          GDPR compliant
        </span>
        <span className="flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 text-emerald-500" />
          HIPAA available
        </span>
        <span className="flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 text-emerald-500" />
          99.95% uptime SLA
        </span>
      </div>

      <div className="grid gap-8 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-8">
          {/* SLA */}
          <Card>
            <CardHeader
              title="Service level agreement"
              description="Enterprise commitments and guarantees"
            />
            <CardContent>
              <div className="grid gap-4 sm:grid-cols-2">
                {SLA_ITEMS.map((item) => (
                  <div
                    key={item.label}
                    className="flex items-start gap-4 rounded-lg border border-border bg-background p-4"
                  >
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/20">
                      <ShieldCheck className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <p className="font-medium text-foreground">{item.value}</p>
                      <p className="text-sm font-medium text-muted-foreground">
                        {item.label}
                      </p>
                      <p className="text-2xs text-muted-foreground">
                        {item.sub}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
              <p className="mt-4 text-2xs text-muted-foreground">
                Full SLA terms are included in the Enterprise agreement. Credit
                applies for verified downtime.
              </p>
            </CardContent>
          </Card>

          {/* SSO */}
          <Card>
            <CardHeader
              title="Single sign-on (SSO)"
              description="SAML 2.0 and SCIM provisioning"
            />
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between rounded-lg border border-border bg-background p-4">
                <div>
                  <p className="font-medium text-foreground">SSO status</p>
                  <p className="text-sm text-muted-foreground">
                    {ssoEnabled
                      ? "Connected to your identity provider"
                      : "Not configured"}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setSsoEnabled((e) => !e)}
                  className={`relative inline-flex h-6 w-11 shrink-0 rounded-full border transition-colors focus:outline-none focus:ring-2 focus:ring-primary ${
                    ssoEnabled
                      ? "border-primary bg-primary"
                      : "border-border bg-background-hover"
                  }`}
                >
                  <span
                    className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow transition-transform ${
                      ssoEnabled ? "translate-x-5" : "translate-x-1"
                    }`}
                    style={{ marginTop: 2 }}
                  />
                </button>
              </div>
              {ssoEnabled && (
                <div className="space-y-4 rounded-lg border border-border bg-background-hover/50 p-4">
                  <Input
                    label="Entity ID (Audience)"
                    placeholder="https://voxera.io/saml/your-org"
                    value={ssoEntityId}
                    onChange={(e) => setSsoEntityId(e.target.value)}
                  />
                  <Input
                    label="SSO URL (IdP sign-in URL)"
                    placeholder="https://idp.example.com/sso"
                    value={ssoSsoUrl}
                    onChange={(e) => setSsoSsoUrl(e.target.value)}
                  />
                  <div>
                    <label className="mb-1.5 block text-sm font-medium text-muted-foreground">
                      IdP certificate (X.509 PEM)
                    </label>
                    <textarea
                      className="w-full rounded-lg border border-border bg-background px-3 py-2 font-mono text-sm text-foreground placeholder-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                      placeholder="-----BEGIN CERTIFICATE-----..."
                      rows={4}
                      value={ssoCert}
                      onChange={(e) => setSsoCert(e.target.value)}
                    />
                  </div>
                  <Button variant="secondary" size="sm">
                    Save SSO configuration
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Data residency & region */}
          <Card>
            <CardHeader
              title="Data residency & region"
              description="Choose where your data is stored and processed"
            />
            <CardContent className="space-y-4">
              <div>
                <label className="mb-2 block text-sm font-medium text-muted-foreground">
                  Primary region
                </label>
                <div className="grid gap-2 sm:grid-cols-2">
                  {REGIONS.map((r) => (
                    <button
                      key={r.id}
                      type="button"
                      onClick={() => setRegion(r.id)}
                      className={`flex items-center gap-3 rounded-lg border px-4 py-3 text-left transition-colors ${
                        region === r.id
                          ? "border-primary bg-primary/10"
                          : "border-border bg-background hover:border-border/80"
                      }`}
                    >
                      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-card">
                        <Globe className="h-4 w-4 text-muted-foreground" />
                      </div>
                      <div className="min-w-0">
                        <p className="font-medium text-foreground">{r.name}</p>
                        <p className="text-2xs text-muted-foreground">
                          {r.residency}
                        </p>
                      </div>
                      {region === r.id && (
                        <CheckCircle2 className="ml-auto h-5 w-5 shrink-0 text-primary" />
                      )}
                    </button>
                  ))}
                </div>
              </div>
              {selectedRegion && (
                <div className="flex items-center gap-2 rounded-lg border border-border bg-background px-4 py-3 text-sm text-muted-foreground">
                  <MapPin className="h-4 w-4 shrink-0" />
                  Data for this organization is stored in{" "}
                  <span className="font-medium text-foreground">
                    {selectedRegion.name}
                  </span>
                  . All processing stays within this region.
                </div>
              )}
            </CardContent>
          </Card>

          {/* Contact sales */}
          <Card>
            <CardHeader
              title="Contact sales"
              description="Get a custom quote or discuss Enterprise requirements"
            />
            <CardContent>
              {contactSent ? (
                <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-4 py-6 text-center">
                  <CheckCircle2 className="mx-auto h-10 w-10 text-emerald-500" />
                  <p className="mt-2 font-medium text-foreground">
                    Message sent
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Our team will respond within one business day.
                  </p>
                </div>
              ) : (
                <form onSubmit={handleContactSubmit} className="space-y-4">
                  <div className="grid gap-4 sm:grid-cols-2">
                    <Input
                      label="Full name"
                      placeholder="Jane Smith"
                      value={contactName}
                      onChange={(e) => setContactName(e.target.value)}
                    />
                    <Input
                      label="Work email"
                      type="email"
                      placeholder="jane@company.com"
                      value={contactEmail}
                      onChange={(e) => setContactEmail(e.target.value)}
                      required
                    />
                  </div>
                  <Input
                    label="Company"
                    placeholder="Acme Inc."
                    value={contactCompany}
                    onChange={(e) => setContactCompany(e.target.value)}
                  />
                  <div>
                    <label className="mb-1.5 block text-sm font-medium text-muted-foreground">
                      Message
                    </label>
                    <textarea
                      className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground placeholder-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                      placeholder="Tell us about your use case, team size, and any compliance or security requirements..."
                      rows={4}
                      value={contactMessage}
                      onChange={(e) => setContactMessage(e.target.value)}
                    />
                  </div>
                  <Button
                    type="submit"
                    disabled={contactSubmitting || !contactEmail.trim()}
                  >
                    {contactSubmitting ? "Sending…" : "Send message"}
                  </Button>
                </form>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Sidebar: Compliance badges */}
        <div className="space-y-6">
          <Card>
            <CardHeader
              title="Compliance"
              description="Certifications and frameworks"
            />
            <CardContent className="space-y-4">
              {COMPLIANCE.map((c) => (
                <div
                  key={c.id}
                  className="flex gap-4 rounded-lg border border-border bg-background p-4"
                >
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/20">
                    <c.icon className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <p className="font-semibold text-foreground">{c.name}</p>
                    <p className="mt-0.5 text-2xs text-muted-foreground">
                      {c.description}
                    </p>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card className="border-border">
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-primary/20">
                  <Mail className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <p className="font-medium text-foreground">Enterprise support</p>
                  <p className="text-2xs text-muted-foreground">
                    Dedicated success manager and 24/7 critical support
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </>
  );
}
