import { lazy, Suspense } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { Landing } from "@/pages/Landing";
import { Login } from "@/pages/Login";
import { Skeleton } from "@/components/ui/Skeleton";

const Overview = lazy(() => import("@/pages/Overview").then((m) => ({ default: m.Overview })));
const LiveCalls = lazy(() => import("@/pages/LiveCalls").then((m) => ({ default: m.LiveCalls })));
const CallDetails = lazy(() => import("@/pages/CallDetails").then((m) => ({ default: m.CallDetails })));
const Agents = lazy(() => import("@/pages/Agents").then((m) => ({ default: m.Agents })));
const AgentEdit = lazy(() => import("@/pages/AgentEdit").then((m) => ({ default: m.AgentEdit })));
const KnowledgeBase = lazy(() => import("@/pages/KnowledgeBase").then((m) => ({ default: m.KnowledgeBase })));
const Workflows = lazy(() => import("@/pages/Workflows").then((m) => ({ default: m.Workflows })));
const ToolRegistry = lazy(() => import("@/pages/ToolRegistry").then((m) => ({ default: m.ToolRegistry })));
const Integrations = lazy(() => import("@/pages/Integrations").then((m) => ({ default: m.Integrations })));
const Tenants = lazy(() => import("@/pages/Tenants").then((m) => ({ default: m.Tenants })));
const Users = lazy(() => import("@/pages/Users").then((m) => ({ default: m.Users })));
const Developer = lazy(() => import("@/pages/Developer").then((m) => ({ default: m.Developer })));
const Usage = lazy(() => import("@/pages/Usage").then((m) => ({ default: m.Usage })));
const Analytics = lazy(() => import("@/pages/Analytics").then((m) => ({ default: m.Analytics })));
const Enterprise = lazy(() => import("@/pages/Enterprise").then((m) => ({ default: m.Enterprise })));
const Billing = lazy(() => import("@/pages/Billing").then((m) => ({ default: m.Billing })));
const Invoices = lazy(() => import("@/pages/Invoices").then((m) => ({ default: m.Invoices })));
const Organization = lazy(() => import("@/pages/Organization").then((m) => ({ default: m.Organization })));
const CreateOrganization = lazy(() => import("@/pages/CreateOrganization").then((m) => ({ default: m.CreateOrganization })));
const AuditLog = lazy(() => import("@/pages/AuditLog").then((m) => ({ default: m.AuditLog })));
const Sessions = lazy(() => import("@/pages/Sessions").then((m) => ({ default: m.Sessions })));
const Settings = lazy(() => import("@/pages/Settings").then((m) => ({ default: m.Settings })));

function PageFallback() {
  return (
    <div className="space-y-4 p-2">
      <Skeleton className="h-8 w-48" />
      <Skeleton className="h-64 w-full rounded-xl" />
    </div>
  );
}

function Lazy({ children }: { children: React.ReactNode }) {
  return <Suspense fallback={<PageFallback />}>{children}</Suspense>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route
        path="/app"
        element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Lazy><Overview /></Lazy>} />
        <Route path="live-calls" element={<Lazy><LiveCalls /></Lazy>} />
        <Route path="calls/:callId" element={<Lazy><CallDetails /></Lazy>} />
        <Route path="agents" element={<Lazy><Agents /></Lazy>} />
        <Route path="agents/new" element={<Lazy><AgentEdit /></Lazy>} />
        <Route path="agents/:id" element={<Lazy><AgentEdit /></Lazy>} />
        <Route path="knowledge" element={<Lazy><KnowledgeBase /></Lazy>} />
        <Route path="workflows" element={<Lazy><Workflows /></Lazy>} />
        <Route path="tools" element={<Lazy><ToolRegistry /></Lazy>} />
        <Route path="integrations" element={<Lazy><Integrations /></Lazy>} />
        <Route path="tenants" element={<Lazy><Tenants /></Lazy>} />
        <Route path="users" element={<Lazy><Users /></Lazy>} />
        <Route path="developer" element={<Lazy><Developer /></Lazy>} />
        <Route path="api-keys" element={<Lazy><Developer /></Lazy>} />
        <Route path="usage" element={<Lazy><Usage /></Lazy>} />
        <Route path="analytics" element={<Lazy><Analytics /></Lazy>} />
        <Route path="enterprise" element={<Lazy><Enterprise /></Lazy>} />
        <Route path="billing" element={<Lazy><Billing /></Lazy>} />
        <Route path="billing/invoices" element={<Lazy><Invoices /></Lazy>} />
        <Route path="organization" element={<Lazy><Organization /></Lazy>} />
        <Route path="organization/new" element={<Lazy><CreateOrganization /></Lazy>} />
        <Route path="audit-log" element={<Lazy><AuditLog /></Lazy>} />
        <Route path="sessions" element={<Lazy><Sessions /></Lazy>} />
        <Route path="settings" element={<Lazy><Settings /></Lazy>} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
