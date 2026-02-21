import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { PageHeader } from "@/components/layout/PageHeader";
import { useAuth } from "@/contexts/AuthContext";

export function Settings() {
  const { user } = useAuth();

  return (
    <>
      <PageHeader
        title="Settings"
        description="Your account and preferences"
      />
      <Card>
        <CardHeader
          title="Profile"
          description="Update your name and email"
        />
        <CardContent className="space-y-4">
          <Input label="Name" defaultValue={user?.name} />
          <Input label="Email" type="email" defaultValue={user?.email} />
          <Button>Save</Button>
        </CardContent>
      </Card>
      <Card className="mt-6">
        <CardHeader
          title="Security"
          description="Password and sessions"
        />
        <CardContent className="space-y-4">
          <Button variant="secondary">Change password</Button>
          <p className="text-sm text-muted-foreground">
            Active sessions and 2FA can be added when auth is wired to your backend.
          </p>
        </CardContent>
      </Card>
    </>
  );
}
