import { describe, it, expect } from "vitest";
import { mapAgent, mapKnowledgeSource, mapTool, mapAuditLog } from "./mappers";
import type { BackendAgent } from "./api/agents";
import type { KnowledgeSource } from "./api/knowledge";
import type { BackendTool } from "./api/tools";
import type { BackendAuditLog } from "./api/audit";

describe("mapAgent", () => {
  it("maps backend agent to UI agent", () => {
    const row = {
      id: "a1",
      tenant_id: "t1",
      name: "Support",
      description: "Help desk",
      status: "active",
      language: "en-US",
      voice: "alloy",
      temperature: 0.7,
      system_prompt: null,
      max_reasoning_steps: 5,
      planner_model: null,
      verifier_model: null,
      created_at: "2024-01-01T00:00:00Z",
      updated_at: "2024-01-02T00:00:00Z",
    } as unknown as BackendAgent;
    const agent = mapAgent(row);
    expect(agent.id).toBe("a1");
    expect(agent.name).toBe("Support");
    expect(agent.config?.language).toBe("en-US");
    expect(agent.status).toBe("active");
  });

  it("maps archived status to paused", () => {
    const row = {
      id: "a1",
      tenant_id: "t1",
      name: "X",
      description: null,
      status: "archived",
      language: "en-US",
      voice: "alloy",
      temperature: 0.5,
      created_at: "2024-01-01T00:00:00Z",
      updated_at: "2024-01-02T00:00:00Z",
    } as unknown as BackendAgent;
    expect(mapAgent(row).status).toBe("paused");
  });
});

describe("mapKnowledgeSource", () => {
  it("maps processing status to indexing", () => {
    const row = {
      id: "k1",
      tenant_id: "t1",
      title: "Policy",
      original_filename: "policy.pdf",
      file_size_bytes: 1024,
      source_type: "pdf",
      status: "processing",
      embedding_status: "pending",
      embedding_count: 0,
      chunk_count: 0,
      processing_percent: 50,
      progress_pct: 50,
      processing_error: null,
      created_at: "2024-01-01T00:00:00Z",
      updated_at: "2024-01-01T00:00:00Z",
    } as KnowledgeSource;
    const doc = mapKnowledgeSource(row);
    expect(doc.embeddingStatus).toBe("indexing");
    expect(doc.fileType).toBe("pdf");
    expect(doc.indexingProgress).toBe(50);
  });
});

describe("mapTool", () => {
  it("maps active tool as healthy and enabled", () => {
    const row: BackendTool = {
      id: "tool1",
      tenant_id: "t1",
      name: "Lookup",
      slug: "lookup",
      description: null,
      tool_type: "api",
      status: "active",
      created_at: "2024-01-01T00:00:00Z",
      updated_at: "2024-01-01T00:00:00Z",
    };
    const tool = mapTool(row);
    expect(tool.enabled).toBe(true);
    expect(tool.status).toBe("healthy");
  });
});

describe("mapAuditLog", () => {
  it("maps audit log entry", () => {
    const row: BackendAuditLog = {
      id: "log1",
      tenant_id: "t1",
      action: "agent.created",
      actor_id: "user1",
      resource_type: "agent",
      resource_id: "a1",
      metadata: { name: "Support" },
      created_at: "2024-01-01T12:00:00Z",
    };
    const entry = mapAuditLog(row);
    expect(entry.action).toBe("agent.created");
    expect(entry.resourceType).toBe("agent");
    expect(entry.metadata).toEqual({ name: "Support" });
  });
});
