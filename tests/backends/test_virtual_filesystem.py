"""
pytest test suite for VirtualFilesystem

Tests the in-memory virtual filesystem implementation including file operations,
directory operations, pattern matching, and text search.

Run with: uv run pytest tests/test_virtual_filesystem.py -v
"""

import pytest

from src.backends.virtual_filesystem import VirtualFilesystem


@pytest.fixture
def vfs():
    """Create a fresh VirtualFilesystem instance for each test."""
    return VirtualFilesystem()


class TestResolve:
    """Tests for path resolution."""

    def test_resolve_absolute_path(self, vfs):
        """Absolute paths are normalized but unchanged."""
        assert vfs._resolve("/foo/bar") == "/foo/bar"

    def test_resolve_absolute_path_with_dots(self, vfs):
        """Absolute paths with .. are normalized."""
        assert vfs._resolve("/foo/bar/../baz") == "/foo/baz"

    def test_resolve_relative_path(self, vfs):
        """Relative paths are joined with cwd."""
        vfs.cwd = "/home"
        assert vfs._resolve("foo/bar") == "/home/foo/bar"

    def test_resolve_relative_path_with_dots(self, vfs):
        """Relative paths with .. are resolved correctly."""
        vfs.cwd = "/home/user"
        assert vfs._resolve("../foo") == "/home/foo"


class TestInfo:
    """Tests for file/directory info retrieval."""

    def test_info_root_directory(self, vfs):
        """Root directory exists by default."""
        info = vfs.info("/")
        assert info["name"] == ""
        assert info["type"] == "directory"
        assert info["path"] == "/"

    def test_info_created_file(self, vfs):
        """Info for a created file."""
        vfs.write("/test.txt", "content")
        info = vfs.info("/test.txt")
        assert info["name"] == "test.txt"
        assert info["type"] == "file"
        assert info["path"] == "/test.txt"

    def test_info_created_directory(self, vfs):
        """Info for a created directory."""
        vfs.mkdir("/mydir")
        info = vfs.info("/mydir")
        assert info["name"] == "mydir"
        assert info["type"] == "directory"

    def test_info_nonexistent_raises(self, vfs):
        """FSError raised for nonexistent path."""
        with pytest.raises(Exception):
            vfs.info("/nonexistent")


class TestLs:
    """Tests for directory listing."""

    def test_ls_empty_directory(self, vfs):
        """Empty directory returns empty list."""
        result = vfs.ls("/")
        assert result == []

    def test_ls_with_files(self, vfs):
        """Directory with files returns all items."""
        vfs.write("/a.txt", "a")
        vfs.write("/b.txt", "b")
        result = vfs.ls("/")
        names = [item["name"] for item in result]
        assert "a.txt" in names
        assert "b.txt" in names
        assert len(result) == 2

    def test_ls_with_subdirectory(self, vfs):
        """Subdirectories are included in listing."""
        vfs.mkdir("/subdir")
        vfs.write("/file.txt", "content")
        result = vfs.ls("/")
        types = {item["name"]: item["type"] for item in result}
        assert types["subdir"] == "directory"
        assert types["file.txt"] == "file"

    def test_ls_nonexistent_raises(self, vfs):
        """FSError raised for nonexistent directory."""
        with pytest.raises(Exception):
            vfs.ls("/nonexistent")


