# Lattice API Roadmap

Development phases for the LangGraph-compatible API, focused on a **literature survey agent** for single-user use.

---

## Phase 1: Core API ✅ (Completed)

**Goal**: Basic run execution and thread management.

| Endpoint | Method | Status |
|----------|--------|--------|
| `/health` | GET | ✅ |
| `/runs/wait` | POST | ✅ |
| `/threads` | POST | ✅ |
| `/threads/{id}` | GET | ✅ |
| `/threads/{id}` | DELETE | ✅ |
| `/threads/{id}/state` | GET | ✅ |
| `/threads/{id}/runs/wait` | POST | ✅ |

---

## Phase 1.5: Tool Calls + HITL

**Goal**: Enable research tools (paper search, databases) and human review points.

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/threads/{id}/state` | POST | Update state / resume from interrupt |

### Features

**Tool Calls**
```python
# agent calls search_papers tool
{"role": "assistant", "tool_calls": [
    {"id": "call_1", "type": "function", 
     "function": {"name": "search_papers", "arguments": "{\"query\": \"...\"}"}}
]}

# client returns results
{"role": "tool", "tool_call_id": "call_1", "content": "[paper results]"}
```

**Human-in-the-Loop**
```python
# run with interrupt before summarization
POST /threads/{id}/runs/wait
{"interrupt_before": ["summarize_papers"]}

# agent pauses, user reviews papers, then resumes
POST /threads/{id}/state
{"values": {"approved_papers": ["paper1", "paper2"]}}
```

### Tasks
- [ ] Add `interrupt_before/after` to run schemas
- [ ] Create `POST /threads/{id}/state` endpoint
- [ ] Handle tool call messages in conversion
- [ ] Add `tasks` and `interrupts` to ThreadState

---

## Phase 2: Streaming

**Goal**: Real-time feedback during long research operations.

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/runs/stream` | POST | Stateless streaming run |
| `/threads/{id}/runs/stream` | POST | Thread streaming run |

### Stream Events

| Event | Description |
|-------|-------------|
| `metadata` | Run ID, start time |
| `messages/partial` | Token-by-token generation |
| `messages/complete` | Full message |
| `values` | State updates |
| `done` | Stream complete |

### Implementation

```python
from sse_starlette.sse import EventSourceResponse

@router.post("/runs/stream")
async def stream_run(request: RunCreateStateless):
    async def generate():
        async for event in agent.astream_events(...):
            yield {"event": event["event"], "data": json.dumps(event["data"])}
    return EventSourceResponse(generate())
```

### Tasks
- [ ] Create `/runs/stream` endpoint
- [ ] Create `/threads/{id}/runs/stream` endpoint
- [ ] Implement SSE event generator
- [ ] Add streaming tests

---

## Phase 3: Store + Vector Store

**Goal**: Persistent storage for papers, notes, and semantic search.

### Infrastructure Mapping

| Component | MVP (Local) | Production |
|-----------|-------------|------------|
| KV Store | In-memory dict | Neon (Postgres) |
| Vector Store | Qdrant (local/Docker) | Qdrant Cloud |
| Queue | `asyncio.Queue` | Upstash (Redis) |
| Artifacts | Local files | Cloudflare R2 |

### Store Endpoints (KV)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/store/items` | PUT | Store/update item |
| `/store/items` | GET | Get item by key |
| `/store/items` | DELETE | Delete item |
| `/store/items/search` | POST | Search items by filter |
| `/store/namespaces` | POST | List namespaces |

### Vector Store Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/vectors/upsert` | POST | Add/update embeddings |
| `/vectors/search` | POST | Semantic similarity search |
| `/vectors/delete` | DELETE | Remove embeddings |

### Use Cases for Literature Survey

| Storage | Namespace/Collection | Content |
|---------|---------------------|---------|
| KV Store | `papers` | Metadata, DOI, notes |
| KV Store | `summaries` | Generated summaries |
| KV Store | `bookmarks` | Reading list |
| Vector | `paper_abstracts` | Abstract embeddings |
| Vector | `paper_chunks` | Full-text chunks |

### Schema

```python
# KV Store
class StoreItem(BaseModel):
    namespace: List[str]  # ["papers", "physics"]
    key: str              # "doi:10.1234/abc"
    value: dict
    created_at: datetime
    updated_at: datetime

# Vector Store
class VectorUpsertRequest(BaseModel):
    collection: str       # "paper_abstracts"
    vectors: List[dict]   # [{"id": "...", "embedding": [...], "metadata": {...}}]

class VectorSearchRequest(BaseModel):
    collection: str
    query_embedding: List[float]
    top_k: int = 10
    filter: Optional[dict] = None
```

### Tasks
- [ ] Create `src/services/kv_store.py` (dict → Postgres)
- [ ] Create `src/services/vector_store.py` (Qdrant client)
- [ ] Create `/store/items` CRUD endpoints
- [ ] Create `/vectors/*` endpoints
- [ ] Add store/vector schemas

---

## Phase 4: Thread History + Checkpoints

**Goal**: Time-travel through research sessions.

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/threads/{id}/history` | GET | List state history |
| `/threads/{id}/state/{checkpoint_id}` | GET | Get state at checkpoint |

### Tasks
- [ ] Create history endpoint
- [ ] Create checkpoint retrieval endpoint

---

## Phase 5: Background Runs + Artifacts

**Goal**: Long-running tasks and file storage.

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/threads/{id}/runs` | POST | Create background run |
| `/threads/{id}/runs` | GET | List runs |
| `/threads/{id}/runs/{run_id}` | GET | Get run status |
| `/threads/{id}/runs/{run_id}` | DELETE | Cancel run |
| `/artifacts` | POST | Upload artifact |
| `/artifacts/{id}` | GET | Download artifact |

### Artifacts Use Cases
- PDF papers
- Generated reports
- Export summaries

### Tasks
- [ ] Create background run endpoints
- [ ] Create `src/services/artifact_store.py` (local → R2)
- [ ] Create artifact upload/download endpoints

---

## Not Planned (Single-User Scope)

| Feature | Reason |
|---------|--------|
| Multi-Assistant CRUD | Single agent |
| Crons | No scheduled tasks |
| A2A/MCP Protocols | No external integrations |
| Thread Search/Count | Few threads |
| Authentication | Single user |

---

## Infrastructure Evolution

| Phase | Threads | KV Store | Vectors | Queue | Artifacts |
|-------|---------|----------|---------|-------|-----------|
| 1-2 | MemorySaver | - | - | - | - |
| 3 | MemorySaver | dict | Qdrant local | - | - |
| 4-5 | MemorySaver | dict | Qdrant local | asyncio | local files |
| Prod | Neon | Neon | Qdrant Cloud | Upstash | R2 |
