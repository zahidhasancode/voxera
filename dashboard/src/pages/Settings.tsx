import { useState } from "react";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { PageHeader } from "@/components/layout/PageHeader";
import { useToast } from "@/components/ui/Toast";
import { useAuth } from "@/contexts/AuthContext";

export function Settings() {
  const { user } = useAuth();
  const { success } = useToast();
  const [name, setName] = useState(user?.name ?? "");
  const [email, setEmail] = useState(user?.email ?? "");
  const [saving, setSaving] = useState(false);

  async function handleSave() {
    setSaving(true);
    await new Promise((r) => setTimeout(r, 600));
    setSaving(false);
    success("Profile updated");
  }

  return (
    <>
      <PageHeader title="Settings" description="Your account and preferences" />
      <Card>
        <CardHeader title="Profile" description="Update your name and email" />
        <CardContent className="space-y-4">
          <Input label="Name" value={name} onChange={(e) => setName(e.target.value)} />
          <Input label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          <Button onClick={handleSave} loading={saving}>
            Save changes
          </Button>
        </CardContent>
      </Card>
      <Card className="mt-6">
        <CardHeader title="Security" description="Password and sessions" />
        <CardContent className="space-y-4">
          <Button variant="secondary">Change password</Button>
          <p className="text-sm text-muted-foreground">
            Manage active sessions from the Sessions page.
          </p>
        </CardContent>
      </Card>
    </>
  );
}
