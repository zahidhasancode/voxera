import { useState } from "react";
import { Link } from "react-router-dom";
import { Check, CreditCard, FileText, ExternalLink } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { PageHeader } from "@/components/layout/PageHeader";
import { useOrg } from "@/contexts/OrgContext";
import { useBilling } from "@/contexts/BillingContext";
import { PLANS, getPlan } from "@/lib/billing";
import type { PlanId } from "@/types";

export function Billing() {
  const { currentOrg } = useOrg();
  const { openBillingPortal, paymentMethods, createCheckoutSession } = useBilling();
  const [billingInterval, setBillingInterval] = useState<"month" | "year">(
    currentOrg?.billingInterval ?? "month"
  );
  const [portalLoading, setPortalLoading] = useState(false);

  const currentPlanId = (currentOrg?.plan ?? "free") as PlanId;
  const currentPlan = getPlan(currentPlanId);

  const handleOpenPortal = async () => {
    setPortalLoading(true);
    try {
      await openBillingPortal();
    } finally {
      setPortalLoading(false);
    }
  };

  const handleUpgrade = async (planId: PlanId) => {
    const plan = getPlan(planId);
    if (plan.contactSales) {
      window.location.href = "mailto:sales@voxera.com?subject=Enterprise%20plan";
      return;
    }
    const priceId =
      billingInterval === "year"
        ? plan.stripePriceIdYearly
        : plan.stripePriceIdMonthly;
    if (!priceId) return;
    await createCheckoutSession(
      priceId,
      `${window.location.origin}/billing?success=true`,
      `${window.location.origin}/billing`,
      billingInterval
    );
  };

  return (
    <>
      <PageHeader
        title="Billing"
        description="Manage your subscription, payment methods, and invoices"
      />

      {/* Current plan — premium card */}
      <Card className="mb-6 overflow-hidden border-primary/30 bg-gradient-to-b from-card to-background">
        <div className="border-b border-border bg-hover/50 px-6 py-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h2 className="text-lg font-semibold text-foreground">
                Current plan
              </h2>
              <p className="mt-0.5 text-sm text-muted-foreground">
                {currentPlan.name}
                {currentPlan.contactSales
                  ? " — Contact sales for custom pricing"
                  : billingInterval === "year"
                  ? " — Billed annually"
                  : " — Billed monthly"}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="secondary"
                onClick={handleOpenPortal}
                disabled={portalLoading}
              >
                {portalLoading ? "Opening…" : "Manage subscription"}
              </Button>
              <Link to="/app/billing/invoices">
                <Button variant="ghost" size="sm">
                  <FileText className="mr-2 h-4 w-4" />
                  Invoices
                </Button>
              </Link>
            </div>
          </div>
        </div>
        <CardContent className="p-6">
          <p className="text-sm text-muted-foreground">
            Update payment method, change plan, or cancel from the secure Stripe billing portal.
          </p>
          <p className="mt-2 flex items-center gap-1.5 text-2xs text-muted-foreground">
            <CreditCard className="h-3.5 w-3.5" />
            Secured by Stripe. Your payment data is never stored on our servers.
          </p>
        </CardContent>
      </Card>

      {/* Payment methods */}
      <Card className="mb-6">
        <CardHeader
          title="Payment methods"
          description="Cards on file. Manage in billing portal."
        />
        <CardContent className="p-0">
          <ul className="divide-y divide-border">
            {paymentMethods.map((pm) => (
              <li
                key={pm.id}
                className="flex items-center justify-between px-6 py-4"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-14 items-center justify-center rounded-lg border border-border bg-card">
                    <CreditCard className="h-5 w-5 text-muted-foreground" />
                  </div>
                  <div>
                    <p className="font-medium capitalize text-foreground">
                      {pm.brand} •••• {pm.last4}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      Expires {String(pm.expMonth).padStart(2, "0")}/{pm.expYear}
                      {pm.isDefault && (
                        <span className="ml-2 text-primary-light">Default</span>
                      )}
                    </p>
                  </div>
                </div>
              </li>
            ))}
          </ul>
          <div className="border-t border-border p-4">
            <Button variant="secondary" size="sm" onClick={handleOpenPortal}>
              <ExternalLink className="mr-2 h-4 w-4" />
              Add or update in portal
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Pricing plans */}
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-foreground">Plans</h2>
        <div className="flex rounded-lg border border-border p-0.5">
          <button
            type="button"
            onClick={() => setBillingInterval("month")}
            className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
              billingInterval === "month"
                ? "bg-border text-foreground"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            Monthly
          </button>
          <button
            type="button"
            onClick={() => setBillingInterval("year")}
            className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
              billingInterval === "year"
                ? "bg-border text-foreground"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            Yearly
            <span className="ml-1.5 text-2xs text-emerald-400">Save 20%</span>
          </button>
        </div>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {PLANS.map((plan) => {
          const isCurrent = plan.id === currentPlanId;
          const price =
            billingInterval === "year" ? plan.priceYearly : plan.priceMonthly;
          return (
            <Card
              key={plan.id}
              className={`flex flex-col ${
                isCurrent ? "ring-1 ring-primary" : ""
              }`}
            >
              <CardHeader
                title={plan.name}
                description={
                  plan.contactSales
                    ? "Contact sales"
                    : price === 0
                    ? "Free"
                    : billingInterval === "year"
                    ? `$${price}/year`
                    : `$${price}/month`
                }
              />
              <CardContent className="flex flex-1 flex-col space-y-4">
                <ul className="space-y-2 text-sm text-muted-foreground">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-center gap-2">
                      <Check className="h-4 w-4 shrink-0 text-primary" />
                      {f}
                    </li>
                  ))}
                </ul>
                <div className="mt-auto pt-2">
                  {plan.contactSales ? (
                    <Button
                      variant="secondary"
                      className="w-full"
                      onClick={() => handleUpgrade(plan.id)}
                    >
                      Contact sales
                    </Button>
                  ) : (
                    <Button
                      variant={isCurrent ? "secondary" : "primary"}
                      size="sm"
                      className="w-full"
                      disabled={isCurrent}
                      onClick={() => handleUpgrade(plan.id)}
                    >
                      {isCurrent ? "Current plan" : "Upgrade"}
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </>
  );
}
