import { useState } from "react";
import { useVoxera } from "@/store/VoxeraContext";

const DEFAULT_TRANSCRIPT = "What can you help me with?";

export function DevControls() {
  const { sendDevTestTranscript, sendDevTestTts, clearConversation, connectionStatus } = useVoxera();
  const [transcript, setTranscript] = useState(DEFAULT_TRANSCRIPT);
  const [ttsText, setTtsText] = useState("This is a TTS test.");

  const connected = connectionStatus === "connected";

  return (
    <section className="rounded-xl border border-amber-700/50 bg-amber-950/20 overflow-hidden">
      <div className="px-4 py-3 border-b border-amber-700/30 bg-amber-900/20">
        <h2 className="text-sm font-semibold text-amber-200">Developer Controls</h2>
      </div>
      <div className="p-4 space-y-4">
        <div>
          <label className="block text-xs text-amber-300/90 mb-1">Test transcript (→ LLM → TTS)</label>
          <div className="flex gap-2">
            <input
              type="text"
              value={transcript}
              onChange={(e) => setTranscript(e.target.value)}
              placeholder='e.g. "Hello, what can you do?"'
              className="flex-1 rounded-lg border border-amber-700/50 bg-slate-900/80 px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
              disabled={!connected}
            />
            <button
              onClick={() => sendDevTestTranscript(transcript)}
              disabled={!connected}
              className="px-4 py-2 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Send
            </button>
          </div>
        </div>
        <div>
          <label className="block text-xs text-amber-300/90 mb-1">Test TTS only</label>
          <div className="flex gap-2">
            <input
              type="text"
              value={ttsText}
              onChange={(e) => setTtsText(e.target.value)}
              placeholder="Text to speak"
              className="flex-1 rounded-lg border border-amber-700/50 bg-slate-900/80 px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
              disabled={!connected}
            />
            <button
              onClick={() => sendDevTestTts(ttsText)}
              disabled={!connected}
              className="px-4 py-2 rounded-lg bg-amber-600/80 hover:bg-amber-500/80 text-white text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              TTS
            </button>
          </div>
        </div>
        <button
          onClick={clearConversation}
          className="w-full py-2 rounded-lg border border-slate-600 text-slate-400 hover:border-slate-500 hover:text-slate-300 text-sm transition-colors"
        >
          Clear conversation
        </button>
      </div>
    </section>
  );
}
