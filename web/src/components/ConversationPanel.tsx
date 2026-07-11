import { useRef, useEffect, useState } from "react";
import { Avatar } from "@/components/ui/Avatar";
import { EmptyState } from "@/components/ui/EmptyState";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Mic } from "lucide-react";
import { useVoxera } from "@/store/VoxeraContext";
import type { Turn } from "@/store/VoxeraContext";

function TurnBubble({ t }: { t: Turn }) {
  const isUser = t.role === "user";
  const time = new Date(t.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : "flex-row"}`}>
      <Avatar name={isUser ? "You" : "Agent"} size="sm" />
      <div className={`max-w-[80%] ${isUser ? "items-end" : "items-start"} flex flex-col`}>
        <div
          className={`rounded-2xl px-4 py-3 ${
            isUser
              ? "rounded-tr-sm bg-primary text-primary-foreground"
              : t.cancelled
              ? "rounded-tl-sm border border-destructive/30 bg-destructive-muted/30 text-foreground"
              : "rounded-tl-sm border border-border bg-muted/50 text-foreground"
          }`}
        >
          <p className="text-sm leading-relaxed whitespace-pre-wrap break-words" aria-live={t.isPartial ? "polite" : "off"}>
            {t.text || " "}
          </p>
          {t.isPartial && (
            <span className="inline-block mt-1 h-4 w-0.5 animate-pulse bg-primary" />
          )}
          {t.cancelled && (
            <span className="mt-1 block text-2xs text-destructive">Interrupted</span>
          )}
        </div>
        <span className="mt-1 text-2xs text-muted-foreground">{time}</span>
      </div>
    </div>
  );
}

export function ConversationPanel() {
  const { turns, connectionStatus } = useVoxera();
  const bottomRef = useRef<HTMLDivElement>(null);
  const [showJump, setShowJump] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!showJump) bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns, showJump]);

  return (
    <Card className="flex h-full min-h-[360px] flex-col overflow-hidden">
      <CardHeader title="Conversation" description="Real-time voice dialogue" />
      <CardContent className="relative flex-1 overflow-hidden p-0">
        <div
          ref={containerRef}
          className="h-full max-h-[480px] overflow-y-auto p-4 space-y-4"
          onScroll={() => setShowJump(true)}
        >
          {turns.length === 0 ? (
            <EmptyState
              variant="dashed"
              icon={<Mic className="h-6 w-6" />}
              title="No conversation yet"
              description={
                connectionStatus === "connected"
                  ? "Tap the microphone or send a test message to begin."
                  : "Connect to the VOXERA backend to start."
              }
            />
          ) : (
            turns.map((t) => <TurnBubble key={t.id} t={t} />)
          )}
          <div ref={bottomRef} />
        </div>
        {showJump && turns.length > 0 && (
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2">
            <Button size="sm" variant="secondary" onClick={() => { setShowJump(false); bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }}>
              Jump to latest
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
