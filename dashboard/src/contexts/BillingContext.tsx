import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type { Invoice, PaymentMethod, UsageSummary } from "@/types";

interface BillingContextValue {
  /** Create Stripe Checkout session and redirect. In production, call your backend. */
  createCheckoutSession: (
    priceId: string,
    successUrl: string,
    cancelUrl: string,
    interval: "month" | "year"
  ) => Promise<void>;
  /** Open Stripe Customer Portal. In production, backend returns portal URL. */
  openBillingPortal: () => Promise<void>;
  usage: UsageSummary;
  invoices: Invoice[];
  paymentMethods: PaymentMethod[];
  setDefaultPaymentMethod: (id: string) => void;
}

const BillingContext = createContext<BillingContextValue | null>(null);

const EMPTY_USAGE: UsageSummary = {
  voiceMinutes: 0,
  llmTokens: 0,
  ttsSeconds: 0,
  apiCalls: 0,
  period: new Date().toLocaleString(undefined, { month: "long", year: "numeric" }),
};

export function BillingProvider({ children }: { children: ReactNode }) {
  const [usage] = useState<UsageSummary>(EMPTY_USAGE);
  const [invoices] = useState<Invoice[]>([]);
  const [paymentMethods, setPaymentMethodsState] = useState<PaymentMethod[]>([]);

  const createCheckoutSession = useCallback(
    async (_priceId: string, _successUrl: string, _cancelUrl: string, _interval: "month" | "year") => {
      // In production: POST /api/billing/create-checkout-session { priceId, successUrl, cancelUrl }
      // then redirect to session.url
      await new Promise((r) => setTimeout(r, 300));
      window.open("https://billing.stripe.com/p/login/test", "_blank");
    },
    []
  );

  const openBillingPortal = useCallback(async () => {
    // In production: POST /api/billing/create-portal-session { returnUrl }
    // then redirect to session.url
    await new Promise((r) => setTimeout(r, 300));
    window.open("https://billing.stripe.com/p/login/test", "_blank");
  }, []);

  const setDefaultPaymentMethod = useCallback((id: string) => {
    setPaymentMethodsState((prev) =>
      prev.map((pm) => ({ ...pm, isDefault: pm.id === id }))
    );
  }, []);

  const value: BillingContextValue = useMemo(
    () => ({
      createCheckoutSession,
      openBillingPortal,
      usage,
      invoices,
      paymentMethods,
      setDefaultPaymentMethod,
    }),
    [createCheckoutSession, openBillingPortal, usage, invoices, paymentMethods, setDefaultPaymentMethod]
  );

  return (
    <BillingContext.Provider value={value}>{children}</BillingContext.Provider>
  );
}

export function useBilling(): BillingContextValue {
  const ctx = useContext(BillingContext);
  if (!ctx) throw new Error("useBilling must be used within BillingProvider");
  return ctx;
}
