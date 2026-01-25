import { useVoxera } from "@/store/VoxeraContext";

export function TurnStatePanel() {
  const { systemSpeaking, userSpeaking, bargeIn, audioActive } = useVoxera();

  const sysActive = systemSpeaking || audioActive;
  const state = userSpeaking ? "user" : sysActive ? "system" : "idle";

  return (
    <section className="rounded-xl border border-voxera-border bg-voxera-surface overflow-hidden">
      <div className="px-4 py-3 border-b border-voxera-border bg-voxera-surface-elevated">
        <h2 className="text-sm font-semibold text-slate-200">Turn-Taking</h2>
      </div>
      <div className="p-4 space-y-3">
        <div className="flex items-center gap-2">
          <span
            className={`inline-block w-3 h-3 rounded-full ${
              state === "user"
                ? "bg-blue-500 animate-pulse"
                : state === "system"
                ? "bg-voxera-brand-light animate-pulse"
                : "bg-slate-600"
            }`}
          />
          <span className="text-sm text-slate-200">
            {state === "user"
              ? "User Speaking"
              : state === "system"
              ? "System Speaking"
              : "Idle"}
          </span>
        </div>
        {bargeIn && (
          <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-rose-900/30 border border-rose-700/50">
            <span className="text-rose-400 text-sm font-medium">Barge-in</span>
            <span className="text-xs text-rose-300">User interrupted</span>
          </div>
        )}
      </div>
    </section>
  );
}
