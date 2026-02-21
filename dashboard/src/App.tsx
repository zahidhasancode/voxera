import { Routes, Route, Navigate } from "react-router-dom";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { Landing } from "@/pages/Landing";
import { Overview } from "@/pages/Overview";
import { Agents } from "@/pages/Agents";
import { AgentEdit } from "@/pages/AgentEdit";
import { KnowledgeBase } from "@/pages/KnowledgeBase";
import { Developer } from "@/pages/Developer";
import { Usage } from "@/pages/Usage";
import { Analytics } from "@/pages/Analytics";
import { Enterprise } from "@/pages/Enterprise";
import { Billing } from "@/pages/Billing";
import { Invoices } from "@/pages/Invoices";
import { Organization } from "@/pages/Organization";
import { CreateOrganization } from "@/pages/CreateOrganization";
import { AuditLog } from "@/pages/AuditLog";
import { Sessions } from "@/pages/Sessions";
import { Settings } from "@/pages/Settings";
import { Login } from "@/pages/Login";

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
        <Route index element={<Overview />} />
        <Route path="agents" element={<Agents />} />
        <Route path="agents/new" element={<AgentEdit />} />
        <Route path="agents/:id" element={<AgentEdit />} />
        <Route path="knowledge" element={<KnowledgeBase />} />
        <Route path="developer" element={<Developer />} />
        <Route path="api-keys" element={<Developer />} />
        <Route path="usage" element={<Usage />} />
        <Route path="analytics" element={<Analytics />} />
        <Route path="enterprise" element={<Enterprise />} />
        <Route path="billing" element={<Billing />} />
        <Route path="billing/invoices" element={<Invoices />} />
        <Route path="organization" element={<Organization />} />
        <Route path="organization/new" element={<CreateOrganization />} />
        <Route path="audit-log" element={<AuditLog />} />
        <Route path="sessions" element={<Sessions />} />
        <Route path="settings" element={<Settings />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
