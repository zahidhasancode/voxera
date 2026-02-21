import { Plus } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { PageHeader } from "@/components/layout/PageHeader";
import type { ApiKey } from "@/types";

const MOCK_KEYS: ApiKey[] = [
  { id: "key_1", name: "Production", prefix: "vox_live_••••••••••••", lastUsedAt: "2024-03-15T14:32:00Z", createdAt: "2024-01-10" },
  { id: "key_2", name: "Development", prefix: "vox_test_••••••••••••", lastUsedAt: null, createdAt: "2024-02-01" },
];

export function ApiKeys() {
  const [keys] = useState<ApiKey[]>(MOCK_KEYS);

  return (
    <>
      <PageHeader
        title="API keys"
        description="Manage keys for API and WebSocket access"
        actions={
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Create key
          </Button>
        }
      />
      <Card>
        <CardHeader
          title="Keys"
          description="Never share keys. Rotate if compromised."
        />
        <CardContent className="p-0">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border text-left text-sm text-muted-foreground">
                <th className="px-6 py-3 font-medium">Name</th>
                <th className="px-6 py-3 font-medium">Key</th>
                <th className="px-6 py-3 font-medium">Last used</th>
                <th className="px-6 py-3 font-medium">Created</th>
                <th className="px-6 py-3 font-medium" />
              </tr>
            </thead>
            <tbody>
              {keys.map((k) => (
                <tr
                  key={k.id}
                  className="border-b border-border/50 transition-colors hover:bg-hover/50"
                >
                  <td className="px-6 py-4 font-medium text-white">{k.name}</td>
                  <td className="px-6 py-4 font-mono text-sm text-muted-foreground">
                    {k.prefix}
                  </td>
                  <td className="px-6 py-4 text-sm text-muted-foreground">
                    {k.lastUsedAt
                      ? new Date(k.lastUsedAt).toLocaleDateString()
                      : "Never"}
                  </td>
                  <td className="px-6 py-4 text-sm text-muted-foreground">
                    {k.createdAt}
                  </td>
                  <td className="px-6 py-4">
                    <Button variant="ghost" size="sm">
                      Revoke
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </>
  );
}
