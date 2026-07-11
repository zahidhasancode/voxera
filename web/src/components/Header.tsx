import { Shield } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { ThemeToggle } from "@/components/ui/ThemeToggle";
import { useVoxera } from "@/store/VoxeraContext";

export function Header() {
  const { connectionStatus, connect, disconnect, connectionError } = useVoxera();

  const statusVariant =
    connectionStatus === "connected"
      ? "success"
      : connectionStatus === "connecting"
      ? "warning"
      : connectionError
      ? "error"
      : "default";

  const statusLabel =
    connectionStatus === "connected"
      ? "Connected"
      : connectionStatus === "connecting"
      ? "Connecting…"
      : connectionError
      ? "Error"
      : "Disconnected";

  return (
    <header className="sticky top-0 z-30 flex items-center justify-between border-b border-border bg-background/95 px-4 py-3 backdrop-blur-sm sm:px-6">
      <div className="flex items-center gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary">
          <Shield className="h-5 w-5 text-primary-foreground" />
        </div>
        <div>
          <span className="text-lg font-semibold text-foreground">VOXERA</span>
          <p className="text-2xs text-muted-foreground">Voice demo</p>
        </div>
        {import.meta.env.DEV && (
          <Badge variant="warning">Dev</Badge>
        )}
      </div>

      <div className="flex items-center gap-3">
        <Badge variant={statusVariant}>{statusLabel}</Badge>
        <ThemeToggle />
        {connectionStatus === "connected" ? (
          <Button variant="outline" size="sm" onClick={disconnect}>
            Disconnect
          </Button>
        ) : (
          <Button size="sm" onClick={connect} loading={connectionStatus === "connecting"}>
            Connect
          </Button>
        )}
      </div>
    </header>
  );
}
