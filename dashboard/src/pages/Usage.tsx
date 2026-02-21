import { Link } from "react-router-dom";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
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
        actions={
          showUpgrade ? (
            <Link to="/app/billing">
              <Button>Upgrade plan</Button>
            </Link>
          ) : null
        }
      />

      <div className="mb-6 rounded-xl border border-border bg-gradient-to-b from-card to-background p-6">
        <h2 className="text-sm font-medium text-muted-foreground">
          Usage this period
        </h2>
        <p className="mt-1 text-2xl font-semibold text-white">
          {usage.period}
        </p>
        {showUpgrade && (
          <p className="mt-2 text-sm text-amber-400">
            You're near or over a plan limit. Upgrade to avoid overages or service limits.
          </p>
        )}
      </div>

      <div className="space-y-4">
        <UsageProgressBar
          label="Voice minutes"
          used={usage.voiceMinutes}
          limit={voiceLimit}
          unit="min"
          upgradeCta={showUpgrade ? upgradeCta : undefined}
        />
        <UsageProgressBar
          label="LLM tokens"
          used={usage.llmTokens}
          limit={llmLimit}
          unit="tokens"
          upgradeCta={showUpgrade ? upgradeCta : undefined}
        />
        <UsageProgressBar
          label="TTS seconds"
          used={usage.ttsSeconds}
          limit={ttsLimit}
          unit="sec"
          upgradeCta={showUpgrade ? upgradeCta : undefined}
        />
        <UsageProgressBar
          label="API calls"
          used={usage.apiCalls}
          limit={apiLimit}
          unit="calls"
          upgradeCta={showUpgrade ? upgradeCta : undefined}
        />
      </div>

      <Card className="mt-6">
        <CardHeader
          title="Usage history"
          description="Daily breakdown (connect to your usage API for real data)"
        />
        <CardContent>
          <div className="flex h-48 items-center justify-center rounded-lg border border-border text-sm text-muted-foreground">
            Chart placeholder — time-series by voice min, tokens, TTS, API
          </div>
        </CardContent>
      </Card>
    </>
  );
}
