# Test Documentation

Test suites for the Lattice project:
- **API Tests**: `tests/test_api.py` (14 tests)
- **VirtualFilesystem Tests**: `tests/test_virtual_filesystem.py` (43 tests)

## Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run API tests only
uv run pytest tests/test_api.py -v

# Run VirtualFilesystem tests only
uv run pytest tests/test_virtual_filesystem.py -v
```


## Test Structure

### API Tests (14 tests)

| Class | Tests | Description |
|-------|-------|-------------|
| `TestHealth` | 1 | Health endpoint |
| `TestThreads` | 7 | Thread CRUD operations |
| `TestStatelessRuns` | 1 | Stateless run execution |
| `TestThreadRuns` | 3 | Thread run execution |
| `TestThreadState` | 2 | Thread state retrieval |


### VirtualFilesystem Tests (43 tests)

| Class | Tests | Description |
|-------|-------|-------------|
| `TestResolve` | 4 | Path resolution |
| `TestInfo` | 4 | File/directory metadata |
| `TestLs` | 4 | Directory listing |
| `TestWrite` | 6 | File writing and creation |
| `TestMkdir` | 3 | Directory creation |
| `TestRead` | 7 | File reading with ranges |
| `TestGlob` | 3 | Glob pattern matching |
| `TestGrep` | 12 | Regex search in files |


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

### `vfs`
Fresh `VirtualFilesystem` instance for each test.


## Adding Tests

```python
# API test example
class TestNewFeature:
    def test_something(self, client, mock_agent_service):
        r = client.post("/new-endpoint", json={...})
        assert r.status_code == 200

# VirtualFilesystem test example
class TestNewMethod:
    def test_something(self, vfs):
        vfs.write("/file.txt", "content")
        result = vfs.read("/file.txt")
        assert result["content"] == "content"
```
