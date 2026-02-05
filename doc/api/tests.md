# API Test Documentation

Test suite for the Lattice API located in `tests/test_api.py`.

## Running Tests

```bash
uv run pytest tests/test_api.py -v
```


## Test Structure

| Class | Tests | Description |
|-------|-------|-------------|
| `TestHealth` | 1 | Health endpoint |
| `TestThreads` | 7 | Thread CRUD operations |
| `TestStatelessRuns` | 1 | Stateless run execution |
| `TestThreadRuns` | 3 | Thread run execution |
| `TestThreadState` | 2 | Thread state retrieval |

**Total: 14 tests**


## Test Details

### TestHealth

| Test | Verifies |
|------|----------|
| `test_health_returns_ok` | `/health` returns `{"status": "ok"}` |

### TestThreads

| Test | Verifies |
|------|----------|
| `test_create_thread_with_defaults` | Creates thread with auto-generated UUID |
| `test_create_thread_with_custom_id` | Respects custom `thread_id` |
| `test_create_thread_with_metadata` | Stores metadata correctly |
| `test_get_thread` | Retrieves existing thread |
| `test_get_thread_not_found` | Returns 404 for missing thread |
| `test_delete_thread` | Deletes thread and confirms removal |
| `test_delete_thread_not_found` | Returns 404 for missing thread |

### TestStatelessRuns

| Test | Verifies |
|------|----------|
| `test_stateless_run` | Executes run without thread |

### TestThreadRuns

| Test | Verifies |
|------|----------|
| `test_run_on_thread` | Executes run on existing thread |
| `test_run_on_nonexistent_thread` | Returns 404 for missing thread |
| `test_run_updates_thread_status` | Status changes during run |

### TestThreadState

| Test | Verifies |
|------|----------|
| `test_get_thread_state` | Returns state with values and next |
| `test_get_state_thread_not_found` | Returns 404 for missing thread |


## Fixtures

### `client`
FastAPI `TestClient` instance. Resets stores between tests.

### `mock_agent_service`
Mocks `invoke_agent` and `get_thread_state` to avoid:
- Loading `main.py` (requires env vars)
- Making real API calls
- Non-deterministic tests


## Adding Tests

```python
class TestNewFeature:
    def test_something(self, client, mock_agent_service):
        r = client.post("/new-endpoint", json={...})
        assert r.status_code == 200
```
