/** Organization-level role. Order: owner > admin > developer > viewer */
export type OrgRole = "owner" | "admin" | "developer" | "viewer";

export interface User {
  id: string;
  email: string;
  name: string;
  /** Role in current org; for display. Check org membership for actual role. */
  role: OrgRole;
  avatarUrl?: string;
}

/** Billing plan id. Must match Stripe price ids in production. */
export type PlanId = "free" | "pro" | "business" | "enterprise";

export interface Organization {
  id: string;
  name: string;
  slug: string;
  plan: PlanId;
  /** Current user's role in this org */
  role: OrgRole;
  /** Monthly or yearly billing interval (for paid plans) */
  billingInterval?: "month" | "year";
  /** Organization logo URL (data URL or CDN) */
  logoUrl?: string | null;
}

export interface OrgMember {
  id: string;
  userId: string;
  email: string;
  name: string;
  role: OrgRole;
  joinedAt: string;
}

export interface OrgInvitation {
  id: string;
  email: string;
  role: OrgRole;
  status: "pending" | "accepted" | "expired";
  createdAt: string;
  inviterName: string;
}

export interface Session {
  id: string;
  device: string;
  location?: string;
  ip?: string;
  lastActiveAt: string;
  /** Current session */
  current: boolean;
}

export interface AuditLogEntry {
  id: string;
  action: string;
  actorEmail: string;
  actorName: string;
  resourceType: string;
  resourceId?: string;
  metadata?: Record<string, unknown>;
  timestamp: string;
}

export type Environment = "development" | "production";

/** Tool capabilities that can be toggled per agent */
export type AgentToolId =
  | "knowledge_base"
  | "web_search"
  | "calculator"
  | "code_interpreter"
  | "function_calling";

export interface AgentRateLimits {
  requestsPerMinute: number;
  concurrentConversations: number;
}

export interface AgentConfig {
  language: string;
  voiceId: string;
  temperature: number;
  toolToggles: Record<AgentToolId, boolean>;
  knowledgeBaseIds: string[];
  rateLimits: AgentRateLimits;
}

export interface AgentVersion {
  id: string;
  version: number;
  label: string;
  configSnapshot: AgentConfig;
  createdAt: string;
}

export interface Agent {
  id: string;
  name: string;
  description: string;
  status: "active" | "paused" | "draft";
  createdAt: string;
  updatedAt?: string;
  conversationCount?: number;
  config?: AgentConfig;
  versionHistory?: AgentVersion[];
}

export interface KnowledgeArticle {
  id: string;
  title: string;
  slug: string;
  status: "published" | "draft";
  updatedAt: string;
}

export type EmbeddingStatus = "pending" | "indexing" | "ready" | "failed";

export interface KnowledgeChunk {
  id: string;
  documentId: string;
  index: number;
  text: string;
  tokenCount?: number;
}

export interface KnowledgeDocument {
  id: string;
  name: string;
  fileType: "pdf" | "txt";
  size: number;
  uploadedAt: string;
  embeddingStatus: EmbeddingStatus;
  indexingProgress?: number;
  chunkCount: number;
  chunks: KnowledgeChunk[];
}

export interface ApiKey {
  id: string;
  name: string;
  prefix: string;
  /** Full secret shown only once after create/regenerate */
  secret?: string;
  lastUsedAt: string | null;
  createdAt: string;
}

export interface WebhookEndpoint {
  id: string;
  url: string;
  description?: string;
  events: string[];
  signingSecretPrefix: string;
  createdAt: string;
  enabled: boolean;
}

export interface ApiUsageLogEntry {
  id: string;
  timestamp: string;
  method: string;
  path: string;
  status: number;
  keyId: string;
  keyName: string;
  durationMs?: number;
}

export interface ApiRateLimitDisplay {
  limit: number;
  remaining: number;
  window: string;
  resetsAt: string;
}

export interface UsageSummary {
  voiceMinutes: number;
  llmTokens: number;
  ttsSeconds: number;
  apiCalls: number;
  period: string;
}

/** Plan limits per billing period. 0 or undefined = unlimited. */
export interface PlanLimits {
  voiceMinutes: number;
  llmTokens: number;
  ttsSeconds: number;
  apiCalls: number;
}

export interface BillingPlan {
  id: PlanId;
  name: string;
  priceMonthly: number;
  priceYearly: number;
  /** Price id for Stripe (monthly). Used for checkout. */
  stripePriceIdMonthly?: string;
  /** Price id for Stripe (yearly). */
  stripePriceIdYearly?: string;
  limits: PlanLimits;
  features: string[];
  /** Enterprise is contact sales only */
  contactSales?: boolean;
}

export interface Invoice {
  id: string;
  number: string;
  amountDue: number;
  amountPaid: number;
  status: "draft" | "open" | "paid" | "void" | "uncollectible";
  date: string;
  periodStart: string;
  periodEnd: string;
  invoicePdfUrl?: string;
}

export interface PaymentMethod {
  id: string;
  brand: string;
  last4: string;
  expMonth: number;
  expYear: number;
  isDefault: boolean;
}

/** Role hierarchy for permission checks */
export const ORG_ROLE_ORDER: OrgRole[] = ["viewer", "developer", "admin", "owner"];
export function hasMinimumRole(userRole: OrgRole, required: OrgRole): boolean {
  return ORG_ROLE_ORDER.indexOf(userRole) >= ORG_ROLE_ORDER.indexOf(required);
}
