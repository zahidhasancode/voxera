import { Copy, MessageSquare, Pencil, Plus } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Switch } from "@/components/ui/Switch";
import { PageHeader } from "@/components/layout/PageHeader";
import { useToast } from "@/components/ui/Toast";
import { useAgents } from "@/contexts/AgentsContext";

export function Agents() {
  const navigate = useNavigate();
  const { agents, setAgentStatus } = useAgents();
  const { success } = useToast();

  return (
    <>
      <PageHeader
        title="AI agents"
        description="Monitor, configure, and manage voice AI agents"
        actions={
          <Button onClick={() => navigate("/app/agents/new")} type="button">
            <Plus className="h-4 w-4" />
            Create agent
          </Button>
        }
      />

      {agents.length === 0 ? (
        <Card>
          <CardContent className="p-8">
            <EmptyState
              icon={<MessageSquare className="h-6 w-6" />}
              title="No agents yet"
              description="Create your first voice AI agent to handle calls and conversations."
              action={
                <Button onClick={() => navigate("/app/agents/new")}>
                  <Plus className="h-4 w-4" />
                  New agent
                </Button>
              }
            />
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
          {agents.map((agent) => {
            const config = agent.config;
            return (
              <Card key={agent.id} className="flex flex-col">
                <CardHeader
                  title={agent.name}
                  description={agent.description}
                  actions={
                    <Badge
                      variant={
                        agent.status === "active" ? "success" : agent.status === "paused" ? "warning" : "default"
                      }
                    >
                      {agent.status}
                    </Badge>
                  }
                />
                <CardContent className="flex flex-1 flex-col gap-4">
                  <dl className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <dt className="text-2xs text-muted-foreground">Language</dt>
                      <dd className="font-medium text-foreground">{config?.language ?? "en-US"}</dd>
                    </div>
                    <div>
                      <dt className="text-2xs text-muted-foreground">Voice</dt>
                      <dd className="font-medium text-foreground">{config?.voiceId ?? "default"}</dd>
                    </div>
                    <div>
                      <dt className="text-2xs text-muted-foreground">Resolution</dt>
                      <dd className="font-medium text-foreground">—</dd>
                    </div>
                    <div>
                      <dt className="text-2xs text-muted-foreground">Avg latency</dt>
                      <dd className="font-medium text-foreground">—</dd>
                    </div>
                    <div>
                      <dt className="text-2xs text-muted-foreground">Knowledge</dt>
                      <dd className="font-medium text-foreground">{config?.knowledgeBaseIds?.length ?? 0} sources</dd>
                    </div>
                    <div>
                      <dt className="text-2xs text-muted-foreground">Monthly usage</dt>
                      <dd className="font-medium text-foreground">{agent.conversationCount?.toLocaleString() ?? 0} calls</dd>
                    </div>
                  </dl>

                  <div className="mt-auto flex flex-wrap items-center gap-2 border-t border-border pt-4">
                    <Switch
                      checked={agent.status === "active"}
                      onChange={(on) => {
                        setAgentStatus(agent.id, on ? "active" : "draft");
                        success(on ? `${agent.name} enabled` : `${agent.name} disabled`);
                      }}
                      label="Active"
                    />
                    <div className="ml-auto flex gap-1">
                      <Button variant="ghost" size="sm" onClick={() => navigate(`/app/agents/${agent.id}`)}>
                        <Pencil className="h-4 w-4" />
                        Edit
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => success("Agent cloned")}>
                        <Copy className="h-4 w-4" />
                        Clone
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </>
  );
}
