import {
  BarChart3,
  BookOpen,
  Building2,
  ClipboardList,
  CreditCard,
  GitBranch,
  Key,
  LayoutDashboard,
  MessageSquare,
  Phone,
  Plug,
  Settings,
  Shield,
  Users,
  Wrench,
  X,
  type LucideIcon,
} from "lucide-react";
import { Link, NavLink, useLocation } from "react-router-dom";
import { useLiveCallsStore } from "@/stores/liveCallsStore";

interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
  badge?: number;
}

interface NavGroup {
  label: string;
  items: NavItem[];
}

function useNavGroups(): NavGroup[] {
  const activeCalls = useLiveCallsStore((s) => s.calls.filter((c) => c.status !== "ended").length);

  return [
    {
      label: "Operations",
      items: [
        { to: "/app", label: "Dashboard", icon: LayoutDashboard },
        { to: "/app/live-calls", label: "Live calls", icon: Phone, badge: activeCalls || undefined },
        { to: "/app/agents", label: "AI agents", icon: MessageSquare },
        { to: "/app/knowledge", label: "Knowledge base", icon: BookOpen },
        { to: "/app/workflows", label: "Workflows", icon: GitBranch },
        { to: "/app/tools", label: "Tool registry", icon: Wrench },
        { to: "/app/integrations", label: "Integrations", icon: Plug },
      ],
    },
    {
      label: "Platform",
      items: [
        { to: "/app/analytics", label: "Analytics", icon: BarChart3 },
        { to: "/app/tenants", label: "Tenants", icon: Building2 },
        { to: "/app/users", label: "Users", icon: Users },
        { to: "/app/billing", label: "Billing", icon: CreditCard },
        { to: "/app/audit-log", label: "Audit logs", icon: ClipboardList },
        { to: "/app/developer", label: "Developer", icon: Key },
      ],
    },
    {
      label: "Account",
      items: [{ to: "/app/settings", label: "Settings", icon: Settings }],
    },
  ];
}

interface SidebarProps {
  mobileOpen?: boolean;
  onMobileClose?: () => void;
}

function NavContent({ onNavigate }: { onNavigate?: () => void }) {
  const location = useLocation();
  const navGroups = useNavGroups();

  return (
    <nav className="flex-1 space-y-6 overflow-y-auto px-3 py-4" aria-label="Main">
      {navGroups.map((group) => (
        <div key={group.label}>
          <p className="mb-2 px-3 text-2xs font-medium uppercase tracking-widest text-muted-foreground">
            {group.label}
          </p>
          <div className="space-y-0.5">
            {group.items.map(({ to, label, icon: Icon, badge }) => {
              const activeByPath =
                to === "/app/developer" && location.pathname === "/app/api-keys";
              return (
                <NavLink
                  key={to}
                  to={to}
                  end={to === "/app"}
                  onClick={onNavigate}
                  className={({ isActive }) => {
                    const active = isActive || activeByPath;
                    return `flex items-center gap-3 rounded-lg border-l-2 px-3 py-2.5 text-sm font-medium transition-colors duration-150 ${
                      active
                        ? "border-primary bg-primary-muted/40 text-foreground"
                        : "border-transparent text-muted-foreground hover:bg-hover hover:text-foreground"
                    }`;
                  }}
                >
                  <Icon className="h-4 w-4 shrink-0 opacity-90" />
                  <span className="flex-1">{label}</span>
                  {badge !== undefined && badge > 0 && (
                    <span className="rounded-full bg-primary px-1.5 py-0.5 text-2xs font-semibold text-primary-foreground">
                      {badge}
                    </span>
                  )}
                </NavLink>
              );
            })}
          </div>
        </div>
      ))}
    </nav>
  );
}

export function Sidebar({ mobileOpen = false, onMobileClose }: SidebarProps) {
  return (
    <>
      <aside className="fixed left-0 top-0 z-40 hidden h-screen w-56 flex-col border-r border-border bg-card lg:flex">
        <Link to="/app" className="flex h-16 items-center gap-3 border-b border-border px-5">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-primary">
            <Shield className="h-5 w-5 text-primary-foreground" />
          </div>
          <span className="text-lg font-semibold tracking-tight text-card-foreground">VOXERA</span>
        </Link>
        <NavContent />
      </aside>

      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-background/80 backdrop-blur-sm lg:hidden"
          aria-hidden
          onClick={onMobileClose}
        />
      )}

      <aside
        className={`fixed left-0 top-0 z-50 flex h-screen w-72 flex-col border-r border-border bg-card transition-transform duration-200 lg:hidden ${
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        }`}
        aria-hidden={!mobileOpen}
      >
        <div className="flex h-16 items-center justify-between border-b border-border px-5">
          <Link to="/app" className="flex items-center gap-3" onClick={onMobileClose}>
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary">
              <Shield className="h-5 w-5 text-primary-foreground" />
            </div>
            <span className="text-lg font-semibold tracking-tight">VOXERA</span>
          </Link>
          <button
            type="button"
            onClick={onMobileClose}
            className="rounded-lg p-2 text-muted-foreground hover:bg-hover"
            aria-label="Close menu"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        <NavContent onNavigate={onMobileClose} />
      </aside>
    </>
  );
}
