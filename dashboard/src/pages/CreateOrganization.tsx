import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { PageHeader } from "@/components/layout/PageHeader";
import { useOrg } from "@/contexts/OrgContext";

export function CreateOrganization() {
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { createOrganization } = useOrg();
  const navigate = useNavigate();

  function deriveSlug(value: string) {
    return value
      .toLowerCase()
      .replace(/\s+/g, "-")
      .replace(/[^a-z0-9-]/g, "");
  }

  function handleNameChange(e: React.ChangeEvent<HTMLInputElement>) {
    const v = e.target.value;
    setName(v);
    if (!slug || slug === deriveSlug(name)) setSlug(deriveSlug(v));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setIsSubmitting(true);
    try {
      await createOrganization(name.trim(), slug.trim() || deriveSlug(name));
      navigate("/app/organization", { replace: true });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <>
      <PageHeader
        title="Create organization"
        description="Add a new organization to your account"
      />
      <Card className="max-w-lg">
        <CardHeader
          title="Organization details"
          description="Name and URL slug. The slug is used in API and billing."
        />
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Organization name"
              placeholder="Acme Corp"
              value={name}
              onChange={handleNameChange}
              required
            />
            <Input
              label="Slug"
              placeholder="acme-corp"
              value={slug}
              onChange={(e) => setSlug(deriveSlug(e.target.value))}
            />
            <div className="flex gap-2 pt-2">
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Creating…" : "Create organization"}
              </Button>
              <Button
                type="button"
                variant="ghost"
                onClick={() => navigate("/app/organization")}
              >
                Cancel
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </>
  );
}
