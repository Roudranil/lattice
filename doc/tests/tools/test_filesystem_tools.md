# Filesystem Tools Tests

Test suite for LangChain filesystem tools located in `tests/tools/test_filesystem_tools.py`.

## Test Classes

| Class | Tests | Description |
|-------|-------|-------------|
| `TestToolCreation` | 3 | Factory function |
| `TestFSResponse` | 2 | Response structure |
| `TestFsInfo` | 3 | Info tool |
| `TestFsLs` | 2 | Ls tool |
| `TestFsWrite` | 4 | Write tool |
| `TestFsMkdir` | 2 | Mkdir tool |
| `TestFsRead` | 3 | Read tool |
| `TestFsGlob` | 2 | Glob tool |
| `TestFsGrep` | 5 | Grep tool |

**Total: 26 tests**

## Test Details

### TestToolCreation

| Test | Verifies |
|------|----------|
| `test_creates_seven_tools` | Factory returns 7 tools |
| `test_all_tools_have_names` | All tools properly named |
| `test_tools_have_descriptions` | Docstrings as descriptions |

### TestFSResponse

| Test | Verifies |
|------|----------|
| `test_success_response_structure` | `{status: "ok", error: null, response: ...}` |
| `test_error_response_structure` | `{status: "error", error: str, response: null}` |

### TestFsInfo

| Test | Verifies |
|------|----------|
| `test_info_file` | File metadata returned |
| `test_info_directory` | Directory metadata returned |
| `test_info_nonexistent` | Error for missing path |

### TestFsLs

| Test | Verifies |
|------|----------|
| `test_ls_empty_directory` | Empty list returned |
| `test_ls_with_items` | All items listed |

### TestFsWrite

| Test | Verifies |
|------|----------|
| `test_write_creates_file` | New file created |
| `test_write_overwrite` | Content replaced |
| `test_write_append` | Content appended |
| `test_write_none_creates_empty` | Empty file created |

### TestFsMkdir

| Test | Verifies |
|------|----------|
| `test_mkdir_creates_directory` | Directory created |
| `test_mkdir_nested` | Nested dirs created |

### TestFsRead

| Test | Verifies |
|------|----------|
| `test_read_entire_file` | Full content returned |
| `test_read_line_range` | Line range works |
| `test_read_nonexistent` | Error for missing file |

### TestFsGlob

| Test | Verifies |
|------|----------|
| `test_glob_matches` | Pattern matches |
| `test_glob_no_matches` | Empty for no matches |

### TestFsGrep

| Test | Verifies |
|------|----------|
| `test_grep_finds_match` | Pattern found |
| `test_grep_no_match` | Empty for no matches |
| `test_grep_ignore_case` | Case insensitive |
| `test_grep_directory` | Directory search |
| `test_grep_line_window` | Context lines |

## Fixtures

### `vfs`
Fresh `VirtualFilesystem` instance.

### `tools`
List of LangChain tools bound to vfs.

### `get_tool`
Helper function to retrieve tool by name.
