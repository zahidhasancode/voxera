import { useEffect } from "react";
import {
  Header,
  ConversationPanel,
  AudioPanel,
  TurnStatePanel,
  MetricsDashboard,
  DevControls,
} from "./components";
import { useVoxera } from "./store/VoxeraContext";

function App() {
  const { connect } = useVoxera();

  useEffect(() => {
    // Auto-connect in dev for quicker demos; user can disconnect/reconnect
    connect();
  }, [connect]);

  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1 p-6 overflow-auto">
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Top: Conversation + Audio + Turn State */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 min-h-[360px]">
              <ConversationPanel />
            </div>
            <div className="space-y-6">
              <AudioPanel />
              <TurnStatePanel />
            </div>
          </div>

          {/* Metrics */}
          <MetricsDashboard />

          {/* Dev controls */}
          <DevControls />
        </div>
      </main>
    </div>
  );
}

export default App;
