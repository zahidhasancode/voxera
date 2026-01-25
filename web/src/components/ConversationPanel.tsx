import { useRef, useEffect } from "react";
import { useVoxera } from "@/store/VoxeraContext";
import type { Turn } from "@/store/VoxeraContext";

function TurnBubble({ t }: { t: Turn }) {
  const isUser = t.role === "user";
  return (
    <div
      className={`flex ${isUser ? "justify-end" : "justify-start"} transition-opacity duration-200`}
    >
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-3 ${
          isUser
            ? "bg-voxera-brand/30 text-white"
            : t.cancelled
            ? "bg-rose-900/40 text-rose-200 border border-rose-700/50"
            : t.isPartial
            ? "bg-voxera-surface-elevated text-slate-200 border border-voxera-border"
            : "bg-voxera-surface-elevated text-slate-100 border border-voxera-border"
        }`}
      >
        <p className="text-[15px] leading-relaxed whitespace-pre-wrap break-words">{t.text || " "}</p>
        {t.isPartial && (
          <span className="inline-block mt-1 w-2 h-4 bg-voxera-brand-light animate-pulse-soft" />
        )}
        {t.cancelled && (
          <span className="block mt-1 text-xs text-rose-400">Interrupted</span>
        )}
      </div>
    </div>
  );
}

export function ConversationPanel() {
  const { turns } = useVoxera();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns]);

  return (
    <section className="flex flex-col h-full bg-voxera-surface rounded-xl border border-voxera-border overflow-hidden">
      <div className="px-4 py-3 border-b border-voxera-border bg-voxera-surface-elevated">
        <h2 className="text-sm font-semibold text-slate-200">Conversation</h2>
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {turns.length === 0 ? (
          <div className="flex items-center justify-center h-32 text-voxera-muted text-sm">
            Connect and send a test transcript to start.
          </div>
        ) : (
          turns.map((t) => <TurnBubble key={t.id} t={t} />)
        )}
        <div ref={bottomRef} />
      </div>
    </section>
  );
}
