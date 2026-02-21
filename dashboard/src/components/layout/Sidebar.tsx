import {
  BarChart3,
  BookOpen,
  Building2,
  CreditCard,
  ClipboardList,
  Key,
  LayoutDashboard,
  MessageSquare,
  Settings,
  Shield,
  TrendingUp,
  Users,
} from "lucide-react";
import { Link, NavLink, useLocation } from "react-router-dom";

const nav = [
  { to: "/app", label: "Overview", icon: LayoutDashboard },
  { to: "/app/agents", label: "Agents", icon: MessageSquare },
  { to: "/app/knowledge", label: "Knowledge base", icon: BookOpen },
  { to: "/app/developer", label: "Developer", icon: Key },
  { to: "/app/usage", label: "Usage", icon: TrendingUp },
  { to: "/app/analytics", label: "Analytics", icon: BarChart3 },
  { to: "/app/enterprise", label: "Enterprise", icon: Building2 },
  { to: "/app/billing", label: "Billing", icon: CreditCard },
  { to: "/app/organization", label: "Organization", icon: Users },
  { to: "/app/audit-log", label: "Audit log", icon: ClipboardList },
  { to: "/app/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const location = useLocation();
  return (
    <aside className="fixed left-0 top-0 z-40 flex h-screen w-52 flex-col border-r border-border bg-card shadow-soft">
      <Link to="/app" className="flex h-14 items-center gap-3 border-b border-border px-4">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-primary shadow-soft">
          <Shield className="h-4 w-4 text-primary-foreground" />
        </div>
        <span className="font-semibold tracking-tight text-card-foreground">VOXERA</span>
      </Link>
      <nav className="flex-1 space-y-1 overflow-y-auto p-3">
        {nav.map(({ to, label, icon: Icon }) => {
          const activeByPath = to === "/app/developer" && location.pathname === "/app/api-keys";
          return (
          <NavLink
            key={to}
            to={to}
            end={to === "/app"}
            className={({ isActive }) => {
              const active = isActive || activeByPath;
              return `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors duration-200 ${
                active
                  ? "bg-muted text-foreground"
                  : "text-muted-foreground hover:bg-hover hover:text-foreground"
              }`;
            }}
          >
            <Icon className="h-4 w-4 shrink-0 opacity-80" />
            {label}
          </NavLink>
          );
        })}
      </nav>
    </aside>
  );
}
