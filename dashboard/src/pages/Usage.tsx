import { Link } from "react-router-dom";
import { Mic, Cpu, Volume2, Activity } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import { StatCard } from "@/components/ui/StatCard";
import { PageHeader } from "@/components/layout/PageHeader";
import { UsageProgressBar } from "@/components/billing/UsageProgressBar";
import { useOrg } from "@/contexts/OrgContext";
import { useBilling } from "@/contexts/BillingContext";
import { getPlanLimit } from "@/lib/billing";

export function Usage() {
  const { currentOrg } = useOrg();
  const { usage } = useBilling();
  const planId = currentOrg?.plan ?? "free";

  const voiceLimit = getPlanLimit(planId, "voiceMinutes");
  const llmLimit = getPlanLimit(planId, "llmTokens");
  const ttsLimit = getPlanLimit(planId, "ttsSeconds");
  const apiLimit = getPlanLimit(planId, "apiCalls");

  const showUpgrade =
    planId === "free" ||
    (voiceLimit > 0 && usage.voiceMinutes >= voiceLimit * 0.8) ||
    (llmLimit > 0 && usage.llmTokens >= llmLimit * 0.8) ||
    (ttsLimit > 0 && usage.ttsSeconds >= ttsLimit * 0.8) ||
    (apiLimit > 0 && usage.apiCalls >= apiLimit * 0.8);

  const upgradeCta = (
    <Link to="/app/billing">
      <Button size="sm">Upgrade plan</Button>
    </Link>
  );

  return (
    <>
      <PageHeader
        title="Usage"
        description={`Current plan: ${currentOrg?.plan ?? "Free"}. Usage for ${usage.period}.`}
        actions={showUpgrade ? upgradeCta : undefined}
      />

      {showUpgrade && (
        <Alert variant="warning" title="Approaching plan limits" className="mb-6">
          You're near or over a plan limit. Upgrade to avoid overages or service limits.
        </Alert>
      )}

      <div className="mb-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Voice minutes" value={usage.voiceMinutes} icon={Mic} tint="primary" />
        <StatCard label="LLM tokens" value={usage.llmTokens.toLocaleString()} icon={Cpu} tint="accent" />
        <StatCard label="TTS seconds" value={usage.ttsSeconds} icon={Volume2} tint="info" />
        <StatCard label="API calls" value={usage.apiCalls.toLocaleString()} icon={Activity} tint="success" />
      </div>

      <div className="space-y-4">
        <UsageProgressBar label="Voice minutes" used={usage.voiceMinutes} limit={voiceLimit} unit="min" upgradeCta={showUpgrade ? upgradeCta : undefined} />
        <UsageProgressBar label="LLM tokens" used={usage.llmTokens} limit={llmLimit} unit="tokens" upgradeCta={showUpgrade ? upgradeCta : undefined} />
        <UsageProgressBar label="TTS seconds" used={usage.ttsSeconds} limit={ttsLimit} unit="sec" upgradeCta={showUpgrade ? upgradeCta : undefined} />
        <UsageProgressBar label="API calls" used={usage.apiCalls} limit={apiLimit} unit="calls" upgradeCta={showUpgrade ? upgradeCta : undefined} />
      </div>

      <Card className="mt-6">
        <CardHeader title="Usage history" description="Daily breakdown for the current period" />
        <CardContent>
          <p className="py-12 text-center text-sm text-muted-foreground">
            Usage history requires a billing analytics API. Current period totals above reflect real billing context state (zeros until connected).
          </p>
        </CardContent>
      </Card>
    </>
  );
}
