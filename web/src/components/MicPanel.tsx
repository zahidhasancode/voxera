import { Mic, MicOff } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { Alert } from "@/components/ui/Alert";
import { useVoxera } from "@/store/VoxeraContext";

/** Map frame RMS (0..1) to a 0..100 meter width on a dB scale, -60 dBFS → 0, 0 dBFS → 100. */
function levelPercent(rms: number): number {
  if (rms <= 0) return 0;
  const db = 20 * Math.log10(rms);
  return Math.max(0, Math.min(100, ((db + 60) / 60) * 100));
}

export function MicPanel() {
  const { connectionStatus, micStatus, micError, micLevel, systemSpeaking, startMic, stopMic } =
    useVoxera();

  const connected = connectionStatus === "connected";
  const on = micStatus === "on";
  const starting = micStatus === "starting";

  function toggleMic() {
    if (!connected) return;
    if (micStatus === "off") void startMic();
    else stopMic();
  }

  const hint = !connected
    ? "Connect to start a voice session"
    : starting
    ? "Waiting for microphone access…"
    : on
    ? systemSpeaking
      ? "Microphone is live. Speak to interrupt the assistant."
      : "Microphone is live. Just speak."
    : "Tap to turn the microphone on";

  return (
    <Card>
      <CardHeader
        title="Voice input"
        description="Live microphone, streamed to the server while it is on"
      />
      <CardContent className="space-y-4">
        {micError && <Alert variant="error">{micError}</Alert>}
        <div className="flex flex-col items-center gap-4 py-4">
          <button
            type="button"
            onClick={toggleMic}
            disabled={!connected}
            aria-pressed={on}
            className={`flex h-20 w-20 items-center justify-center rounded-full transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary ${
              on
                ? "bg-destructive text-primary-foreground animate-glow-speaking"
                : starting
                ? "bg-primary text-primary-foreground animate-pulse-soft"
                : "bg-primary text-primary-foreground hover:opacity-90"
            } disabled:opacity-40`}
            aria-label={micStatus === "off" ? "Turn microphone on" : "Turn microphone off"}
          >
            {on ? <MicOff className="h-8 w-8" /> : <Mic className="h-8 w-8" />}
          </button>
          <p className="text-center text-sm text-muted-foreground">{hint}</p>
          {on && (
            <div className="w-full">
              <div
                className="h-2 w-full overflow-hidden rounded-full bg-muted"
                role="meter"
                aria-label="Microphone level"
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={Math.round(levelPercent(micLevel))}
              >
                <div
                  className="h-full rounded-full bg-primary transition-all duration-150"
                  style={{ width: `${levelPercent(micLevel)}%` }}
                />
              </div>
              <p className="mt-1 text-center text-2xs text-muted-foreground">
                Microphone level
              </p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
