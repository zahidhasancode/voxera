export type CallStatus = "ringing" | "active" | "on_hold" | "transferring" | "ended";

export interface LiveCall {
  id: string;
  agentId: string;
  agentName: string;
  customerId: string;
  customerName: string;
  status: CallStatus;
  language: string;
  startedAt: string;
  durationSec: number;
  intent: string;
  plannerState: string;
  workflowState: string;
  currentTool: string | null;
  riskScore: number;
  latencyMs: number;
  transcript: TranscriptLine[];
  memorySnapshot: Record<string, string>;
}

export interface TranscriptLine {
  id: string;
  role: "user" | "agent" | "system";
  text: string;
  timestamp: string;
}

export interface DashboardMetrics {
  todaysCalls: number;
  activeCalls: number;
  aiResolutionRate: number;
  escalationRate: number;
  avgCallDurationSec: number;
  avgLatencyMs: number;
  costTodayUsd: number;
  knowledgeSources: number;
  activeAgents: number;
  workflowSuccessRate: number;
  systemHealth: "healthy" | "degraded" | "critical";
}

export interface ActivityEvent {
  id: string;
  type: "call" | "workflow" | "tool" | "knowledge" | "agent" | "system";
  title: string;
  description: string;
  timestamp: string;
  severity?: "info" | "warning" | "error" | "success";
}

export interface WorkflowDefinition {
  id: string;
  name: string;
  slug: string;
  enabled: boolean;
  steps: { id: string; label: string; type: string }[];
  rulesCount: number;
  approvalSteps: number;
  escalationTargets: string[];
  lastModified: string;
}

export interface ToolRegistryEntry {
  id: string;
  slug: string;
  name: string;
  category: string;
  status: "healthy" | "degraded" | "disabled";
  enabled: boolean;
  avgLatencyMs: number;
  executions24h: number;
  failures24h: number;
  permissions: string[];
}

export interface TenantSummary {
  id: string;
  name: string;
  plan: string;
  status: "active" | "suspended" | "trial";
  agents: number;
  knowledgeDocs: number;
  storageGb: number;
  usageMinutes: number;
  apiKeys: number;
}

export interface PlatformUser {
  id: string;
  name: string;
  email: string;
  role: string;
  status: "active" | "invited" | "suspended";
  lastActiveAt: string;
  sessions: number;
}

export interface CallTimelineEvent {
  id: string;
  category: "transcript" | "planner" | "verifier" | "tool" | "knowledge" | "workflow" | "audio" | "latency";
  title: string;
  detail?: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
}
