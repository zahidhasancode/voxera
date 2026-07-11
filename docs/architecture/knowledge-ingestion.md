# Knowledge Base Ingestion Architecture

Enterprise knowledge ingestion for VOXERA — built **alongside** the real-time voice pipeline. Twilio, STT, LLM, and TTS are **not modified**.

## Overview

Tenants upload documents (PDF, DOCX, TXT, Markdown, CSV FAQ, Website URLs) which flow through a multi-stage ingestion pipeline. Parsed content is chunked, optionally embedded, and stored in a tenant-isolated vector namespace for agent retrieval.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         API  /tenants/{id}/knowledge                         │
│  POST /upload   GET /   GET /{id}   DELETE /{id}   POST /reprocess   GET /status │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │ Depends()
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      KnowledgeSourceService (application)                    │
│  upload · list · delete · reprocess · status summary                         │
└───────────────┬───────────────────────────────┬─────────────────────────────┘
                │                               │
                ▼                               ▼
┌───────────────────────────┐     ┌───────────────────────────────────────────┐
│ BackgroundIngestionProcessor│     │ KnowledgeSourceRepository + ChunkRepository │
│ (async task / future Celery)│     │ (SQLAlchemy)                                │
└───────────────┬───────────┘     └───────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         IngestionPipeline (orchestrator)                     │
│                                                                              │
│  Upload ──▶ Parse ──▶ Clean ──▶ Chunk ──▶ Metadata ──▶ Embed ──▶ Vector    │
│                                                                              │
│  ParserRegistry    ChunkingStrategy    EmbeddingProvider*    VectorStore*    │
│  (DocumentParser)  (configurable)      (abstract port)       (abstract port) │
└─────────────────────────────────────────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────┐     ┌────────────────────────────────────────┐
│ PostgreSQL                    │     │ Vector Store (Qdrant / Pinecone / …)   │
│ knowledge_sources             │     │ namespace: tenant-{tid}-source-{sid}   │
│ knowledge_chunks              │     │ (one namespace per source, no sharing) │
└──────────────────────────────┘     └────────────────────────────────────────┘

* Provider implementations registered via DI — not hardcoded in pipeline.
```

## Retrieval Path (agent query time)

```
RetrievalService
    │
    ├─▶ EmbeddingProvider.embed_query(query)
    ├─▶ VectorStore.search(namespace, vector, top_k, min_score, metadata_filter)
    └─▶ KnowledgeChunkRepository.get_by_ids → RetrievalResult
```

## Folder Structure

```
app/knowledge/
├── api/routes.py              # REST endpoints
├── schemas/                   # Pydantic DTOs
│   ├── source.py              # KnowledgeSource + frontend response
│   ├── chunk.py               # Chunk metadata
│   ├── ingestion.py           # Job status, metrics
│   └── retrieval.py           # Query + results
├── repository/                # Persistence ports (ABC)
├── services/                  # Application service ports (ABC)
├── ingestion/
│   ├── pipeline.py            # Stage orchestrator
│   ├── background.py          # BackgroundIngestionProcessor port
│   ├── metrics.py             # ProcessingMetricsCollector
│   └── stages.py              # Progress mapping, text cleaning
├── parser/                    # DocumentParser port + registry
├── chunking/                  # ChunkConfig + ChunkingStrategy
├── embeddings/                # EmbeddingProvider port
└── retrieval/                 # VectorStore port

app/infrastructure/knowledge/
├── storage.py                 # LocalKnowledgeFileStorage
├── parsers/                   # PlainTextDocumentParser, stubs for PDF/DOCX/…
├── background_processor.py    # AsyncInProcessIngestionProcessor
├── providers.py               # DI factory for embedder / vector store
└── unconfigured_providers.py  # Clear errors until wired

app/database/models/knowledge_source.py   # KnowledgeSourceModel, KnowledgeChunkModel
```

## KnowledgeSource Model

| Field | Description |
|-------|-------------|
| `id`, `tenant_id` | Primary key + tenant isolation |
| `title` | Display name |
| `source_type` | pdf, docx, txt, md, csv_faq, website (+ future integrations) |
| `status` | pending → processing → ready / failed / reprocessing |
| `file_path`, `website_url` | Source location |
| `processing_*` | Stage, timestamps, error, progress_pct |
| `chunk_count`, `embedding_count` | Processing outputs |
| `embedding_model`, `embedding_status` | Embedding lifecycle |
| `vector_namespace` | `tenant-{uuid}-source-{uuid}` — never shared |
| `chunk_config` | chunk_size, overlap, separator, maximum_tokens |
| `metadata` | Extensible JSON |

## Chunk Metadata

Each chunk stores: `document`, `page`, `section`, `chunk_number`, `language`, `source`.

## API Endpoints

Base: `/api/v1/tenants/{tenant_id}/knowledge`

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/upload` | Multipart file upload (title, source_type, file) |
| `POST` | `/` | Create from URL (website sources) |
| `GET` | `/` | List sources (frontend-ready response) |
| `GET` | `/status` | Tenant-wide processing summary |
| `GET` | `/{id}` | Single source detail |
| `DELETE` | `/{id}` | Delete source + chunks + vector namespace |
| `POST` | `/reprocess` | Re-run pipeline for failed/selected sources |

## Frontend Response Fields

`KnowledgeSourceFrontendRead` includes:

- `processing_percent` (0–100)
- `chunk_count`, `embedding_status`, `embedding_status_label`
- `file_size_display`, `created_date`
- `is_processing` boolean

## Logging Events

Structured logs at each stage:

- `knowledge_processing_stage_started` / `_completed` / `_failed`
- `knowledge_embedding_started`
- `knowledge_vector_insert_started`
- `knowledge_processing_completed` / `_failed`
- `knowledge_ingestion_job_submitted`

## Metrics

`ProcessingMetricsSnapshot` captures per-document:

- `processing_time_ms`
- `chunk_count`, `embedding_count`
- `average_chunk_size_chars`, `average_chunk_tokens`
- `stage_durations_ms` breakdown

## Tenant Isolation

1. All rows scoped by `tenant_id` (FK + repository filters)
2. Vector namespaces are unique per source: `tenant-{tenant_id}-source-{source_id}`
3. Metadata filter always includes `tenant_id` in retrieval

## Provider Registration (future sprint)

```python
# Example — register OpenAI embedder + Qdrant store in providers.py
def get_embedding_provider() -> EmbeddingProvider:
    return OpenAIEmbeddingProvider(api_key=settings.OPENAI_API_KEY)

def get_vector_store() -> VectorStore:
    return QdrantVectorStore(url=settings.QDRANT_URL)
```

Pipeline code never imports provider SDKs directly.

## Scale Considerations

- Chunk batch inserts (not one row per flush)
- Background processor interface swappable for Celery/ARQ/SQS
- Vector store handles millions of vectors per namespace
- Pagination on list endpoints (default limit 50, max 200)
- File size cap via `KNOWLEDGE_MAX_UPLOAD_BYTES`

## What Was Not Modified

- `app/api/v1/endpoints/websocket.py`
- `app/telephony/twilio_handler.py`
- STT / LLM / TTS consumers and streaming pipeline
