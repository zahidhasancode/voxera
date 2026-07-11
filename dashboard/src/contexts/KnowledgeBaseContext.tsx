import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  type ReactNode,
} from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { EmbeddingStatus, KnowledgeChunk, KnowledgeDocument } from "@/types";
import { useOrg } from "@/contexts/OrgContext";
import {
  deleteKnowledgeSource,
  listKnowledgeSources,
  reprocessKnowledge,
  uploadKnowledgeFile,
} from "@/lib/api/knowledge";
import { mapKnowledgeSource } from "@/lib/mappers";
import { queryKeys } from "@/hooks/queryKeys";

type KnowledgeBaseContextValue = {
  documents: KnowledgeDocument[];
  isLoading: boolean;
  error: Error | null;
  getDocumentById: (id: string) => KnowledgeDocument | undefined;
  addDocument: (doc: Omit<KnowledgeDocument, "id" | "uploadedAt">, file?: File) => Promise<KnowledgeDocument>;
  deleteDocument: (id: string) => Promise<void>;
  reindexDocument: (id: string) => Promise<void>;
  updateDocumentProgress: (id: string, progress: number, chunkCount?: number, chunks?: KnowledgeChunk[]) => void;
  setDocumentStatus: (id: string, status: EmbeddingStatus) => void;
  searchTest: (query: string) => { documentId: string; chunkId: string; score: number; snippet: string }[];
};

const KnowledgeBaseContext = createContext<KnowledgeBaseContextValue | null>(null);

export function KnowledgeBaseProvider({ children }: { children: ReactNode }) {
  const { tenantId } = useOrg();
  const queryClient = useQueryClient();

  const docsQuery = useQuery({
    queryKey: queryKeys.knowledge(tenantId ?? "none"),
    enabled: Boolean(tenantId),
    refetchInterval: (query) => {
      const docs = query.state.data ?? [];
      return docs.some((d) => d.embeddingStatus === "indexing") ? 3000 : 30_000;
    },
    queryFn: async () => {
      const res = await listKnowledgeSources(tenantId!);
      return res.items.map(mapKnowledgeSource);
    },
  });

  const invalidate = useCallback(() => {
    if (tenantId) {
      queryClient.invalidateQueries({ queryKey: queryKeys.knowledge(tenantId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.knowledgeStatus(tenantId) });
    }
  }, [queryClient, tenantId]);

  const uploadMutation = useMutation({
    mutationFn: async ({
      doc,
      file,
    }: {
      doc: Omit<KnowledgeDocument, "id" | "uploadedAt">;
      file?: File;
    }) => {
      if (!tenantId || !file) throw new Error("File and tenant required");
      const sourceType = doc.fileType === "pdf" ? "pdf" : "txt";
      const row = await uploadKnowledgeFile(tenantId, file, doc.name, sourceType);
      return mapKnowledgeSource(row);
    },
    onSuccess: invalidate,
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      if (!tenantId) throw new Error("Tenant not configured");
      await deleteKnowledgeSource(tenantId, id);
    },
    onSuccess: invalidate,
  });

  const reindexMutation = useMutation({
    mutationFn: async (id: string) => {
      if (!tenantId) throw new Error("Tenant not configured");
      await reprocessKnowledge(tenantId, [id], true);
    },
    onSuccess: invalidate,
  });

  const documents = docsQuery.data ?? [];

  const getDocumentById = useCallback(
    (id: string) => documents.find((d) => d.id === id),
    [documents],
  );

  const addDocument = useCallback(
    async (doc: Omit<KnowledgeDocument, "id" | "uploadedAt">, file?: File) =>
      uploadMutation.mutateAsync({ doc, file }),
    [uploadMutation],
  );

  const deleteDocument = useCallback(
    async (id: string) => deleteMutation.mutateAsync(id),
    [deleteMutation],
  );

  const reindexDocument = useCallback(
    async (id: string) => reindexMutation.mutateAsync(id),
    [reindexMutation],
  );

  const updateDocumentProgress = useCallback(() => {}, []);
  const setDocumentStatus = useCallback(() => {}, []);

  const searchTest = useCallback((_query: string) => [], []);

  const value = useMemo<KnowledgeBaseContextValue>(
    () => ({
      documents,
      isLoading: docsQuery.isLoading,
      error: docsQuery.error as Error | null,
      getDocumentById,
      addDocument,
      deleteDocument,
      reindexDocument,
      updateDocumentProgress,
      setDocumentStatus,
      searchTest,
    }),
    [
      documents,
      docsQuery.isLoading,
      docsQuery.error,
      getDocumentById,
      addDocument,
      deleteDocument,
      reindexDocument,
      searchTest,
    ],
  );

  return (
    <KnowledgeBaseContext.Provider value={value}>{children}</KnowledgeBaseContext.Provider>
  );
}

export function useKnowledgeBase() {
  const ctx = useContext(KnowledgeBaseContext);
  if (!ctx) throw new Error("useKnowledgeBase must be used within KnowledgeBaseProvider");
  return ctx;
}
