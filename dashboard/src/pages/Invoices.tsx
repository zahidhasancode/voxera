import { Download } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { PageHeader } from "@/components/layout/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { useBilling } from "@/contexts/BillingContext";

export function Invoices() {
  const { invoices } = useBilling();

  return (
    <>
      <PageHeader
        title="Invoices"
        description="Download and view billing history"
      />
      <Card>
        <CardHeader
          title="Invoice history"
          description="Paid and open invoices"
        />
        <CardContent className="p-0">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border text-left text-sm text-muted-foreground">
                <th className="px-6 py-3 font-medium">Number</th>
                <th className="px-6 py-3 font-medium">Date</th>
                <th className="px-6 py-3 font-medium">Period</th>
                <th className="px-6 py-3 font-medium">Amount</th>
                <th className="px-6 py-3 font-medium">Status</th>
                <th className="px-6 py-3 font-medium" />
              </tr>
            </thead>
            <tbody>
              {invoices.map((inv) => (
                <tr
                  key={inv.id}
                  className="border-b border-border/50 transition-colors hover:bg-hover/50"
                >
                  <td className="px-6 py-4 font-mono text-sm text-white">
                    {inv.number}
                  </td>
                  <td className="px-6 py-4 text-sm text-muted-foreground">
                    {inv.date}
                  </td>
                  <td className="px-6 py-4 text-sm text-muted-foreground">
                    {inv.periodStart} – {inv.periodEnd}
                  </td>
                  <td className="px-6 py-4 text-sm text-white">
                    ${(inv.amountPaid || inv.amountDue).toFixed(2)}
                  </td>
                  <td className="px-6 py-4">
                    <Badge
                      variant={
                        inv.status === "paid"
                          ? "success"
                          : inv.status === "open"
                          ? "warning"
                          : "default"
                      }
                    >
                      {inv.status}
                    </Badge>
                  </td>
                  <td className="px-6 py-4">
                    {inv.invoicePdfUrl && (
                      <a
                        href={inv.invoicePdfUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        <Button variant="ghost" size="sm">
                          <Download className="mr-2 h-4 w-4" />
                          PDF
                        </Button>
                      </a>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </>
  );
}
