import { useVoxera } from "@/store/VoxeraContext";

export function Header() {
  const { connectionStatus, connect, disconnect } = useVoxera();

  return (
    <header className="flex items-center justify-between px-6 py-4 border-b border-voxera-border bg-voxera-surface-elevated">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-voxera-brand flex items-center justify-center">
            <svg viewBox="0 0 24 24" className="w-5 h-5 text-white" fill="currentColor">
              <path d="M12 2a3 3 0 0 1 3 3v2.18a3 3 0 0 1 1.5 5.194v.612a3 3 0 0 1-1.5 5.194V18a3 3 0 0 1-6 0v-.612a3 3 0 0 1-1.5-5.194v-.612A3 3 0 0 1 9 7.18V5a3 3 0 0 1 3-3z" />
            </svg>
          </div>
          <span className="text-lg font-semibold text-white">Voxera</span>
        </div>
        <span className="text-xs px-2 py-0.5 rounded bg-amber-500/20 text-amber-400 font-medium">Dev</span>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <span
            className={`inline-block w-2 h-2 rounded-full ${
              connectionStatus === "connected"
                ? "bg-latency-good animate-pulse"
                : connectionStatus === "connecting"
                ? "bg-amber-500 animate-pulse-soft"
                : "bg-slate-500"
            }`}
          />
          <span className="text-sm text-voxera-muted">
            {connectionStatus === "connected"
              ? "Connected"
              : connectionStatus === "connecting"
              ? "Connecting…"
              : "Disconnected"}
          </span>
        </div>
        {connectionStatus === "connected" ? (
          <button
            onClick={disconnect}
            className="text-sm px-3 py-1.5 rounded-md border border-voxera-border text-voxera-muted hover:bg-voxera-border/30 hover:text-white transition-colors"
          >
            Disconnect
          </button>
        ) : (
          <button
            onClick={connect}
            disabled={connectionStatus === "connecting"}
            className="text-sm px-3 py-1.5 rounded-md bg-voxera-brand hover:bg-voxera-brand-light text-white transition-colors disabled:opacity-50"
          >
            Connect
          </button>
        )}
      </div>
    </header>
  );
}
