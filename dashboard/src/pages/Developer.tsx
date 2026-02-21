import {
  Check,
  Copy,
  Key,
  Plus,
  RefreshCw,
  Trash2,
  Webhook,
} from "lucide-react";
import { useCallback, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Input } from "@/components/ui/Input";
import { PageHeader } from "@/components/layout/PageHeader";
import { useDeveloper } from "@/contexts/DeveloperContext";
import type { ApiKey } from "@/types";

function CodeBlock({
  code,
  language,
  onCopy,
}: {
  code: string;
  language: string;
  onCopy?: () => void;
}) {
  const [copied, setCopied] = useState(false);
  const copy = useCallback(() => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    onCopy?.();
    setTimeout(() => setCopied(false), 2000);
  }, [code, onCopy]);

  return (
    <div className="relative">
      <div className="flex items-center justify-between border-b border-border bg-hover px-4 py-2">
        <span className="text-2xs font-medium uppercase text-muted-foreground">
          {language}
        </span>
        <button
          type="button"
          onClick={copy}
          className="flex items-center gap-1.5 rounded px-2 py-1 text-2xs text-muted-foreground hover:bg-muted/30 hover:text-foreground"
        >
          {copied ? (
            <>
              <Check className="h-3.5 w-3.5" />
              Copied
            </>
          ) : (
            <>
              <Copy className="h-3.5 w-3.5" />
              Copy
            </>
          )}
        </button>
      </div>
      <pre className="overflow-x-auto border border-t-0 border-border bg-background p-4 text-sm text-muted-foreground">
        <code>{code}</code>
      </pre>
    </div>
  );
}