class TestWrite:
    """Tests for file writing."""

    def test_write_creates_new_file(self, vfs):
        """Writing creates a new file."""
        vfs.write("/new.txt", "hello")
        content = vfs.read("/new.txt")["content"]
        assert content == "hello"

    def test_write_overwrite_mode(self, vfs):
        """Overwrite mode replaces content."""
        vfs.write("/file.txt", "first")
        vfs.write("/file.txt", "second", mode="overwrite")
        content = vfs.read("/file.txt")["content"]
        assert content == "second"

    def test_write_append_mode(self, vfs):
        """Append mode adds to existing content."""
        vfs.write("/file.txt", "hello")
        vfs.write("/file.txt", " world", mode="append")
        content = vfs.read("/file.txt")["content"]
        assert content == "hello world"

    def test_write_none_content_creates_empty_file(self, vfs):
        """None content creates empty file."""
        vfs.write("/empty.txt")
        info = vfs.info("/empty.txt")
        assert info["type"] == "file"

    def test_write_none_content_existing_file_unchanged(self, vfs):
        """None content on existing file leaves it unchanged."""
        vfs.write("/file.txt", "original content")
        vfs.write("/file.txt", None)  # Should not modify
        content = vfs.read("/file.txt")["content"]
        assert content == "original content"

    def test_write_append_to_nonexistent_creates_file(self, vfs):
        """Append to nonexistent file creates it first."""
        vfs.write("/new.txt", "content", mode="append")
        content = vfs.read("/new.txt")["content"]
        assert content == "content"


class TestMkdir:
    """Tests for directory creation."""

    def test_mkdir_creates_directory(self, vfs):
        """Creates a single directory."""
        vfs.mkdir("/mydir")
        info = vfs.info("/mydir")
        assert info["type"] == "directory"

    def test_mkdir_creates_nested_directories(self, vfs):
        """Creates nested directories."""
        vfs.mkdir("/a/b/c")
        info = vfs.info("/a/b/c")
        assert info["type"] == "directory"

    def test_mkdir_existing_raises(self, vfs):
        """FSError raised when directory exists."""
        vfs.mkdir("/mydir")
        with pytest.raises(Exception):
            vfs.mkdir("/mydir")


class TestRead:
    """Tests for file reading."""

    def test_read_entire_file(self, vfs):
        """Read entire file when no range specified."""
        vfs.write("/file.txt", "line1\nline2\nline3")
        result = vfs.read("/file.txt")
        assert result["content"] == "line1\nline2\nline3"
        assert result["start"] == 0
        assert result["end"] == 3

    def test_read_line_range(self, vfs):
        """Read specific line range (0-indexed)."""
        vfs.write("/file.txt", "line0\nline1\nline2\nline3")
        result = vfs.read("/file.txt", start=1, end=3)
        assert result["content"] == "line1\nline2"
        assert result["start"] == 1
        assert result["end"] == 3

    def test_read_start_only(self, vfs):
        """Read from start to end of file."""
        vfs.write("/file.txt", "line0\nline1\nline2")
        result = vfs.read("/file.txt", start=1)
        assert result["content"] == "line1\nline2"

    def test_read_negative_start_clamped(self, vfs):
        """Negative start is clamped to 0."""
        vfs.write("/file.txt", "line0\nline1")
        result = vfs.read("/file.txt", start=-5, end=1)
        assert result["start"] == 0

    def test_read_end_beyond_file_clamped(self, vfs):
        """End beyond file is clamped to file length."""
        vfs.write("/file.txt", "line0\nline1")
        result = vfs.read("/file.txt", start=0, end=100)
        assert result["end"] == 2

    def test_read_includes_info(self, vfs):
        """Result includes file info."""
        vfs.write("/file.txt", "content")
        result = vfs.read("/file.txt")
        assert result["info"]["name"] == "file.txt"
        assert result["info"]["type"] == "file"

    def test_read_nonexistent_raises(self, vfs):
        """FSError raised for nonexistent file."""
        with pytest.raises(Exception):
            vfs.read("/nonexistent.txt")


class TestGlob:
    """Tests for glob pattern matching."""

    def test_glob_star_pattern(self, vfs):
        """Match files with * pattern."""
        vfs.write("/a.txt", "a")
        vfs.write("/b.txt", "b")
        vfs.write("/c.py", "c")
        result = vfs.glob("/*.txt")
        names = [item["name"] for item in result]
        assert "a.txt" in names
        assert "b.txt" in names
        assert "c.py" not in names

    def test_glob_no_matches(self, vfs):
        """No matches returns empty list."""
        vfs.write("/file.txt", "content")
        result = vfs.glob("/*.py")
        assert result == []

    def test_glob_in_subdirectory(self, vfs):
        """Glob in subdirectory."""
        vfs.mkdir("/subdir")
        vfs.write("/subdir/file.txt", "content")
        result = vfs.glob("/subdir/*.txt")
        assert len(result) == 1
        assert result[0]["name"] == "file.txt"


