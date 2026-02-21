import { MessageSquare, Pencil, Plus } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { PageHeader } from "@/components/layout/PageHeader";
import { useAgents } from "@/contexts/AgentsContext";

export function Agents() {
  const navigate = useNavigate();
  const { agents, setAgentStatus } = useAgents();

  return (
    <>
      <PageHeader
        title="Agents"
        description="Manage voice AI agents for your organization"
        actions={
          <Button
            onClick={() => navigate("/app/agents/new")}
            type="button"
          >
            <Plus className="mr-2 h-4 w-4" />
            New agent
          </Button>
        }
      />
      <Card>
        <CardHeader title="All agents" description={`${agents.length} agents`} />
        <CardContent className="p-0">
          {agents.length === 0 ? (
            <div className="p-8">
              <EmptyState
                icon={<MessageSquare className="h-6 w-6" />}
                title="No agents yet"
                description="Create your first voice AI agent to handle calls and conversations."
                action={
                  <Button onClick={() => navigate("/app/agents/new")}>
                    <Plus className="mr-2 h-4 w-4" />
                    New agent
                  </Button>
                }
              />
            </div>
          ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-border text-left text-sm text-muted-foreground">
                <th className="px-6 py-3 font-medium">Name</th>
                <th className="px-6 py-3 font-medium">Description</th>
                <th className="px-6 py-3 font-medium">Status</th>
                <th className="px-6 py-3 font-medium">Conversations</th>
                <th className="px-6 py-3 font-medium">Created</th>
                <th className="px-6 py-3 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {agents.map((a) => (
                <tr
                  key={a.id}
                  className="border-b border-border/50 transition-colors hover:bg-hover/50"
                >
                  <td className="px-6 py-4 font-medium text-white">
                    <button
                      type="button"
                      onClick={() => navigate(`/app/agents/${a.id}`)}
                      className="text-left hover:underline focus:outline-none focus:ring-2 focus:ring-primary rounded"
                    >
                      {a.name}
                    </button>
                  </td>
                  <td className="px-6 py-4 text-sm text-muted-foreground">
                    {a.description}
                  </td>
                  <td className="px-6 py-4">
                    <button
                      type="button"
                      onClick={() =>
                        setAgentStatus(
                          a.id,
                          a.status === "active" ? "draft" : "active"
                        )
                      }
                      className="focus:outline-none focus:ring-2 focus:ring-primary rounded"
                      title={a.status === "active" ? "Disable agent" : "Enable agent"}
                    >
                      <Badge
                        variant={
                          a.status === "active"
                            ? "success"
                            : a.status === "paused"
                            ? "warning"
                            : "default"
                        }
                      >
                        {a.status}
                      </Badge>
                    </button>
                  </td>
                  <td className="px-6 py-4 text-sm text-muted-foreground">
                    {a.conversationCount?.toLocaleString() ?? "—"}
                  </td>
                  <td className="px-6 py-4 text-sm text-muted-foreground">
                    {a.createdAt}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => navigate(`/app/agents/${a.id}`)}
                      aria-label={`Edit ${a.name}`}
                    >
                      <Pencil className="h-4 w-4" />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          )}
        </CardContent>
      </Card>
    </>
  );
}
