import { Alert } from "@/components/ui/Alert";
import {
  Header,
  ConversationPanel,
  TurnStatePanel,
  MetricsDashboard,
  DevControls,
} from "./components";
import { MicPanel } from "./components/MicPanel";
import { TurnLatencyPanel } from "./components/TurnLatencyPanel";
import { useVoxera } from "./store/VoxeraContext";

function App() {
  const { connectionError, serverError, dismissServerError, audioFormatError, providers } =
    useVoxera();

  const mockNotes: string[] = [];
  if (providers?.stt === "mock") {
    mockNotes.push("Speech-to-text is a mock: the transcript is random words, not what you said.");
  }
  if (providers?.llm === "mock") {
    mockNotes.push("The language model is a mock: replies do not come from a real model.");
  }
  if (providers?.tts === "mock") {
    mockNotes.push("Text-to-speech is a mock: the reply audio is a tone, not a voice.");
  }

  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-[100] focus:rounded-lg focus:bg-primary focus:px-4 focus:py-2 focus:text-primary-foreground"
      >
        Skip to content
      </a>
      <Header />

      <main id="main-content" className="flex-1 overflow-auto p-4 sm:p-6">
        <div className="mx-auto max-w-wide space-y-6">
          {connectionError && (
            <Alert variant="error" title="Connection failed">
              {connectionError}. Check that the backend is running on port 8000.
            </Alert>
          )}

          {mockNotes.length > 0 && (
            <Alert variant="warning" title="Mock providers">
              {mockNotes.join(" ")}
            </Alert>
          )}

          {audioFormatError && (
            <Alert variant="error" title="Audio format mismatch">
              {audioFormatError}
            </Alert>
          )}

          {serverError && (
            <Alert
              variant="error"
              title={`Server error: ${serverError.code}`}
              onDismiss={dismissServerError}
            >
              {serverError.message}
            </Alert>
          )}

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <ConversationPanel />
            </div>
            <div className="space-y-6">
              <MicPanel />
              <TurnStatePanel />
              <TurnLatencyPanel />
            </div>
          </div>

          <MetricsDashboard />

          {import.meta.env.DEV && <DevControls />}
        </div>
      </main>
    </div>
  );
}

export default App;
