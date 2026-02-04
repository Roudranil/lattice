# LangGraph API -> Minimal Runtime Mapping Reference

- [LangGraph API -\> Minimal Runtime Mapping Reference](#langgraph-api---minimal-runtime-mapping-reference)
  - [CORE LANGGRAPH RESOURCE MODEL](#core-langgraph-resource-model)
    - [Assistant](#assistant)
    - [Thread](#thread)
    - [Run](#run)
    - [State / Checkpoint](#state--checkpoint)
    - [Store (Cross-thread memory)](#store-cross-thread-memory)
  - [FULL LANGGRAPH PLATFORM ENDPOINT SURFACE](#full-langgraph-platform-endpoint-surface)
    - [ASSISTANTS](#assistants)
    - [THREADS](#threads)
    - [RUNS - STATEFUL](#runs---stateful)
    - [RUNS - STATELESS](#runs---stateless)
    - [STREAM JOIN / RECONNECT](#stream-join--reconnect)
    - [CRON / SCHEDULING](#cron--scheduling)
    - [STORE / MEMORY](#store--memory)
    - [MCP EXPOSURE](#mcp-exposure)
  - [MINIMUM ENDPOINTS REQUIRED FOR CUSTOM FASTAPI](#minimum-endpoints-required-for-custom-fastapi)
    - [THREAD MANAGEMENT](#thread-management)
    - [RUN EXECUTION](#run-execution)
    - [RUN MANAGEMENT](#run-management)
    - [INTERRUPT RESUME](#interrupt-resume)
    - [OPENAI COMPATIBILITY LAYER](#openai-compatibility-layer)
  - [REQUIRED FUNCTIONAL CAPABILITIES](#required-functional-capabilities)
  - [INTERNAL COMPONENTS REQUIRED](#internal-components-required)
    - [HTTP Layer](#http-layer)
    - [Executor Service](#executor-service)
    - [Streaming Manager](#streaming-manager)
    - [Interrupt Manager](#interrupt-manager)
    - [Tool Dispatch Manager](#tool-dispatch-manager)
    - [Persistence Layer](#persistence-layer)
  - [DATA MODELS REQUIRED](#data-models-required)
    - [Thread Model](#thread-model)
    - [Run Model](#run-model)
    - [Event Model](#event-model)
    - [Interrupt Model](#interrupt-model)
  - [OPENAI ENDPOINT MAPPING](#openai-endpoint-mapping)
    - [OPENAI -\> LangGraph Execution Mapping](#openai---langgraph-execution-mapping)
    - [OpenAI Streaming Mapping](#openai-streaming-mapping)
    - [OpenAI Tool Calls Mapping](#openai-tool-calls-mapping)
    - [OpenAI Structured Output Mapping](#openai-structured-output-mapping)
    - [OpenAI Conversation Mapping](#openai-conversation-mapping)
  - [DEVELOPMENT ORDER](#development-order)
  - [OPTIONAL FEATURES (NOT REQUIRED)](#optional-features-not-required)
  - [ARCHITECTURAL PRINCIPLE](#architectural-principle)


This document describes:

1. Full LangGraph resource model
2. Full endpoint families (from LangGraph platform)
3. Minimal subset required for custom FastAPI runtime
4. Internal component requirements
5. OpenAI endpoint mapping to LangGraph runtime

## CORE LANGGRAPH RESOURCE MODEL

LangGraph runtime is built around several core resources:

### Assistant
Represents a configured agent graph.

Fields:
- assistant_id
- graph_id
- configuration
- metadata
- versioning

Lifecycle:
Persistent + versioned

### Thread
Represents a persistent execution context (conversation / state container).

Fields:
- thread_id
- metadata
- checkpoint state
- status (idle, busy, interrupted, error)

Lifecycle:
Persistent until deleted

### Run
Represents one graph execution.

Fields:
- run_id
- thread_id (optional)
- assistant_id (optional)
- input payload
- status
- event logs
- interrupt state
- timestamps

Lifecycle:
Transient or persisted

### State / Checkpoint
Represents snapshot of graph execution.

Fields:
- checkpoint_id
- thread_id
- state values
- node execution progress

Lifecycle:
Versioned within thread

### Store (Cross-thread memory)
Key-value namespace memory.

Fields:
- namespace
- key
- value


## FULL LANGGRAPH PLATFORM ENDPOINT SURFACE


### ASSISTANTS

```
POST   /assistants
GET    /assistants
GET    /assistants/{assistant_id}
POST   /assistants/search
PATCH  /assistants/{assistant_id}
DELETE /assistants/{assistant_id}
```

### THREADS

```
POST   /threads
POST   /threads/search
POST   /threads/count
GET    /threads/{thread_id}
PATCH  /threads/{thread_id}
DELETE /threads/{thread_id}
POST   /threads/{thread_id}/copy
```

### RUNS - STATEFUL

```
POST   /threads/{thread_id}/runs
POST   /threads/{thread_id}/runs/wait
POST   /threads/{thread_id}/runs/stream
GET    /threads/{thread_id}/runs
GET    /threads/{thread_id}/runs/{run_id}
DELETE /threads/{thread_id}/runs/{run_id}
POST   /threads/{thread_id}/runs/{run_id}/cancel
```

### RUNS - STATELESS
```
POST   /runs
POST   /runs/wait
POST   /runs/stream
POST   /runs/batch
```
### STREAM JOIN / RECONNECT
```
GET    /threads/{thread_id}/runs/{run_id}/stream
GET    /threads/{thread_id}/runs/{run_id}/join
```

### CRON / SCHEDULING
```
POST   /threads/{thread_id}/runs/crons
POST   /runs/crons
```

### STORE / MEMORY
```
GET    /store/{namespace}/{key}
POST   /store/{namespace}/{key}
DELETE /store/{namespace}/{key}
```

### MCP EXPOSURE
```
GET    /mcp
POST   /mcp
```

## MINIMUM ENDPOINTS REQUIRED FOR CUSTOM FASTAPI

### THREAD MANAGEMENT
```
POST   /v1/threads
GET    /v1/threads/{thread_id}
```
### RUN EXECUTION
```
POST   /v1/threads/{thread_id}/runs
POST   /v1/threads/{thread_id}/runs/stream
POST   /v1/runs
POST   /v1/runs/stream
```
### RUN MANAGEMENT
```
GET    /v1/runs/{run_id}
GET    /v1/runs/{run_id}/stream
```
### INTERRUPT RESUME
```
POST   /v1/threads/{thread_id}/resume
```
### OPENAI COMPATIBILITY LAYER
```
POST   /v1/chat/completions
POST   /v1/responses
```

## REQUIRED FUNCTIONAL CAPABILITIES

THREAD FEATURES
- Persistent state storage
- Metadata support
- Checkpoint restoration

RUN FEATURES
- Stateful execution
- Stateless execution
- Background execution
- Multitask control

STREAMING FEATURES
- Server Sent Events transport
- Token streaming
- Tool call events
- Lifecycle events
- Interrupt events
- Final completion events
- Stream reconnection support

INTERRUPT FEATURES
- Detect "input_required" state
- Resume execution using:
    - thread_id
    - run_id or task_id
    - user input payload

STRUCTURED OUTPUT FEATURES
- JSON schema validation
- Schema-bound model output

TOOL EXECUTION FEATURES
- Tool call event emission
- Tool result injection back into executor


## INTERNAL COMPONENTS REQUIRED

### HTTP Layer
Handles request validation and OpenAPI schema.

### Executor Service
Wraps LangGraph runtime.

Interface:
```python
run(thread_id, input)
stream(thread_id, input)
resume(thread_id, task_id, input)
get_status(run_id)
```
### Streaming Manager
Handles SSE transport.
Maintains event cursor tracking.

### Interrupt Manager
Tracks paused runs.
Routes resume requests.

### Tool Dispatch Manager
Executes external tools.
Returns tool results.

### Persistence Layer
Repositories for:

Thread Repository
Run Repository
Checkpoint Repository
Event Log Repository


## DATA MODELS REQUIRED

### Thread Model
- thread_id
- metadata
- state_snapshot
- last_run_id
- status

### Run Model
- run_id
- thread_id
- assistant_id
- input
- status
- event_log_reference
- interrupt_state
- timestamps

### Event Model
- event_id
- run_id
- event_type
- payload
- timestamp

### Interrupt Model
- task_id
- run_id
- thread_id
- expected_input_schema
- resume_state_pointer


## OPENAI ENDPOINT MAPPING

### OPENAI -> LangGraph Execution Mapping

POST /v1/chat/completions
Maps To:

1. Normalize messages -> LangGraph input format
2. Create thread if missing
3. Call:
```    
    /threads/{thread_id}/runs OR
    /threads/{thread_id}/runs/stream
```
4. Convert LangGraph events -> OpenAI response schema

POST /v1/responses

Maps To:

1. Same as chat completions but supports:

- multi-modal payloads
- structured output schema
- tool definitions
- response aggregation

### OpenAI Streaming Mapping

OpenAI stream chunk:
-> token events
-> tool call events
-> completion events

Mapped From:
LangGraph SSE event stream

### OpenAI Tool Calls Mapping

OpenAI:
"tool_calls"

LangGraph:
Tool invocation events emitted from graph nodes.

### OpenAI Structured Output Mapping

OpenAI:
response_format / JSON schema

LangGraph:
Schema enforcement in executor
Return validated JSON object

### OpenAI Conversation Mapping

OpenAI message list:
-> thread state
-> checkpoint memory


## DEVELOPMENT ORDER

Phase 1
Thread creation + synchronous runs

Phase 2
Streaming SSE execution

Phase 3
OpenAI compatibility wrapper

Phase 4
Interrupt resume support

Phase 5
Streaming reconnection support


## OPTIONAL FEATURES (NOT REQUIRED)

Assistants management
Cron scheduling
MCP server exposure
Batch runs
Store API
Enterprise observability


## ARCHITECTURAL PRINCIPLE

The FastAPI runtime should act as:

Transport Layer
+ Execution Orchestrator
+ Event Router
+ State Persistence Coordinator

LangGraph remains the execution engine.

