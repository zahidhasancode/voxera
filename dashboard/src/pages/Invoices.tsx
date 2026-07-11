import { Download } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/Table";
import { PageHeader } from "@/components/layout/PageHeader";
import { useBilling } from "@/contexts/BillingContext";

export function Invoices() {
  const { invoices } = useBilling();

  return (
    <>
      <PageHeader title="Invoices" description="Download and view billing history" />
      <Card>
        <CardHeader title="Invoice history" description="Paid and open invoices" />
        <CardContent className="p-0">
          <Table className="border-0 rounded-none">
            <TableHeader>
              <TableRow>
                <TableHead>Number</TableHead>
                <TableHead>Date</TableHead>
                <TableHead>Period</TableHead>
                <TableHead>Amount</TableHead>
                <TableHead>Status</TableHead>
                <TableHead aria-hidden />
              </TableRow>
            </TableHeader>
            <TableBody>
              {invoices.map((inv) => (
                <TableRow key={inv.id}>
                  <TableCell className="font-mono text-sm">{inv.number}</TableCell>
                  <TableCell className="text-muted-foreground">{inv.date}</TableCell>
                  <TableCell className="text-muted-foreground">
                    {inv.periodStart} – {inv.periodEnd}
                  </TableCell>
                  <TableCell>${(inv.amountPaid || inv.amountDue).toFixed(2)}</TableCell>
                  <TableCell>
                    <Badge variant={inv.status === "paid" ? "success" : inv.status === "open" ? "warning" : "default"}>
                      {inv.status}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {inv.invoicePdfUrl && (
                      <a href={inv.invoicePdfUrl} target="_blank" rel="noopener noreferrer">
                        <Button variant="ghost" size="sm">
                          <Download className="h-4 w-4" />
                          PDF
                        </Button>
                      </a>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </>
  );
}
