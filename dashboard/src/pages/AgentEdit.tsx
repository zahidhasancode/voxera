import { ArrowLeft, Play, Save } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { PageHeader } from "@/components/layout/PageHeader";
import { useAgents } from "@/contexts/AgentsContext";
import type {
  AgentConfig,
  AgentToolId,
  AgentVersion,
} from "@/types";

const LANGUAGES = [
  { value: "en-US", label: "English (US)" },
  { value: "en-GB", label: "English (UK)" },
  { value: "es-ES", label: "Spanish" },
  { value: "fr-FR", label: "French" },
  { value: "de-DE", label: "German" },
  { value: "it-IT", label: "Italian" },
  { value: "pt-BR", label: "Portuguese (BR)" },
  { value: "ja-JP", label: "Japanese" },
];

const VOICES = [
  { value: "alloy", label: "Alloy" },
  { value: "echo", label: "Echo" },
  { value: "fable", label: "Fable" },
  { value: "onyx", label: "Onyx" },
  { value: "nova", label: "Nova" },
  { value: "shimmer", label: "Shimmer" },
];

const TOOL_LABELS: Record<AgentToolId, string> = {
  knowledge_base: "Knowledge base",
  web_search: "Web search",
  calculator: "Calculator",
  code_interpreter: "Code interpreter",
  function_calling: "Function calling",
};

const MOCK_KNOWLEDGE_BASES = [
  { id: "kb_1", name: "Returns policy" },
  { id: "kb_2", name: "Shipping options" },
  { id: "kb_3", name: "Enterprise SSO" },
];

function formatVersionDate(iso: string) {
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, {
    dateStyle: "short",
    timeStyle: "short",
  });
}

