import {
  Bell,
  ChevronDown,
  LogOut,
  Monitor,
  Plus,
  User,
} from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { Link } from "react-router-dom";
import { ThemeToggle } from "@/components/ui/ThemeToggle";
import { useAuth } from "@/contexts/AuthContext";
import { useEnv } from "@/contexts/EnvContext";
import { useOrg } from "@/contexts/OrgContext";
import { useNotifications } from "@/contexts/NotificationContext";
import type { Environment, Organization } from "@/types";

function formatNotificationTime(iso: string) {
  const d = new Date(iso);
  const diff = Date.now() - d.getTime();
  if (diff < 60000) return "Just now";
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
  return d.toLocaleDateString();
}

export function Header() {
  const { user, signOut, sessions } = useAuth();
  const { environment, setEnvironment } = useEnv();
  const { currentOrg, organizations, setCurrentOrg } = useOrg();
  const { notifications, unreadCount, markAsRead, markAllRead } = useNotifications();
  const [orgOpen, setOrgOpen] = useState(false);
  const [envOpen, setEnvOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const [userOpen, setUserOpen] = useState(false);
  const orgRef = useRef<HTMLDivElement>(null);
  const envRef = useRef<HTMLDivElement>(null);
  const notifRef = useRef<HTMLDivElement>(null);
  const userRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      const target = e.target as Node;
      if (
        orgRef.current && !orgRef.current.contains(target) &&
        envRef.current && !envRef.current.contains(target) &&
        notifRef.current && !notifRef.current.contains(target) &&
        userRef.current && !userRef.current.contains(target)
      ) {
        setOrgOpen(false);
        setEnvOpen(false);
        setNotifOpen(false);
        setUserOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const envLabel = environment === "development" ? "Dev" : "Prod";

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-border bg-background px-6 shadow-soft">
      <div className="flex items-center gap-3">
        <div className="relative" ref={orgRef}>
          <button
            type="button"
            onClick={() => setOrgOpen((o) => !o)}
            className="flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium text-foreground transition-colors duration-200 hover:bg-hover"
          >
            {currentOrg?.logoUrl ? (
              <img
                src={currentOrg.logoUrl}
                alt=""
                className="h-6 w-6 rounded-lg object-cover shrink-0"
              />
            ) : null}
            <span className="max-w-[140px] truncate">
              {currentOrg?.name ?? "Select org"}
            </span>
            <ChevronDown className="h-4 w-4 shrink-0 text-muted-foreground" />
          </button>
          {orgOpen && (
            <div className="dropdown-panel absolute left-0 top-full z-50 mt-1.5 w-60 animate-fade-in">
              <div className="dropdown-section-header">Organizations</div>
              <div className="space-y-0.5">
                {organizations.map((org: Organization) => (
                  <button
                    key={org.id}
                    type="button"
                    onClick={() => {
                      setCurrentOrg(org);
                      setOrgOpen(false);
                    }}
                    className="dropdown-item"
                  >
                    {org.logoUrl ? (
                      <img
                        src={org.logoUrl}
                        alt=""
                        className="h-5 w-5 shrink-0 rounded object-cover"
                      />
                    ) : (
                      <span className="h-5 w-5 shrink-0 rounded bg-border" />
                    )}
                    <div className="min-w-0 flex-1">
                      <div className="font-medium truncate text-sm">{org.name}</div>
                      <div className="text-xs text-muted-foreground capitalize">
                        {org.role} · {org.plan}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
              <div className="my-2 border-t border-border" role="separator" />
              <Link
                to="/app/organization/new"
                onClick={() => setOrgOpen(false)}
                className="dropdown-item text-primary"
              >
                <Plus className="h-4 w-4 shrink-0" />
                <span>Create organization</span>
              </Link>
            </div>
          )}
        </div>

        <div className="relative" ref={envRef}>
          <button
            type="button"
            onClick={() => setEnvOpen((o) => !o)}
            className="flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium text-muted-foreground transition-colors duration-200 hover:bg-hover hover:text-foreground"
          >
            <Monitor className="h-4 w-4" />
            {envLabel}
            <ChevronDown className="h-4 w-4" />
          </button>
          {envOpen && (
            <div className="dropdown-panel absolute left-0 top-full z-50 mt-1.5 w-36 animate-fade-in">
              <div className="dropdown-section-header">Environment</div>
              <div className="space-y-0.5">
                {(["development", "production"] as Environment[]).map((env) => (
                  <button
                    key={env}
                    type="button"
                    onClick={() => {
                      setEnvironment(env);
                      setEnvOpen(false);
                    }}
                    className={`dropdown-item capitalize ${
                      environment === env ? "bg-muted font-medium" : ""
                    }`}
                  >
                    {env === "development" ? "Dev" : "Prod"}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2">
        <ThemeToggle />
        <a
          href="#"
          className="hidden items-center gap-2 rounded-xl px-3 py-2 text-2xs font-medium text-muted-foreground transition-colors duration-200 hover:bg-hover hover:text-foreground sm:flex"
          title="System status"
        >
          <span className="h-2 w-2 shrink-0 rounded-full bg-emerald-500 shadow-[0_0_6px_rgba(16,185,129,0.5)]" />
          All systems operational
        </a>

        <div className="relative" ref={notifRef}>
          <button
            type="button"
            onClick={() => setNotifOpen((o) => !o)}
            className="relative flex items-center justify-center rounded-xl p-2 text-muted-foreground transition-colors duration-200 hover:bg-hover hover:text-foreground"
            aria-label="Notifications"
          >
            <Bell className="h-4 w-4" />
            {unreadCount > 0 && (
              <span className="absolute -right-0.5 -top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-primary text-[10px] font-medium text-primary-foreground">
                {unreadCount > 9 ? "9+" : unreadCount}
              </span>
            )}
          </button>
          {notifOpen && (
            <div className="dropdown-panel absolute right-0 top-full z-50 mt-1.5 w-80 animate-fade-in">
              <div className="flex items-center justify-between border-b border-border pb-2 mb-2">
                <span className="text-2xs font-medium uppercase tracking-wide text-muted-foreground">
                  Notifications
                </span>
                {unreadCount > 0 && (
                  <button
                    type="button"
                    onClick={markAllRead}
                    className="text-2xs font-medium text-primary hover:underline"
                  >
                    Mark all read
                  </button>
                )}
              </div>
              <div className="max-h-80 overflow-y-auto -mx-0.5">
                {notifications.length === 0 ? (
                  <div className="px-3 py-6 text-center text-sm text-muted-foreground">
                    No notifications yet.
                  </div>
                ) : (
                  notifications.map((n) => (
                    <button
                      key={n.id}
                      type="button"
                      onClick={() => markAsRead(n.id)}
                      className={`dropdown-item flex-col items-stretch gap-0.5 py-2 ${
                        !n.read ? "bg-muted/50" : ""
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2 w-full">
                        <span className="text-sm font-medium text-foreground">
                          {n.title}
                        </span>
                        <span className="text-2xs text-muted-foreground shrink-0">
                          {formatNotificationTime(n.createdAt)}
                        </span>
                      </div>
                      {n.message && (
                        <p className="text-2xs text-muted-foreground line-clamp-2 text-left w-full">
                          {n.message}
                        </p>
                      )}
                    </button>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        <div className="relative" ref={userRef}>
          <button
            type="button"
            onClick={() => setUserOpen((o) => !o)}
            className="flex items-center gap-2 rounded-xl px-3 py-2 text-sm text-foreground transition-colors duration-200 hover:bg-hover"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-border">
              <User className="h-4 w-4 text-muted-foreground" />
            </div>
            <span className="hidden font-medium sm:inline">{user?.name}</span>
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          </button>
          {userOpen && (
            <div className="dropdown-panel absolute right-0 top-full z-50 mt-1.5 w-56 animate-fade-in">
              <div className="dropdown-section-header">Account</div>
              <div className="border-b border-border px-3 py-2 mb-2">
                <div className="font-medium text-sm text-card-foreground">{user?.name}</div>
                <div className="text-xs text-muted-foreground">{user?.email}</div>
                <div className="mt-0.5 text-2xs text-muted-foreground capitalize">
                  {user?.role}
                </div>
              </div>
              <div className="space-y-0.5">
                <Link
                  to="/app/settings"
                  onClick={() => setUserOpen(false)}
                  className="dropdown-item"
                >
                  <User className="h-4 w-4 shrink-0" />
                  Settings
                </Link>
                <Link
                  to="/app/sessions"
                  onClick={() => setUserOpen(false)}
                  className="dropdown-item"
                >
                  <Monitor className="h-4 w-4 shrink-0" />
                  Sessions {sessions.length > 0 && `(${sessions.length})`}
                </Link>
                <button
                  type="button"
                  onClick={() => {
                    signOut();
                    setUserOpen(false);
                  }}
                  className="dropdown-item w-full text-left"
                >
                  <LogOut className="h-4 w-4 shrink-0" />
                  Sign out
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
