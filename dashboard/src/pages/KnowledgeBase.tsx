import {
  FileText,
  Loader2,
  RefreshCw,
  Search,
  Trash2,
  Upload,
} from "lucide-react";
import { useCallback, useRef, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Input } from "@/components/ui/Input";
import { PageHeader } from "@/components/layout/PageHeader";
import { useKnowledgeBase } from "@/contexts/KnowledgeBaseContext";
import type {
  EmbeddingStatus,
  KnowledgeChunk,
  KnowledgeDocument,
} from "@/types";

const ACCEPT = ".pdf,.txt";
const MAX_FILE_MB = 20;

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: "short",
    timeStyle: "short",
  });
}

function EmbeddingStatusBadge({
  status,
  progress,
}: {
  status: EmbeddingStatus;
  progress?: number;
}) {
  if (status === "indexing" && progress !== undefined) {
    return (
      <div className="flex min-w-[100px] items-center gap-2">
        <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-border">
          <div
            className="h-full rounded-full bg-primary transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
        <span className="text-2xs text-muted-foreground">{progress}%</span>
      </div>
    );
  }
  const variant: Record<EmbeddingStatus, "default" | "success" | "warning" | "error"> = {
    pending: "default",
    indexing: "warning",
    ready: "success",
    failed: "error",
  };
  return (
    <Badge variant={variant[status]}>
      {status === "indexing" && progress !== undefined ? `${progress}%` : status}
    </Badge>
  );
}

