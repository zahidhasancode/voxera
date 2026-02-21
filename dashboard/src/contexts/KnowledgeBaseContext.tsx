import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type {
  EmbeddingStatus,
  KnowledgeChunk,
  KnowledgeDocument,
} from "@/types";

function createChunks(documentId: string, count: number): KnowledgeChunk[] {
  return Array.from({ length: count }, (_, i) => ({
    id: `${documentId}_chunk_${i + 1}`,
    documentId,
    index: i + 1,
    text: `This is chunk ${i + 1} of the document. Sample content for preview and retrieval testing.`,
    tokenCount: 42 + i * 5,
  }));
}

const INITIAL_DOCS: KnowledgeDocument[] = [
  {
    id: "doc_1",
    name: "Returns policy.pdf",
    fileType: "pdf",
    size: 245_000,
    uploadedAt: "2024-03-01T14:00:00Z",
    embeddingStatus: "ready",
    chunkCount: 12,
    chunks: createChunks("doc_1", 12),
  },
  {
    id: "doc_2",
    name: "Shipping options.txt",
    fileType: "txt",
    size: 18_400,
    uploadedAt: "2024-02-28T09:30:00Z",
    embeddingStatus: "ready",
    chunkCount: 4,
    chunks: createChunks("doc_2", 4),
  },
  {
    id: "doc_3",
    name: "Enterprise SSO.pdf",
    fileType: "pdf",
    size: 512_000,
    uploadedAt: "2024-03-10T11:00:00Z",
    embeddingStatus: "indexing",
    indexingProgress: 65,
    chunkCount: 0,
    chunks: [],
  },
];

type KnowledgeBaseContextValue = {
  documents: KnowledgeDocument[];
  getDocumentById: (id: string) => KnowledgeDocument | undefined;
  addDocument: (doc: Omit<KnowledgeDocument, "id" | "uploadedAt">) => KnowledgeDocument;
  deleteDocument: (id: string) => void;
  reindexDocument: (id: string) => void;
  updateDocumentProgress: (id: string, progress: number, chunkCount?: number, chunks?: KnowledgeChunk[]) => void;
  setDocumentStatus: (id: string, status: EmbeddingStatus) => void;
  searchTest: (query: string) => { documentId: string; chunkId: string; score: number; snippet: string }[];
};

const KnowledgeBaseContext = createContext<KnowledgeBaseContextValue | null>(null);

export function KnowledgeBaseProvider({ children }: { children: ReactNode }) {
  const [documents, setDocuments] = useState<KnowledgeDocument[]>(INITIAL_DOCS);

  const getDocumentById = useCallback(
    (id: string) => documents.find((d) => d.id === id),
    [documents]
  );

  const addDocument = useCallback(
    (doc: Omit<KnowledgeDocument, "id" | "uploadedAt">) => {
      const id = `doc_${Date.now()}`;
      const uploadedAt = new Date().toISOString();
      const newDoc: KnowledgeDocument = {
        ...doc,
        id,
        uploadedAt,
        embeddingStatus: "indexing",
        indexingProgress: 0,
        chunkCount: doc.chunkCount ?? 0,
        chunks: doc.chunks ?? [],
      };
      setDocuments((prev) => [...prev, newDoc]);
      return newDoc;
    },
    []
  );

  const deleteDocument = useCallback((id: string) => {
    setDocuments((prev) => prev.filter((d) => d.id !== id));
  }, []);

  const reindexDocument = useCallback((id: string) => {
    setDocuments((prev) =>
      prev.map((d) => {
        if (d.id !== id) return d;
        return {
          ...d,
          embeddingStatus: "indexing" as const,
          indexingProgress: 0,
        };
      })
    );
    // Simulate progress
    const interval = setInterval(() => {
      setDocuments((prev) =>
        prev.map((d) => {
          if (d.id !== id) return d;
          if (d.indexingProgress === undefined || d.indexingProgress >= 100) {
            clearInterval(interval);
            return {
              ...d,
              embeddingStatus: "ready" as const,
              indexingProgress: 100,
              chunkCount: d.chunkCount || 8,
              chunks: d.chunks.length ? d.chunks : createChunks(id, 8),
            };
          }
          return { ...d, indexingProgress: Math.min(d.indexingProgress + 15, 100) };
        })
      );
    }, 400);
    setTimeout(() => clearInterval(interval), 2500);
  }, []);

  const updateDocumentProgress = useCallback(
    (id: string, progress: number, chunkCount?: number, chunks?: KnowledgeChunk[]) => {
      setDocuments((prev) =>
        prev.map((d) => {
          if (d.id !== id) return d;
          const next: KnowledgeDocument = {
            ...d,
            indexingProgress: progress,
            ...(chunkCount !== undefined && { chunkCount }),
            ...(chunks !== undefined && { chunks }),
          };
          if (progress >= 100) {
            next.embeddingStatus = "ready";
            next.indexingProgress = 100;
          }
          return next;
        })
      );
    },
    []
  );

  const setDocumentStatus = useCallback((id: string, status: EmbeddingStatus) => {
    setDocuments((prev) =>
      prev.map((d) =>
        d.id === id ? { ...d, embeddingStatus: status, indexingProgress: status === "ready" ? 100 : undefined } : d
      )
    );
  }, []);

  const searchTest = useCallback((query: string) => {
    if (!query.trim()) return [];
    const results: { documentId: string; chunkId: string; score: number; snippet: string }[] = [];
    documents.forEach((d) => {
      d.chunks?.slice(0, 2).forEach((c, i) => {
        results.push({
          documentId: d.id,
          chunkId: c.id,
          score: 0.92 - i * 0.05,
          snippet: c.text.slice(0, 120) + (c.text.length > 120 ? "…" : ""),
        });
      });
    });
    return results.slice(0, 6);
  }, [documents]);

  const value = useMemo<KnowledgeBaseContextValue>(
    () => ({
      documents,
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
      getDocumentById,
      addDocument,
      deleteDocument,
      reindexDocument,
      updateDocumentProgress,
      setDocumentStatus,
      searchTest,
    ]
  );

  return (
    <KnowledgeBaseContext.Provider value={value}>
      {children}
    </KnowledgeBaseContext.Provider>
  );
}

export function useKnowledgeBase() {
  const ctx = useContext(KnowledgeBaseContext);
  if (!ctx) throw new Error("useKnowledgeBase must be used within KnowledgeBaseProvider");
  return ctx;
}
