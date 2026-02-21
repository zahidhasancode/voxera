import { useEffect } from "react";
import { Monitor, Smartphone } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { PageHeader } from "@/components/layout/PageHeader";
import { useAuth } from "@/contexts/AuthContext";
import { Badge } from "@/components/ui/Badge";

export function Sessions() {
  const { sessions, fetchSessions, revokeSession } = useAuth();

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  return (
    <>
      <PageHeader
        title="Sessions"
        description="Manage active sessions and devices"
      />
      <Card>
        <CardHeader
          title="Active sessions"
          description="Revoke any session to sign it out. You will stay signed in on this device."
        />
        <CardContent className="p-0">
          <ul className="divide-y divide-border">
            {sessions.map((s) => (
              <li
                key={s.id}
                className="flex flex-col gap-2 px-6 py-4 sm:flex-row sm:items-center sm:justify-between"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-border">
                    {s.device.toLowerCase().includes("iphone") ? (
                      <Smartphone className="h-5 w-5 text-muted-foreground" />
                    ) : (
                      <Monitor className="h-5 w-5 text-muted-foreground" />
                    )}
                  </div>
                  <div>
                    <p className="font-medium text-white">{s.device}</p>
                    {s.location && (
                      <p className="text-sm text-muted-foreground">{s.location}</p>
                    )}
                    <p className="text-2xs text-muted-foreground">
                      Last active {new Date(s.lastActiveAt).toLocaleString()}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {s.current && (
                    <Badge variant="success">Current</Badge>
                  )}
                  {!s.current && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => revokeSession(s.id)}
                    >
                      Revoke
                    </Button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </>
  );
}
