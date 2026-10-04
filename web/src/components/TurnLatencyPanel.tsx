import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { useVoxera } from "@/store/VoxeraContext";

function Row({ label, source, ms }: { label: string; source: string; ms: number | null }) {
  return (
    <div className="flex items-baseline justify-between gap-4">
      <div className="min-w-0">
        <p className="text-sm text-foreground">{label}</p>
        <p className="text-2xs text-muted-foreground">{source}</p>
      </div>
      <span className="shrink-0 font-mono text-sm font-semibold tabular-nums text-foreground">
        {ms === null ? "—" : `${Math.round(ms)} ms`}
      </span>
    </div>
  );
}

export function TurnLatencyPanel() {
  const { lastTurnMetrics, clientLatency } = useVoxera();

  return (
    <Card>
      <CardHeader title="Turn latency" description="Latest turn; — means not measured" />
      <CardContent className="space-y-3">
        <Row
          label="Final transcript → LLM first token"
          source="Reported by the server"
          ms={lastTurnMetrics?.transcript_final_to_llm_first_token_ms ?? null}
        />
        <Row
          label="LLM first token → first audio"
          source="Reported by the server"
          ms={lastTurnMetrics?.llm_first_token_to_first_audio_ms ?? null}
        />
        <Row
          label="Final transcript → first audio"
          source="Reported by the server"
          ms={lastTurnMetrics?.transcript_final_to_first_audio_ms ?? null}
        />
        <div className="border-t border-border pt-3">
          <Row
            label="Final transcript → first audio heard"
            source="Measured in this browser, from the transcript arriving to playback starting (includes the network, the playback jitter buffer and the output delay the browser reports)"
            ms={clientLatency?.finalToFirstAudioMs ?? null}
          />
        </div>
      </CardContent>
    </Card>
  );
}
