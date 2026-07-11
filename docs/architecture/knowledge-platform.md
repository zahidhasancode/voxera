# Knowledge Platform Architecture

VOXERA's knowledge platform ingests tenant documents, chunks and embeds them, and stores vectors for low-latency retrieval with strict tenant isolation.

## Pipeline

```
Upload → Validation → Parse → Clean → Chunk → Metadata → Embed → Vector Store → READY
```

Background ingestion jobs are persisted in `knowledge_ingestion_jobs` and processed by `PersistentIngestionWorker`, which opens an isolated database session per job.

## Provider abstraction

Configuration selects implementations — nothing is hardcoded.

| Layer | Config key | Supported values |
|-------|------------|------------------|
| Embeddings | `KNOWLEDGE_DEFAULT_EMBEDDING_PROVIDER` | `openai`, `voyageai`, `nomic`, `azure_openai`, `bge` |
| Vector store | `KNOWLEDGE_DEFAULT_VECTOR_STORE` | `pgvector`, `qdrant`, `pinecone`, `weaviate`, `milvus` |

Registry: `app/infrastructure/knowledge/registry.py`

Startup validation (`validate_knowledge_platform`) runs during application lifespan when `DATABASE_URL` is set. Set `KNOWLEDGE_REQUIRE_PROVIDERS=true` (or deploy to production) to fail fast on misconfiguration.

## Document parsers

| Type | Parser |
|------|--------|
| TXT, MD | Plain text |
| PDF | pypdf |
| DOCX | python-docx |
| CSV FAQ | csv |
| HTML | BeautifulSoup |
| Website | httpx + BeautifulSoup |
| Confluence, Notion, Drive, SharePoint | Explicit unsupported (clear error) |

## Background jobs

Job states: `queued`, `running`, `completed`, `failed`, `retrying`, `cancelled`.

API: `GET /api/v1/tenants/{tenant_id}/knowledge/jobs/{job_id}`

## Security

- Tenant-scoped namespaces: `tenant-{tenant_id}-source-{source_id}`
- Upload validation: size, extension, magic bytes, path traversal, duplicate SHA-256 hash
- HTML/script pattern scanning on text uploads
- Cross-tenant retrieval blocked at repository and vector metadata filter layers

## Operations

### Enable production providers

```bash
KNOWLEDGE_REQUIRE_PROVIDERS=true
KNOWLEDGE_DEFAULT_EMBEDDING_PROVIDER=openai
KNOWLEDGE_DEFAULT_VECTOR_STORE=pgvector
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql+asyncpg://...
```

### Run migration

```bash
alembic upgrade head
```

Migration `009_knowledge_production` creates:

- `knowledge_vectors` — pgvector-compatible JSONB storage
- `knowledge_ingestion_jobs` — durable job tracking
- Indexes on `knowledge_chunks (tenant_id, source_id)` and `knowledge_sources.file_hash`

### Monitor

Structured logs emit events:

- `knowledge_ingestion_job_queued`
- `knowledge_processing_stage_*`
- `knowledge_vector_insert_started`
- `knowledge_processing_completed`

## Future workers

`PersistentIngestionWorker` implements `BackgroundIngestionProcessor`. The interface supports swapping to Celery, ARQ, RQ, SQS, or Redis Queue without changing domain code.

## Related guides

- Provider credentials: `.env.example`
- Embedding HTTP client: `app/infrastructure/knowledge/embeddings/http_embedding.py`
- Vector stores: `app/infrastructure/knowledge/vector_stores/`
