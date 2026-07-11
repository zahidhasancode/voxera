import { BarChart3 } from "lucide-react";
import { Card, CardContent } from "@/components/ui/Card";
import { PageHeader } from "@/components/layout/PageHeader";
import { EmptyState } from "@/components/ui/EmptyState";

export function Analytics() {
  return (
    <>
      <PageHeader
        title="Analytics"
        description="Call volume, latency, cost, and agent performance"
      />
      <Card>
        <CardContent className="p-8">
          <EmptyState
            icon={<BarChart3 className="h-6 w-6" />}
            title="Analytics not connected"
            description="Usage analytics and time-series metrics require a billing/analytics API that is not yet exposed by the backend. Dashboard operational metrics are available on the Overview page."
          />
        </CardContent>
      </Card>
    </>
  );
}
