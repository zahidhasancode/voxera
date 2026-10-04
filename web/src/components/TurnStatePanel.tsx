import { Avatar } from "@/components/ui/Avatar";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { useVoxera } from "@/store/VoxeraContext";

export function TurnStatePanel() {
  const { userSpeaking, systemSpeaking, bargeIn, connectionStatus, providers } = useVoxera();

  const state =
    bargeIn
      ? { label: "Barge-in", badge: "error" as const, desc: "User interrupted the agent" }
      : userSpeaking
      ? { label: "Listening", badge: "success" as const, desc: "The server is transcribing speech" }
      : systemSpeaking
      ? { label: "Speaking", badge: "brand" as const, desc: "Assistant audio is playing" }
      : connectionStatus === "connected"
      ? { label: "Idle", badge: "default" as const, desc: "Ready for next turn" }
      : { label: "Offline", badge: "default" as const, desc: "Not connected" };

  return (
    <Card>
      <CardHeader title="Session status" />
      <CardContent>
        <div className="flex items-center gap-4">
          <Avatar name="Session" size="md" />
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <Badge variant={state.badge}>{state.label}</Badge>
              {systemSpeaking && (
                <span className="h-2 w-2 rounded-full bg-primary animate-pulse-soft" aria-hidden />
              )}
            </div>
            <p className="mt-1 text-sm text-muted-foreground">{state.desc}</p>
          </div>
        </div>
        {connectionStatus === "connected" && (
          <dl className="mt-4 grid grid-cols-3 gap-2 border-t border-border pt-4">
            {(["stt", "llm", "tts"] as const).map((kind) => {
              const name = providers?.[kind] ?? null;
              return (
                <div key={kind} className="min-w-0">
                  <dt className="text-2xs font-medium uppercase tracking-wider text-muted-foreground">
                    {kind}
                  </dt>
                  <dd className="mt-1">
                    <Badge variant={name === "mock" ? "warning" : "default"}>{name ?? "—"}</Badge>
                  </dd>
                </div>
              );
            })}
          </dl>
        )}
      </CardContent>
    </Card>
  );
}
