import { ChevronRight } from "lucide-react";
import { Link } from "react-router-dom";

export interface BreadcrumbItem {
  label: string;
  href?: string;
}

export function Breadcrumbs({ items }: { items: BreadcrumbItem[] }) {
  if (items.length === 0) return null;
  return (
    <nav aria-label="Breadcrumb" className="flex items-center gap-1 text-sm">
      {items.map((item, i) => (
        <span key={i} className="flex items-center gap-1">
          {i > 0 && (
            <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" aria-hidden />
          )}
          {item.href && i < items.length - 1 ? (
            <Link
              to={item.href}
              className="text-muted-foreground transition-colors hover:text-foreground"
            >
              {item.label}
            </Link>
          ) : (
            <span className={i === items.length - 1 ? "font-medium text-foreground" : "text-muted-foreground"}>
              {item.label}
            </span>
          )}
        </span>
      ))}
    </nav>
  );
}

export function useAppBreadcrumbs(pathname: string): BreadcrumbItem[] {
  const map: Record<string, BreadcrumbItem[]> = {
    "/app/agents/new": [
      { label: "Agents", href: "/app/agents" },
      { label: "New agent" },
    ],
  };
  if (map[pathname]) return map[pathname];
  const agentMatch = pathname.match(/^\/app\/agents\/([^/]+)$/);
  if (agentMatch && agentMatch[1] !== "new") {
    return [
      { label: "Agents", href: "/app/agents" },
      { label: "Edit agent" },
    ];
  }
  if (pathname === "/app/billing/invoices") {
    return [
      { label: "Billing", href: "/app/billing" },
      { label: "Invoices" },
    ];
  }
  if (pathname === "/app/organization/new") {
    return [
      { label: "Organization", href: "/app/organization" },
      { label: "Create organization" },
    ];
  }
  return [];
}
