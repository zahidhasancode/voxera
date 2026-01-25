import { useVoxera } from "@/store/VoxeraContext";

export function AudioPanel() {
  const { audioFrameCount, audioActive } = useVoxera();

  return (
    <section
      className={`rounded-xl border overflow-hidden transition-all duration-300 ${
        audioActive
          ? "border-voxera-brand-light bg-voxera-brand/10 animate-glow-speaking"
          : "border-voxera-border bg-voxera-surface"
      }`}
    >
      <div className="px-4 py-3 border-b border-voxera-border bg-voxera-surface-elevated flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-200">Audio Playback</h2>
        <div className="flex items-center gap-2">
          <span
            className={`inline-block w-2 h-2 rounded-full ${
              audioActive ? "bg-voxera-brand-light animate-pulse" : "bg-slate-500"
            }`}
          />
          <span className="text-xs text-voxera-muted">
            {audioActive ? "Playing" : "Idle"}
          </span>
        </div>
      </div>
      <div className="p-4 flex items-center justify-between">
        <div>
          <p className="text-2xl font-mono font-semibold text-white">{audioFrameCount}</p>
          <p className="text-xs text-voxera-muted">frames played</p>
        </div>
        <div
          className={`w-12 h-12 rounded-full flex items-center justify-center ${
            audioActive ? "bg-voxera-brand/30" : "bg-voxera-surface-elevated"
          }`}
        >
          <svg
            viewBox="0 0 24 24"
            className={`w-6 h-6 ${audioActive ? "text-voxera-brand-light" : "text-voxera-muted"}`}
            fill="currentColor"
          >
            <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z" />
          </svg>
        </div>
      </div>
    </section>
  );
}
