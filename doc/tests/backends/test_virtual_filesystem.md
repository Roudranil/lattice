# VirtualFilesystem Tests

Test suite for the VirtualFilesystem class located in `tests/backends/test_virtual_filesystem.py`.

## Test Classes

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

**Total: 43 tests**

## Test Details

### TestResolve

| Test | Verifies |
|------|----------|
| `test_resolve_absolute_path` | Absolute paths normalized unchanged |
| `test_resolve_absolute_path_with_dots` | Paths with `..` normalized |
| `test_resolve_relative_path` | Relative paths joined with cwd |
| `test_resolve_relative_path_with_dots` | Relative `..` resolved correctly |

### TestInfo

| Test | Verifies |
|------|----------|
| `test_info_root_directory` | Root directory exists |
| `test_info_created_file` | File info returned |
| `test_info_created_directory` | Directory info returned |
| `test_info_nonexistent_raises` | FSError for missing path |

### TestLs

| Test | Verifies |
|------|----------|
| `test_ls_empty_directory` | Empty list for empty dir |
| `test_ls_with_files` | All items listed |
| `test_ls_with_subdirectory` | Subdirs included |
| `test_ls_nonexistent_raises` | FSError for missing dir |

### TestWrite

| Test | Verifies |
|------|----------|
| `test_write_creates_new_file` | Creates new file |
| `test_write_overwrite_mode` | Replaces content |
| `test_write_append_mode` | Appends content |
| `test_write_none_content_creates_empty_file` | None creates empty |
| `test_write_none_content_existing_file_unchanged` | None preserves existing |
| `test_write_append_to_nonexistent_creates_file` | Append creates file first |

### TestMkdir

| Test | Verifies |
|------|----------|
| `test_mkdir_creates_directory` | Creates directory |
| `test_mkdir_creates_nested_directories` | Creates parent dirs |
| `test_mkdir_existing_raises` | FSError for existing |

### TestRead

| Test | Verifies |
|------|----------|
| `test_read_entire_file` | Full content returned |
| `test_read_line_range` | Slice semantics work |
| `test_read_start_only` | Start to end of file |
| `test_read_negative_start_clamped` | Negative clamped to 0 |
| `test_read_end_beyond_file_clamped` | End clamped to length |
| `test_read_includes_info` | File info in result |
| `test_read_nonexistent_raises` | FSError for missing |

### TestGlob

| Test | Verifies |
|------|----------|
| `test_glob_star_pattern` | `*` pattern matches |
| `test_glob_no_matches` | Empty list for no matches |
| `test_glob_in_subdirectory` | Subdir patterns work |

### TestGrep

| Test | Verifies |
|------|----------|
| `test_grep_simple_match` | Finds text |
| `test_grep_multiple_matches` | Multiple matches found |
| `test_grep_no_matches` | Empty for no matches |
| `test_grep_ignore_case` | Case insensitive works |
| `test_grep_case_sensitive_default` | Default case sensitive |
| `test_grep_regex_pattern` | Regex patterns work |
| `test_grep_line_window` | Line context included |
| `test_grep_character_window` | Char context included |
| `test_grep_directory_recursive` | Recursive dir search |
| `test_grep_directory_with_file_pattern` | File pattern filter |
| `test_grep_file_ignores_file_pattern` | Pattern ignored for file |
| `test_grep_match_range` | Match position returned |

## Fixtures

### `vfs`
Fresh `VirtualFilesystem` instance for each test.
