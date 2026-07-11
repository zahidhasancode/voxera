import { Mic, MicOff } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { Alert } from "@/components/ui/Alert";
import { useVoxera } from "@/store/VoxeraContext";

export function MicPanel() {
  const { connectionStatus, sendDevTestTranscript } = useVoxera();
  const [listening, setListening] = useState(false);
  const [permissionError, setPermissionError] = useState<string | null>(null);

  async function toggleMic() {
    if (connectionStatus !== "connected") return;
    if (!listening) {
      try {
        await navigator.mediaDevices.getUserMedia({ audio: true });
        setPermissionError(null);
        setListening(true);
        sendDevTestTranscript("Hello, I'd like help with my order.");
      } catch {
        setPermissionError("Microphone permission denied. Enable mic access to use voice.");
      }
    } else {
      setListening(false);
    }
  }

  return (
    <Card>
      <CardHeader title="Voice input" description="Push to talk (demo uses test transcript)" />
      <CardContent className="space-y-4">
        {permissionError && (
          <Alert variant="error">{permissionError}</Alert>
        )}
        <div className="flex flex-col items-center gap-4 py-4">
          <button
            type="button"
            onClick={toggleMic}
            disabled={connectionStatus !== "connected"}
            className={`flex h-20 w-20 items-center justify-center rounded-full transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary ${
              listening
                ? "bg-destructive text-primary-foreground animate-glow-speaking"
                : "bg-primary text-primary-foreground hover:opacity-90"
            } disabled:opacity-40`}
            aria-label={listening ? "Stop listening" : "Start listening"}
          >
            {listening ? <MicOff className="h-8 w-8" /> : <Mic className="h-8 w-8" />}
          </button>
          <p className="text-sm text-muted-foreground">
            {listening ? "Listening…" : "Tap to speak"}
          </p>
          {listening && (
            <div className="flex h-8 items-end gap-1">
              {Array.from({ length: 16 }).map((_, i) => (
                <div
                  key={i}
                  className="w-1 rounded-full bg-primary animate-pulse-soft"
                  style={{ height: `${8 + Math.sin(i) * 12}px`, animationDelay: `${i * 40}ms` }}
                />
              ))}
            </div>
          )}
        </div>
        {connectionStatus !== "connected" && (
          <p className="text-center text-2xs text-muted-foreground">Connect to start a voice session</p>
        )}
        {import.meta.env.DEV && (
          <Button
            variant="outline"
            size="sm"
            className="w-full"
            disabled={connectionStatus !== "connected"}
            onClick={() => sendDevTestTranscript("What are your business hours?")}
          >
            Send test transcript
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
