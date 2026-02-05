# Lattice API

LangGraph-compatible REST API for the Lattice agent.

## Quick Start

```bash
uv run uvicorn src.api.app:app --reload --port 8000
```

- **OpenAPI UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Documentation

| File | Description |
|------|-------------|
| [openapi.json](openapi.json) | OpenAPI 3.1 spec (auto-generated) |
| [usage.md](usage.md) | Python usage examples |
| [tests.md](tests.md) | Test suite documentation |

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/runs/wait` | Stateless run |
| POST | `/threads` | Create thread |
| GET | `/threads/{id}` | Get thread |
| DELETE | `/threads/{id}` | Delete thread |
| GET | `/threads/{id}/state` | Get thread state |
| POST | `/threads/{id}/runs/wait` | Run on thread |
