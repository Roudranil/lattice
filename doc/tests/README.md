# Test Documentation

This folder documents the test suites for the Lattice project.

## Test Structure

```
tests/
├── conftest.py              # Shared pytest fixtures
├── test_api.py              # API endpoint tests
├── backends/
│   └── test_virtual_filesystem.py  # VirtualFilesystem class tests
└── tools/
    └── test_filesystem_tools.py    # LangChain tool wrapper tests
```

## Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_api.py -v
uv run pytest tests/backends/test_virtual_filesystem.py -v
uv run pytest tests/tools/test_filesystem_tools.py -v
```

## Test Coverage Summary

| Module | Tests | File |
|--------|-------|------|
| API | 14 | [test_api.md](./test_api.md) |
| VirtualFilesystem | 43 | [backends/test_virtual_filesystem.md](./backends/test_virtual_filesystem.md) |
| Filesystem Tools | 26 | [tools/test_filesystem_tools.md](./tools/test_filesystem_tools.md) |

**Total: 83 tests**