class TestGrep:
    """Tests for regex search."""

    def test_grep_simple_match(self, vfs):
        """Find simple text match."""
        vfs.write("/file.txt", "hello world\ngoodbye world")
        results = vfs.grep("hello", "/file.txt")
        assert len(results) == 1
        assert results[0]["line_number"] == 0
        assert results[0]["snippet"] == "hello world"

    def test_grep_multiple_matches(self, vfs):
        """Find multiple matches in file."""
        vfs.write("/file.txt", "foo bar\nbaz foo\nfoo")
        results = vfs.grep("foo", "/file.txt")
        assert len(results) == 3

    def test_grep_no_matches(self, vfs):
        """No matches returns empty list."""
        vfs.write("/file.txt", "hello world")
        results = vfs.grep("notfound", "/file.txt")
        assert results == []

    def test_grep_ignore_case(self, vfs):
        """Case insensitive matching."""
        vfs.write("/file.txt", "Hello WORLD")
        results = vfs.grep("hello", "/file.txt", ignore_case=True)
        assert len(results) == 1

    def test_grep_case_sensitive_default(self, vfs):
        """Default is case sensitive."""
        vfs.write("/file.txt", "Hello WORLD")
        results = vfs.grep("hello", "/file.txt")
        assert len(results) == 0

    def test_grep_regex_pattern(self, vfs):
        """Regex patterns work."""
        vfs.write("/file.txt", "cat\ncar\ncab\ndog")
        results = vfs.grep(r"ca[rt]", "/file.txt")
        assert len(results) == 2

    def test_grep_line_window(self, vfs):
        """Line window includes context lines."""
        vfs.write("/file.txt", "line0\nline1\nMATCH\nline3\nline4")
        results = vfs.grep("MATCH", "/file.txt", line_window=1)
        assert len(results) == 1
        assert "line1" in results[0]["snippet"]
        assert "MATCH" in results[0]["snippet"]
        assert "line3" in results[0]["snippet"]

    def test_grep_character_window(self, vfs):
        """Character window includes context characters."""
        vfs.write("/file.txt", "aaaaMATCHbbbb")
        results = vfs.grep("MATCH", "/file.txt", character_window=2)
        assert results[0]["snippet"] == "aaMATCHbb"

    def test_grep_directory_recursive(self, vfs):
        """Search recursively in directory."""
        vfs.mkdir("/dir")
        vfs.write("/dir/a.txt", "findme")
        vfs.write("/dir/b.txt", "nothing")
        results = vfs.grep("findme", "/dir")
        assert len(results) == 1
        assert "a.txt" in results[0]["path"]

    def test_grep_directory_with_file_pattern(self, vfs):
        """Filter files by pattern in directory."""
        vfs.mkdir("/dir")
        vfs.write("/dir/a.txt", "match")
        vfs.write("/dir/b.py", "match")
        results = vfs.grep("match", "/dir", file_name_pattern="*.txt")
        assert len(results) == 1
        assert "a.txt" in results[0]["path"]

    def test_grep_file_ignores_file_pattern(self, vfs):
        """file_name_pattern is ignored when path is a file."""
        vfs.write("/file.txt", "match")
        # file_name_pattern would filter this out if it were used
        results = vfs.grep("match", "/file.txt", file_name_pattern="*.py")
        assert len(results) == 1

    def test_grep_match_range(self, vfs):
        """Match range indicates position in line."""
        vfs.write("/file.txt", "hello world")
        results = vfs.grep("world", "/file.txt")
        assert results[0]["match_range"] == [6, 11]
