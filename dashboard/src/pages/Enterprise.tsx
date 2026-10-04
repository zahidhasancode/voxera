import { Github } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { PageHeader } from "@/components/layout/PageHeader";
import { REPO_URL } from "@/projectLinks";

export function Enterprise() {
  return (
    <>
      <PageHeader title="Enterprise" description="Not a commercial product" />

      <Card>
        <CardHeader
          title="Not a commercial product"
          description="VOXERA is a personal project by MD Zahid Hasan"
        />
        <CardContent className="space-y-4">
          <p className="max-w-2xl text-sm text-muted-foreground">
            There is no company, no paid plan, no service agreement, no compliance certification, and no support team
            behind this project, so there is nothing to configure on this page. The source code and the setup
            instructions are on GitHub.
          </p>
          <a href={REPO_URL} target="_blank" rel="noopener noreferrer" className="inline-block">
            <Button variant="secondary" size="sm" className="gap-2">
              <Github className="h-4 w-4" />
              View on GitHub
            </Button>
          </a>
        </CardContent>
      </Card>
    </>
  );
}
