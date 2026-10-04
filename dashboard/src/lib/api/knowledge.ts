import { api, apiUpload } from "./client";

export interface KnowledgeSource {
  id: string;
  tenant_id: string;
  title: string;
  source_type: string;
  status: string;
  progress_pct: number;
  chunk_count: number;
  embedding_count: number;
  embedding_status: string;
  file_size_bytes: number | null;
  original_filename: string | null;
  processing_error: string | null;
  is_processing?: boolean;
  processing_percent?: number;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeListResponse {
  items: KnowledgeSource[];
  total: number;
  offset: number;
  limit: number;
}

export interface KnowledgeStatusSummary {
  total_sources: number;
  pending: number;
  processing: number;
  ready: number;
  failed: number;
  total_chunks: number;
  total_embeddings: number;
}

export function listKnowledgeSources(tenantId: string, offset = 0, limit = 100) {
  return api.get<KnowledgeListResponse>(`/knowledge?offset=${offset}&limit=${limit}`, { tenantId });
}

export function getKnowledgeStatus(tenantId: string) {
  return api.get<KnowledgeStatusSummary>("/knowledge/status", { tenantId });
}

export function deleteKnowledgeSource(tenantId: string, sourceId: string) {
  return api.delete(`/knowledge/${sourceId}`, { tenantId });
}

export function reprocessKnowledge(tenantId: string, sourceIds?: string[], force = false) {
  return api.post<KnowledgeSource[]>(
    "/knowledge/reprocess",
    { source_ids: sourceIds ?? [], force },
    { tenantId },
  );
}

export function uploadKnowledgeFile(
  tenantId: string,
  file: File,
  title: string,
  sourceType: string,
) {
  const form = new FormData();
  form.append("file", file);
  form.append("title", title);
  form.append("source_type", sourceType);
  return apiUpload<KnowledgeSource>("/knowledge/upload", form, tenantId);
}