export function AgentEdit() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { getAgentById, createAgent, updateAgent, addVersion, defaultConfig } =
    useAgents();
  const isNew = id === "new" || !id;

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [enabled, setEnabled] = useState(true);
  const [config, setConfig] = useState<AgentConfig>(() => defaultConfig());
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);

  const agent = isNew ? null : getAgentById(id ?? "");

  useEffect(() => {
    if (agent) {
      setName(agent.name);
      setDescription(agent.description ?? "");
      setEnabled(agent.status === "active");
      setConfig(agent.config ?? defaultConfig());
    } else if (!isNew) {
      setName("");
      setDescription("");
      setEnabled(true);
      setConfig(defaultConfig());
    } else {
      setName("");
      setDescription("");
      setEnabled(false);
      setConfig(defaultConfig());
    }
  }, [agent, isNew, defaultConfig]);

  const setTool = useCallback((tool: AgentToolId, value: boolean) => {
    setConfig((c) => ({
      ...c,
      toolToggles: { ...c.toolToggles, [tool]: value },
    }));
  }, []);

  const toggleKnowledgeBase = useCallback((kbId: string) => {
    setConfig((c) => ({
      ...c,
      knowledgeBaseIds: c.knowledgeBaseIds.includes(kbId)
        ? c.knowledgeBaseIds.filter((x) => x !== kbId)
        : [...c.knowledgeBaseIds, kbId],
    }));
  }, []);

  const handleSave = useCallback(async () => {
    if (!name.trim()) return;
    setSaving(true);
    try {
      if (isNew) {
        const created = createAgent({
          name: name.trim(),
          description: description.trim(),
          status: enabled ? "active" : "draft",
          config: { ...config },
        });
        navigate(`/app/agents/${created.id}`, { replace: true });
      } else {
        updateAgent(id!, {
          name: name.trim(),
          description: description.trim(),
          status: enabled ? "active" : "draft",
          config: { ...config },
        });
        addVersion(id!, `Saved ${new Date().toLocaleString()}`);
      }
    } finally {
      setSaving(false);
    }
  }, [
    isNew,
    id,
    name,
    description,
    enabled,
    config,
    createAgent,
    updateAgent,
    addVersion,
    navigate,
  ]);

  const handleTest = useCallback(() => {
    setTesting(true);
    setTimeout(() => {
      setTesting(false);
      // Placeholder: in production would open test session or voice demo
      alert("Test agent: session would start here. Connect your voice pipeline to enable.");
    }, 400);
  }, []);

  const restoreVersion = useCallback((v: AgentVersion) => {
    setConfig({ ...v.configSnapshot });
  }, []);

  return (
    <>
      <PageHeader
        title={isNew ? "New agent" : agent?.name ?? "Edit agent"}
        description={
          isNew
            ? "Create a new voice AI agent"
            : "Update configuration and behavior"
        }
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => navigate("/app/agents")}
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={handleTest}
              disabled={testing}
            >
              <Play className="mr-2 h-4 w-4" />
              {testing ? "Starting…" : "Test agent"}
            </Button>
            <Button size="sm" onClick={handleSave} disabled={saving || !name.trim()}>
              <Save className="mr-2 h-4 w-4" />
              {saving ? "Saving…" : "Save configuration"}
            </Button>
          </div>
        }
      />

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader
              title="Identity"
              description="Name and description for this agent"
            />
            <CardContent className="space-y-4">
              <Input
                label="Agent name"
                placeholder="e.g. Support Agent"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
              <div>
                <label className="mb-1.5 block text-sm font-medium text-muted-foreground">
                  Description
                </label>
                <textarea
                  className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-white placeholder-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                  placeholder="Short description of what this agent does"
                  rows={2}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                />
              </div>
              <div className="flex items-center gap-3 pt-2">
                <span className="text-sm font-medium text-muted-foreground">
                  Agent enabled
                </span>
                <button
                  type="button"
                  role="switch"
                  aria-checked={enabled}
                  onClick={() => setEnabled((e) => !e)}
                  className={`relative inline-flex h-6 w-11 shrink-0 rounded-full border transition-colors focus:outline-none focus:ring-2 focus:ring-primary ${
                    enabled
                      ? "border-primary bg-primary"
                      : "border-border bg-background-hover"
                  }`}
                >
                  <span
                    className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow transition-transform ${
                      enabled ? "translate-x-5" : "translate-x-1"
                    }`}
                    style={{ marginTop: 2 }}
                  />
                </button>
                <span className="text-sm text-muted-foreground">
                  {enabled ? "Active" : "Disabled"}
                </span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader
              title="Voice & language"
              description="Speech and locale settings"
            />
            <CardContent className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="mb-1.5 block text-sm font-medium text-muted-foreground">
                  Language
                </label>
                <select
                  value={config.language}
                  onChange={(e) =>
                    setConfig((c) => ({ ...c, language: e.target.value }))
                  }
                  className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-white focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                >
                  {LANGUAGES.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-muted-foreground">
                  Voice
                </label>
                <select
                  value={config.voiceId}
                  onChange={(e) =>
                    setConfig((c) => ({ ...c, voiceId: e.target.value }))
                  }
                  className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-white focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                >
                  {VOICES.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="sm:col-span-2">
                <label className="mb-1.5 block text-sm font-medium text-muted-foreground">
                  Temperature: {config.temperature}
                </label>
                <input
                  type="range"
                  min={0}
                  max={2}
                  step={0.1}
                  value={config.temperature}
                  onChange={(e) =>
                    setConfig((c) => ({
                      ...c,
                      temperature: parseFloat(e.target.value),
                    }))
                  }
                  className="w-full accent-primary"
                />
                <p className="mt-1 text-xs text-muted-foreground">
                  Lower = more focused; higher = more creative
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader
              title="Tools"
              description="Capabilities this agent can use"
            />
            <CardContent>
              <div className="flex flex-wrap gap-4">
                {(Object.keys(TOOL_LABELS) as AgentToolId[]).map((tool) => (
                  <label
                    key={tool}
                    className="flex cursor-pointer items-center gap-2"
                  >
                    <input
                      type="checkbox"
                      checked={config.toolToggles[tool]}
                      onChange={(e) => setTool(tool, e.target.checked)}
                      className="h-4 w-4 rounded border-border bg-background text-primary focus:ring-primary"
                    />
                    <span className="text-sm text-white">
                      {TOOL_LABELS[tool]}
                    </span>
                  </label>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader
              title="Knowledge base"
              description="Attach knowledge bases for RAG"
            />
            <CardContent>
              <div className="flex flex-wrap gap-3">
                {MOCK_KNOWLEDGE_BASES.map((kb) => (
                  <label
                    key={kb.id}
                    className="flex cursor-pointer items-center gap-2 rounded-lg border border-border bg-background px-3 py-2 transition-colors hover:bg-border/20"
                  >
                    <input
                      type="checkbox"
                      checked={config.knowledgeBaseIds.includes(kb.id)}
                      onChange={() => toggleKnowledgeBase(kb.id)}
                      className="h-4 w-4 rounded border-border bg-background text-primary focus:ring-primary"
                    />
                    <span className="text-sm text-white">{kb.name}</span>
                  </label>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader
              title="Rate limits"
              description="Throttling and concurrency"
            />
            <CardContent className="grid gap-4 sm:grid-cols-2">
              <Input
                label="Requests per minute"
                type="number"
                min={1}
                value={config.rateLimits.requestsPerMinute}
                onChange={(e) =>
                  setConfig((c) => ({
                    ...c,
                    rateLimits: {
                      ...c.rateLimits,
                      requestsPerMinute: parseInt(e.target.value, 10) || 0,
                    },
                  }))
                }
              />
              <Input
                label="Concurrent conversations"
                type="number"
                min={1}
                value={config.rateLimits.concurrentConversations}
                onChange={(e) =>
                  setConfig((c) => ({
                    ...c,
                    rateLimits: {
                      ...c.rateLimits,
                      concurrentConversations:
                        parseInt(e.target.value, 10) || 0,
                    },
                  }))
                }
              />
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader
              title="Version history"
              description="Restore a previous configuration"
            />
            <CardContent>
              {agent?.versionHistory && agent.versionHistory.length > 0 ? (
                <ul className="space-y-2">
                  {[...agent.versionHistory]
                    .reverse()
                    .map((v) => (
                      <li
                        key={v.id}
                        className="flex items-center justify-between rounded-lg border border-border bg-background-hover px-3 py-2 text-sm"
                      >
                        <div>
                          <span className="font-medium text-white">
                            v{v.version}
                          </span>
                          <span className="ml-2 text-muted-foreground">
                            {v.label}
                          </span>
                          <span className="ml-2 text-xs text-muted-foreground">
                            {formatVersionDate(v.createdAt)}
                          </span>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => restoreVersion(v)}
                        >
                          Restore
                        </Button>
                      </li>
                    ))}
                </ul>
              ) : (
                <p className="text-sm text-muted-foreground">
                  {isNew
                    ? "Save once to start version history."
                    : "No previous versions yet."}
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </>
  );
}
