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

const MOCK_USAGE: UsageSummary = {
  voiceMinutes: 3240,
  llmTokens: 420_000,
  ttsSeconds: 5400,
  apiCalls: 28_500,
  period: "March 2024",
};

const MOCK_INVOICES: Invoice[] = [
  { id: "in_1", number: "INV-2024-003", amountDue: 0, amountPaid: 199, status: "paid", date: "2024-03-01", periodStart: "2024-03-01", periodEnd: "2024-03-31", invoicePdfUrl: "#" },
  { id: "in_2", number: "INV-2024-002", amountDue: 0, amountPaid: 199, status: "paid", date: "2024-02-01", periodStart: "2024-02-01", periodEnd: "2024-02-29", invoicePdfUrl: "#" },
  { id: "in_3", number: "INV-2024-001", amountDue: 0, amountPaid: 199, status: "paid", date: "2024-01-01", periodStart: "2024-01-01", periodEnd: "2024-01-31", invoicePdfUrl: "#" },
];

const MOCK_PAYMENT_METHODS: PaymentMethod[] = [
  { id: "pm_1", brand: "visa", last4: "4242", expMonth: 12, expYear: 2026, isDefault: true },
  { id: "pm_2", brand: "mastercard", last4: "5555", expMonth: 6, expYear: 2025, isDefault: false },
];

export function BillingProvider({ children }: { children: ReactNode }) {
  const [usage] = useState<UsageSummary>(MOCK_USAGE);
  const [invoices] = useState<Invoice[]>(MOCK_INVOICES);
  const [paymentMethods, setPaymentMethodsState] = useState<PaymentMethod[]>(MOCK_PAYMENT_METHODS);

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