function ChunkPreviewModal({
  doc,
  onClose,
}: {
  doc: KnowledgeDocument;
  onClose: () => void;
}) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label="Chunk preview"
    >
      <div
        className="max-h-[80vh] w-full max-w-2xl overflow-hidden rounded-xl border border-border bg-card shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-border px-6 py-4">
          <h3 className="font-semibold text-white">
            Chunk preview — {doc.name}
          </h3>
          <Button variant="ghost" size="sm" onClick={onClose}>
            Close
          </Button>
        </div>
        <div className="max-h-[60vh] overflow-y-auto p-6">
          {doc.chunks && doc.chunks.length > 0 ? (
            <ul className="space-y-4">
              {doc.chunks.map((chunk) => (
                <li
                  key={chunk.id}
                  className="rounded-lg border border-border bg-background p-4"
                >
                  <div className="mb-2 flex items-center gap-2 text-xs text-muted-foreground">
                    <span className="font-medium">Chunk {chunk.index}</span>
                    {chunk.tokenCount != null && (
                      <span>· {chunk.tokenCount} tokens</span>
                    )}
                  </div>
                  <p className="text-sm text-white whitespace-pre-wrap">
                    {chunk.text}
                  </p>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">
              No chunks yet. Re-index this document to generate chunks.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

export function KnowledgeBase() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [dragOver, setDragOver] = useState(false);
  const [chunkPreviewDoc, setChunkPreviewDoc] = useState<KnowledgeDocument | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<{ documentId: string; chunkId: string; score: number; snippet: string }[] | null>(null);
  const [searching, setSearching] = useState(false);

  const {
    documents,
    getDocumentById,
    addDocument,
    deleteDocument,
    reindexDocument,
    updateDocumentProgress,
    searchTest,
  } = useKnowledgeBase();

  const runIndexingSimulation = useCallback(
    (docId: string, chunkCount: number, chunks: KnowledgeChunk[]) => {
      let progress = 0;
      const step = 100 / 8;
      const interval = setInterval(() => {
        progress = Math.min(progress + step, 100);
        updateDocumentProgress(docId, progress, progress >= 100 ? chunkCount : undefined, progress >= 100 ? chunks : undefined);
        if (progress >= 100) clearInterval(interval);
      }, 250);
    },
    [updateDocumentProgress]
  );

  const handleFileSelect = useCallback(
    (files: FileList | null) => {
      if (!files?.length) return;
      const file = files[0];
      const ext = file.name.split(".").pop()?.toLowerCase();
      if (ext !== "pdf" && ext !== "txt") {
        alert("Please upload a PDF or TXT file.");
        return;
      }
      if (file.size > MAX_FILE_MB * 1024 * 1024) {
        alert(`File must be under ${MAX_FILE_MB} MB.`);
        return;
      }
      setUploading(true);
      setUploadProgress(0);
      const progressInterval = setInterval(() => {
        setUploadProgress((p) => {
          if (p >= 100) {
            clearInterval(progressInterval);
            const chunkCount = Math.max(1, Math.floor(file.size / 5000));
            const chunks = Array.from({ length: chunkCount }, (_, i) => ({
              id: `new_chunk_${i + 1}`,
              documentId: "",
              index: i + 1,
              text: `Chunk ${i + 1} from ${file.name}. Sample extracted text for embedding.`,
              tokenCount: 35 + i * 3,
            }));
            const added = addDocument({
              name: file.name,
              fileType: ext as "pdf" | "txt",
              size: file.size,
              embeddingStatus: "indexing",
              indexingProgress: 0,
              chunkCount: 0,
              chunks: [],
            });
            chunks.forEach((c) => {
              c.documentId = added.id;
            });
            runIndexingSimulation(added.id, chunkCount, chunks);
            setUploading(false);
            setUploadProgress(0);
            return 100;
          }
          return p + 10;
        });
      }, 120);
    },
    [addDocument, runIndexingSimulation]
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      handleFileSelect(e.dataTransfer.files);
    },
    [handleFileSelect]
  );

  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const onDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  }, []);

  const onSearch = useCallback(() => {
    setSearching(true);
    setSearchResults(null);
    setTimeout(() => {
      setSearchResults(searchTest(searchQuery));
      setSearching(false);
    }, 400);
  }, [searchQuery, searchTest]);

  return (
    <>
      <PageHeader
        title="Knowledge base"
        description="Upload documents, manage chunks, and test search"
      />

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader
              title="Upload documents"
              description="PDF or TXT, max 20 MB"
            />
            <CardContent>
              <input
                ref={inputRef}
                type="file"
                accept={ACCEPT}
                className="hidden"
                onChange={(e) => {
                  handleFileSelect(e.target.files);
                  e.target.value = "";
                }}
              />
              <div
                onDrop={onDrop}
                onDragOver={onDragOver}
                onDragLeave={onDragLeave}
                onClick={() => inputRef.current?.click()}
                className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed py-10 transition-colors ${
                  dragOver
                    ? "border-primary bg-primary/10"
                    : "border-border bg-background-hover/50 hover:border-border/80 hover:bg-background-hover"
                } ${uploading ? "pointer-events-none opacity-80" : ""}`}
              >
                {uploading ? (
                  <>
                    <Loader2 className="h-10 w-10 animate-spin text-primary" />
                    <p className="mt-3 text-sm font-medium text-white">
                      Uploading…
                    </p>
                    <div className="mt-2 h-1.5 w-48 overflow-hidden rounded-full bg-border">
                      <div
                        className="h-full rounded-full bg-primary transition-all"
                        style={{ width: `${uploadProgress}%` }}
                      />
                    </div>
                    <p className="mt-1 text-2xs text-muted-foreground">
                      {uploadProgress}%
                    </p>
                  </>
                ) : (
                  <>
                    <Upload className="h-10 w-10 text-muted-foreground" />
                    <p className="mt-3 text-sm font-medium text-white">
                      Drop files here or click to upload
                    </p>
                    <p className="mt-1 text-2xs text-muted-foreground">
                      PDF, TXT · max 20 MB
                    </p>
                  </>
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader
              title="Documents"
              description={`${documents.length} uploaded`}
            />
            <CardContent className="p-0">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border text-left text-sm text-muted-foreground">
                    <th className="px-6 py-3 font-medium">Name</th>
                    <th className="px-6 py-3 font-medium">Type</th>
                    <th className="px-6 py-3 font-medium">Size</th>
                    <th className="px-6 py-3 font-medium">Uploaded</th>
                    <th className="px-6 py-3 font-medium">Embedding</th>
                    <th className="px-6 py-3 font-medium">Chunks</th>
                    <th className="px-6 py-3 font-medium text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {documents.map((doc) => (
                    <tr
                      key={doc.id}
                      className="border-b border-border/50 transition-colors hover:bg-background-hover/50"
                    >
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <FileText className="h-4 w-4 text-muted-foreground" />
                          <span className="font-medium text-white">
                            {doc.name}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-muted-foreground uppercase">
                        {doc.fileType}
                      </td>
                      <td className="px-6 py-4 text-sm text-muted-foreground">
                        {formatSize(doc.size)}
                      </td>
                      <td className="px-6 py-4 text-sm text-muted-foreground">
                        {formatDate(doc.uploadedAt)}
                      </td>
                      <td className="px-6 py-4">
                        <EmbeddingStatusBadge
                          status={doc.embeddingStatus}
                          progress={doc.indexingProgress}
                        />
                      </td>
                      <td className="px-6 py-4 text-sm text-muted-foreground">
                        {doc.chunkCount}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setChunkPreviewDoc(doc)}
                            title="Chunk preview"
                            disabled={!doc.chunks?.length}
                          >
                            Preview
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => reindexDocument(doc.id)}
                            disabled={doc.embeddingStatus === "indexing"}
                            title="Re-index"
                          >
                            <RefreshCw className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => deleteDocument(doc.id)}
                            title="Delete"
                            className="text-red-400 hover:text-red-300"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {documents.length === 0 && (
                <div className="p-8">
                  <EmptyState
                    icon={<FileText className="h-6 w-6" />}
                    title="No documents yet"
                    description="Upload PDF or TXT files to build your knowledge base for RAG and search."
                    action={
                      <Button onClick={() => inputRef.current?.click()}>
                        <Upload className="mr-2 h-4 w-4" />
                        Upload document
                      </Button>
                    }
                  />
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader
              title="Search test"
              description="Try a query against indexed chunks"
            />
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Input
                  placeholder="e.g. return policy"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && onSearch()}
                  className="flex-1"
                />
                <Button
                  onClick={onSearch}
                  disabled={searching}
                  title="Run search"
                >
                  {searching ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Search className="h-4 w-4" />
                  )}
                </Button>
              </div>
              {searchResults && (
                <div className="space-y-2">
                  <p className="text-2xs font-medium text-muted-foreground">
                    Results
                  </p>
                  {searchResults.length === 0 ? (
                    <p className="text-sm text-muted-foreground">
                      No matches. Try another query or ensure documents are
                      indexed.
                    </p>
                  ) : (
                    <ul className="space-y-2">
                      {searchResults.map((r, i) => (
                        <li
                          key={`${r.documentId}-${r.chunkId}-${i}`}
                          className="rounded-lg border border-border bg-background p-3 text-sm"
                        >
                          <div className="mb-1 flex items-center gap-2 text-2xs text-muted-foreground">
                            <span>Score: {(r.score * 100).toFixed(0)}%</span>
                          </div>
                          <p className="text-white line-clamp-2">{r.snippet}</p>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {chunkPreviewDoc && (() => {
        const doc = getDocumentById(chunkPreviewDoc.id) ?? chunkPreviewDoc;
        return (
          <ChunkPreviewModal
            doc={doc}
            onClose={() => setChunkPreviewDoc(null)}
          />
        );
      })()}
    </>
  );
}
