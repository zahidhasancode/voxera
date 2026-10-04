import type { BillingPlan, PlanId } from "@/types";

export const PLANS: BillingPlan[] = [
  {
    id: "free",
    name: "Free",
    priceMonthly: 0,
    priceYearly: 0,
    limits: { voiceMinutes: 100, llmTokens: 50_000, ttsSeconds: 3_600, apiCalls: 1_000 },
    features: ["1 agent", "Basic analytics", "Community support"],
  },
  {
    id: "pro",
    name: "Pro",
    priceMonthly: 299,
    priceYearly: 2_990,
    stripePriceIdMonthly: "price_pro_monthly",
    stripePriceIdYearly: "price_pro_yearly",
    limits: { voiceMinutes: 5_000, llmTokens: 2_000_000, ttsSeconds: 180_000, apiCalls: 50_000 },
    features: ["10 agents", "Live call center", "Workflow engine", "Priority support"],
  },
  {
    id: "business",
    name: "Business",
    priceMonthly: 899,
    priceYearly: 8_990,
    stripePriceIdMonthly: "price_business_monthly",
    stripePriceIdYearly: "price_business_yearly",
    limits: { voiceMinutes: 25_000, llmTokens: 10_000_000, ttsSeconds: 900_000, apiCalls: 250_000 },
    features: ["Unlimited agents", "SSO", "Audit logs", "Dedicated support"],
  },
  {
    id: "enterprise",
    name: "Enterprise",
    priceMonthly: 0,
    priceYearly: 0,
    limits: { voiceMinutes: 0, llmTokens: 0, ttsSeconds: 0, apiCalls: 0 },
    features: ["Custom SLA", "Private deployment", "Compliance pack", "Solutions architect"],
    contactSales: true,
  },
];

export function getPlan(planId: PlanId): BillingPlan {
  return PLANS.find((p) => p.id === planId) ?? PLANS[0];
}

export function getPlanLimit(planId: PlanId, key: keyof BillingPlan["limits"]): number {
  return getPlan(planId).limits[key];
}
