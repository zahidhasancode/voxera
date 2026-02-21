import { MessageSquare, BookOpen, Key, TrendingUp } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { useOrg } from "@/contexts/OrgContext";

const stats = [
  { label: "Active agents", value: "3", icon: MessageSquare, href: "/app/agents" },
  { label: "Knowledge articles", value: "12", icon: BookOpen, href: "/app/knowledge" },
  { label: "API keys", value: "2", icon: Key, href: "/app/api-keys" },
  { label: "Voice minutes (30d)", value: "1,240", icon: TrendingUp, href: "/app/usage" },
];

export function Overview() {
  const { currentOrg } = useOrg();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const t = setTimeout(() => setLoading(false), 500);
    return () => clearTimeout(t);
  }, []);

  if (loading) {
    return (
      <>
        <div className="mb-8">
          <Skeleton className="mb-2 h-7 w-48" />
          <Skeleton className="h-4 w-64" />
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i}>
              <CardContent className="flex items-center gap-4 p-6">
                <Skeleton className="h-10 w-10 rounded-xl" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-7 w-16" />
                  <Skeleton className="h-4 w-24" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
        <Card className="mt-6">
          <CardHeader title="Recent activity" description="Latest conversations and usage" />
          <CardContent className="space-y-3">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-4/5" />
            <Skeleton className="h-4 w-3/5" />
          </CardContent>
        </Card>
      </>
    );
  }

  return (
    <>
      <div className="mb-8">
        <h1 className="text-xl font-semibold tracking-tight text-foreground">
          Overview
        </h1>
        <p className="mt-0.5 text-sm text-muted-foreground">
          {currentOrg?.name} — {currentOrg?.plan} plan
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map(({ label, value, icon: Icon, href }) => (
          <Link key={href} to={href}>
            <Card className="transition-colors duration-200 hover:border-muted-foreground/30">
              <CardContent className="flex items-center gap-4 p-6">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/20">
                  <Icon className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <p className="text-2xl font-semibold text-foreground">{value}</p>
                  <p className="text-sm text-muted-foreground">{label}</p>
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      <Card className="mt-6">
        <CardHeader
          title="Recent activity"
          description="Latest conversations and usage"
        />
        <CardContent>
          <div className="rounded-xl border border-border bg-hover/30 p-8 text-center text-sm text-muted-foreground">
            No recent activity. Connect an agent or run a test call to see data here.
          </div>
        </CardContent>
      </Card>
    </>
  );
}