function CopyableSecret({
  value,
  label,
}: {
  value: string;
  label: string;
}) {
  const [copied, setCopied] = useState(false);
  const copy = useCallback(() => {
    navigator.clipboard.writeText(value);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [value]);

  return (
    <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 p-4">
      <p className="mb-2 text-2xs font-medium text-amber-200/90">{label}</p>
      <div className="flex items-center gap-2 font-mono text-sm text-foreground">
        <span className="break-all">{value}</span>
        <Button variant="secondary" size="sm" onClick={copy}>
          {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
        </Button>
      </div>
    </div>
  );
}

const CODE_EXAMPLES = {
  curl: `curl https://api.voxera.io/v1/conversations \\
  -H "Authorization: Bearer vox_live_YOUR_SECRET_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"agent_id": "agt_xxx", "user_message": "Hello"}'`,
  node: `const res = await fetch('https://api.voxera.io/v1/conversations', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ' + process.env.VOXERA_API_KEY,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    agent_id: 'agt_xxx',
    user_message: 'Hello',
  }),
});`,
  python: `import os
import requests

response = requests.post(
    "https://api.voxera.io/v1/conversations",
    headers={
        "Authorization": f"Bearer {os.environ['VOXERA_API_KEY']}",
        "Content-Type": "application/json",
    },
    json={"agent_id": "agt_xxx", "user_message": "Hello"},
)`,
};

const WEBHOOK_EVENTS = [
  "conversation.started",
  "conversation.completed",
  "agent.error",
  "agent.limit_reached",
];

export function Developer() {
  const {
    apiKeys,
    webhooks,
    usageLogs,
    rateLimits,
    createKey,
    regenerateKey,
    revokeKey,
    dismissKeySecret,
    addWebhook,
    deleteWebhook,
    toggleWebhook,
  } = useDeveloper();

  const [createModal, setCreateModal] = useState(false);
  const [newKeyName, setNewKeyName] = useState("");
  const [newKeyLive, setNewKeyLive] = useState(false);
  const [createdKey, setCreatedKey] = useState<ApiKey | null>(null);
  const [regeneratingId, setRegeneratingId] = useState<string | null>(null);
  const [regeneratedKey, setRegeneratedKey] = useState<ApiKey | null>(null);
  const [codeTab, setCodeTab] = useState<"curl" | "node" | "python">("curl");

  const [webhookModal, setWebhookModal] = useState(false);
  const [webhookUrl, setWebhookUrl] = useState("");
  const [webhookDesc, setWebhookDesc] = useState("");
  const [webhookEvents, setWebhookEvents] = useState<string[]>([]);

  const handleCreateKey = useCallback(() => {
    if (!newKeyName.trim()) return;
    const key = createKey(newKeyName.trim(), newKeyLive);
    setCreatedKey(key);
    setNewKeyName("");
    setNewKeyLive(false);
    setCreateModal(false);
  }, [newKeyName, newKeyLive, createKey]);

  const handleRegenerate = useCallback(
    (id: string) => {
      setRegeneratingId(id);
      const key = regenerateKey(id);
      setRegeneratedKey(key ?? null);
      setRegeneratingId(null);
    },
    [regenerateKey]
  );

  const handleAddWebhook = useCallback(() => {
    if (!webhookUrl.trim()) return;
    addWebhook({
      url: webhookUrl.trim(),
      description: webhookDesc.trim() || undefined,
      events: webhookEvents.length ? webhookEvents : ["conversation.completed"],
      enabled: true,
    });
    setWebhookUrl("");
    setWebhookDesc("");
    setWebhookEvents([]);
    setWebhookModal(false);
  }, [webhookUrl, webhookDesc, webhookEvents, addWebhook]);

  const toggleWebhookEvent = (event: string) => {
    setWebhookEvents((prev) =>
      prev.includes(event) ? prev.filter((e) => e !== event) : [...prev, event]
    );
  };

  return (
    <>
      <PageHeader
        title="Developer"
        description="API keys, webhooks, rate limits, and usage"
      />

      <div className="space-y-8">
        {/* API Keys */}
        <Card>
          <CardHeader
            title="API keys"
            description="Create and manage keys for API and WebSocket access. Keep keys secret and rotate if compromised."
            actions={
              <Button onClick={() => setCreateModal(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Create key
              </Button>
            }
          />
          <CardContent className="p-0">
            {apiKeys.length === 0 ? (
              <div className="p-8">
                <EmptyState
                  icon={<Key className="h-6 w-6" />}
                  title="No API keys yet"
                  description="Create a key to authenticate API and WebSocket requests."
                  action={
                    <Button onClick={() => setCreateModal(true)}>
                      <Plus className="mr-2 h-4 w-4" />
                      Create key
                    </Button>
                  }
                />
              </div>
            ) : (
            <table className="w-full">
              <thead>
                <tr className="border-b border-border text-left text-sm text-muted-foreground">
                  <th className="px-6 py-3 font-medium">Name</th>
                  <th className="px-6 py-3 font-medium">Key</th>
                  <th className="px-6 py-3 font-medium">Last used</th>
                  <th className="px-6 py-3 font-medium">Created</th>
                  <th className="px-6 py-3 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {apiKeys.map((k) => (
                  <tr
                    key={k.id}
                    className="border-b border-border/50 transition-colors hover:bg-hover/50"
                  >
                    <td className="px-6 py-4 font-medium text-foreground">{k.name}</td>
                    <td className="px-6 py-4 font-mono text-sm text-muted-foreground">
                      {k.secret ? (
                        <span className="text-amber-200/90">{k.secret}</span>
                      ) : (
                        k.prefix
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm text-muted-foreground">
                      {k.lastUsedAt
                        ? new Date(k.lastUsedAt).toLocaleString()
                        : "Never"}
                    </td>
                    <td className="px-6 py-4 text-sm text-muted-foreground">
                      {k.createdAt}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-1">
                        {k.secret ? (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => dismissKeySecret(k.id)}
                          >
                            I've saved the key
                          </Button>
                        ) : (
                          <>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleRegenerate(k.id)}
                              disabled={regeneratingId === k.id}
                              title="Regenerate key"
                            >
                              <RefreshCw
                                className={`h-4 w-4 ${regeneratingId === k.id ? "animate-spin" : ""}`}
                              />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => revokeKey(k.id)}
                              className="text-red-400 hover:text-red-300"
                              title="Revoke"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            )}
          </CardContent>
        </Card>

        {/* Show secret after create */}
        {createdKey?.secret && (
          <Card className="border-amber-500/30">
            <CardHeader
              title="Key created — copy it now"
              description="This is the only time you'll see this secret."
            />
            <CardContent>
              <CopyableSecret
                value={createdKey.secret}
                label="Secret key"
              />
              <Button
                variant="secondary"
                className="mt-4"
                onClick={() => {
                  dismissKeySecret(createdKey.id);
                  setCreatedKey(null);
                }}
              >
                I've saved the key
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Show secret after regenerate */}
        {regeneratedKey?.secret && (
          <Card className="border-amber-500/30">
            <CardHeader
              title="Key regenerated — copy the new secret"
              description="The previous key is no longer valid."
            />
            <CardContent>
              <CopyableSecret
                value={regeneratedKey.secret}
                label="New secret key"
              />
              <Button
                variant="secondary"
                className="mt-4"
                onClick={() => {
                  dismissKeySecret(regeneratedKey.id);
                  setRegeneratedKey(null);
                }}
              >
                I've saved the key
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Rate limits */}
        <Card>
          <CardHeader
            title="Rate limits"
            description="Current usage and reset windows"
          />
          <CardContent>
            <div className="grid gap-4 sm:grid-cols-2">
              {rateLimits.map((r, i) => (
                <div
                  key={i}
                  className="rounded-lg border border-border bg-background p-4"
                >
                  <p className="text-sm font-medium text-foreground">
                    {r.window}
                  </p>
                  <p className="mt-1 text-2xs text-muted-foreground">
                    {r.remaining} / {r.limit} remaining
                  </p>
                  <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-muted">
                    <div
                      className="h-full rounded-full bg-primary"
                      style={{
                        width: `${(r.remaining / r.limit) * 100}%`,
                      }}
                    />
                  </div>
                  <p className="mt-2 text-2xs text-muted-foreground">
                    Resets {new Date(r.resetsAt).toLocaleString()}
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Webhooks */}
        <Card>
          <CardHeader
            title="Webhooks"
            description="Receive events at your endpoint"
            actions={
              <Button variant="secondary" onClick={() => setWebhookModal(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Add endpoint
              </Button>
            }
          />
          <CardContent className="p-0">
            {webhooks.length === 0 ? (
              <div className="p-8">
                <EmptyState
                  icon={<Webhook className="h-6 w-6" />}
                  title="No webhook endpoints"
                  description="Add an endpoint to receive conversation and agent events in real time."
                  action={
                    <Button variant="secondary" onClick={() => setWebhookModal(true)}>
                      <Plus className="mr-2 h-4 w-4" />
                      Add endpoint
                    </Button>
                  }
                />
              </div>
            ) : (
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border text-left text-sm text-muted-foreground">
                    <th className="px-6 py-3 font-medium">URL</th>
                    <th className="px-6 py-3 font-medium">Events</th>
                    <th className="px-6 py-3 font-medium">Status</th>
                    <th className="px-6 py-3 font-medium text-right" />
                  </tr>
                </thead>
                <tbody>
                  {webhooks.map((w) => (
                    <tr
                      key={w.id}
                      className="border-b border-border/50 hover:bg-hover/50"
                    >
                      <td className="px-6 py-4">
                        <div>
                          <p className="font-mono text-sm text-foreground">{w.url}</p>
                          {w.description && (
                            <p className="text-2xs text-muted-foreground">
                              {w.description}
                            </p>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-muted-foreground">
                        {w.events.slice(0, 2).join(", ")}
                        {w.events.length > 2 && ` +${w.events.length - 2}`}
                      </td>
                      <td className="px-6 py-4">
                        <button
                          type="button"
                          onClick={() => toggleWebhook(w.id, !w.enabled)}
                          className={`rounded px-2 py-0.5 text-2xs font-medium ${
                            w.enabled
                              ? "bg-emerald-500/15 text-emerald-400"
                              : "bg-muted text-muted-foreground"
                          }`}
                        >
                          {w.enabled ? "Enabled" : "Disabled"}
                        </button>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => deleteWebhook(w.id)}
                          className="text-red-400 hover:text-red-300"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </CardContent>
        </Card>

        {/* API usage logs */}
        <Card>
          <CardHeader
            title="API usage logs"
            description="Recent API requests"
          />
          <CardContent className="p-0">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border text-left text-sm text-muted-foreground">
                  <th className="px-6 py-3 font-medium">Time</th>
                  <th className="px-6 py-3 font-medium">Method</th>
                  <th className="px-6 py-3 font-medium">Path</th>
                  <th className="px-6 py-3 font-medium">Status</th>
                  <th className="px-6 py-3 font-medium">Key</th>
                  <th className="px-6 py-3 font-medium">Duration</th>
                </tr>
              </thead>
              <tbody>
                {usageLogs.map((log) => (
                  <tr
                    key={log.id}
                    className="border-b border-border/50 hover:bg-hover/50"
                  >
                    <td className="px-6 py-3 text-sm text-muted-foreground">
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td className="px-6 py-3 font-mono text-sm text-foreground">
                      {log.method}
                    </td>
                    <td className="px-6 py-3 font-mono text-2xs text-muted-foreground">
                      {log.path}
                    </td>
                    <td className="px-6 py-3">
                      <span
                        className={
                          log.status >= 200 && log.status < 300
                            ? "text-emerald-400"
                            : log.status === 429
                              ? "text-amber-400"
                              : "text-red-400"
                        }
                      >
                        {log.status}
                      </span>
                    </td>
                    <td className="px-6 py-3 text-sm text-muted-foreground">
                      {log.keyName}
                    </td>
                    <td className="px-6 py-3 text-sm text-muted-foreground">
                      {log.durationMs != null ? `${log.durationMs} ms` : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>

        {/* Code examples */}
        <Card>
          <CardHeader
            title="Code examples"
            description="Quick start with your API key"
          />
          <CardContent className="space-y-4">
            <div className="flex gap-1 border-b border-border">
              {(["curl", "node", "python"] as const).map((tab) => (
                <button
                  key={tab}
                  type="button"
                  onClick={() => setCodeTab(tab)}
                  className={`border-b-2 px-4 py-2 text-sm font-medium transition-colors ${
                    codeTab === tab
                      ? "border-primary text-foreground"
                      : "border-transparent text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {tab === "curl" ? "cURL" : tab === "node" ? "Node.js" : "Python"}
                </button>
              ))}
            </div>
            <CodeBlock
              code={CODE_EXAMPLES[codeTab]}
              language={codeTab}
            />
          </CardContent>
        </Card>
      </div>

      {/* Create key modal */}
      {createModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
          onClick={() => setCreateModal(false)}
          role="dialog"
          aria-modal="true"
        >
          <div
            className="w-full max-w-md rounded-xl border border-border bg-background-elevated p-6 shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="font-semibold text-foreground">Create API key</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              Give the key a name and choose live or test mode.
            </p>
            <div className="mt-4 space-y-4">
              <Input
                label="Name"
                placeholder="e.g. Production"
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
              />
              <div>
                <label className="mb-1.5 block text-sm font-medium text-muted-foreground">
                  Mode
                </label>
                <div className="flex gap-4">
                  <label className="flex cursor-pointer items-center gap-2">
                    <input
                      type="radio"
                      name="mode"
                      checked={!newKeyLive}
                      onChange={() => setNewKeyLive(false)}
                      className="text-primary"
                    />
                    <span className="text-sm text-foreground">Test</span>
                  </label>
                  <label className="flex cursor-pointer items-center gap-2">
                    <input
                      type="radio"
                      name="mode"
                      checked={newKeyLive}
                      onChange={() => setNewKeyLive(true)}
                      className="text-primary"
                    />
                    <span className="text-sm text-foreground">Live</span>
                  </label>
                </div>
              </div>
            </div>
            <div className="mt-6 flex justify-end gap-2">
              <Button variant="secondary" onClick={() => setCreateModal(false)}>
                Cancel
              </Button>
              <Button onClick={handleCreateKey} disabled={!newKeyName.trim()}>
                Create key
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Add webhook modal */}
      {webhookModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
          onClick={() => setWebhookModal(false)}
          role="dialog"
          aria-modal="true"
        >
          <div
            className="w-full max-w-lg rounded-xl border border-border bg-background-elevated p-6 shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="font-semibold text-foreground">Add webhook endpoint</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              We'll send POST requests to your URL for selected events.
            </p>
            <div className="mt-4 space-y-4">
              <Input
                label="Endpoint URL"
                placeholder="https://api.example.com/webhooks/voxera"
                value={webhookUrl}
                onChange={(e) => setWebhookUrl(e.target.value)}
              />
              <Input
                label="Description (optional)"
                placeholder="e.g. Production events"
                value={webhookDesc}
                onChange={(e) => setWebhookDesc(e.target.value)}
              />
              <div>
                <label className="mb-2 block text-sm font-medium text-muted-foreground">
                  Events
                </label>
                <div className="flex flex-wrap gap-2">
                  {WEBHOOK_EVENTS.map((ev) => (
                    <label
                      key={ev}
                      className="flex cursor-pointer items-center gap-2 rounded border border-border bg-background px-3 py-2 text-sm"
                    >
                      <input
                        type="checkbox"
                        checked={webhookEvents.includes(ev)}
                        onChange={() => toggleWebhookEvent(ev)}
                        className="rounded text-primary"
                      />
                      <span className="text-foreground">{ev}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>
            <div className="mt-6 flex justify-end gap-2">
              <Button variant="secondary" onClick={() => setWebhookModal(false)}>
                Cancel
              </Button>
              <Button onClick={handleAddWebhook} disabled={!webhookUrl.trim()}>
                Add endpoint
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
