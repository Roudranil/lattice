"""
pytest test suite for filesystem_tools LangChain wrappers.

Tests the LangChain tool functions that wrap VirtualFilesystem operations.
Verifies FSResponse structure and tool behavior.

Run with: uv run pytest tests/tools/test_filesystem_tools.py -v
"""

import pytest

from src.backends.virtual_filesystem import VirtualFilesystem
from src.tools.filesystem_tools import create_filesystem_tools


@pytest.fixture
def vfs():
    """Create a fresh VirtualFilesystem instance for each test."""
    return VirtualFilesystem()


@pytest.fixture
def tools(vfs):
    """Create filesystem tools bound to the vfs instance."""
    return create_filesystem_tools(vfs)


@pytest.fixture
def get_tool(tools):
    """Helper to get a tool by name."""

    def _get(name):
        return next(t for t in tools if t.name == name)

    return _get


class TestToolCreation:
    """Tests for tool factory function."""

    def test_creates_seven_tools(self, tools):
        """Factory creates all 7 tools."""
        assert len(tools) == 7

    def test_all_tools_have_names(self, tools):
        """All tools have proper names."""
        names = [t.name for t in tools]
        assert "fs_info" in names
        assert "fs_ls" in names
        assert "fs_write" in names
        assert "fs_mkdir" in names
        assert "fs_read" in names
        assert "fs_glob" in names
        assert "fs_grep" in names

    def test_tools_have_descriptions(self, tools):
        """All tools have docstring-based descriptions."""
        for tool in tools:
            assert tool.description, f"{tool.name} missing description"


class TestFSResponse:
    """Tests for FSResponse structure in tool outputs."""

    def test_success_response_structure(self, get_tool, vfs):
        """Success responses have correct structure."""
        vfs.write("/test.txt", "content")
        result = get_tool("fs_info").invoke({"path": "/test.txt"})
        assert result["status"] == "ok"
        assert result["error"] is None
        assert result["response"] is not None

    def test_error_response_structure(self, get_tool):
        """Error responses have correct structure."""
        result = get_tool("fs_read").invoke({"path": "/nonexistent.txt"})
        assert result["status"] == "error"
        assert result["error"] is not None
        assert result["response"] is None


class TestFsInfo:
    """Tests for fs_info tool."""

    def test_info_file(self, get_tool, vfs):
        """Get info for a file."""
        vfs.write("/test.txt", "content")
        result = get_tool("fs_info").invoke({"path": "/test.txt"})
        assert result["status"] == "ok"
        assert result["response"]["name"] == "test.txt"
        assert result["response"]["type"] == "file"

    def test_info_directory(self, get_tool, vfs):
        """Get info for a directory."""
        vfs.mkdir("/mydir")
        result = get_tool("fs_info").invoke({"path": "/mydir"})
        assert result["status"] == "ok"
        assert result["response"]["name"] == "mydir"
        assert result["response"]["type"] == "directory"

    def test_info_nonexistent(self, get_tool):
        """Error for nonexistent path."""
        result = get_tool("fs_info").invoke({"path": "/nonexistent"})
        assert result["status"] == "error"


class TestFsLs:
    """Tests for fs_ls tool."""

    def test_ls_empty_directory(self, get_tool):
        """List empty directory."""
        result = get_tool("fs_ls").invoke({"path": "/"})
        assert result["status"] == "ok"
        assert result["response"] == []

    def test_ls_with_items(self, get_tool, vfs):
        """List directory with items."""
        vfs.write("/a.txt", "a")
        vfs.mkdir("/subdir")
        result = get_tool("fs_ls").invoke({"path": "/"})
        assert result["status"] == "ok"
        items = result["response"]
        names = [i["name"] for i in items]
        assert "a.txt" in names
        assert "subdir" in names


class TestFsWrite:
    """Tests for fs_write tool."""

    def test_write_creates_file(self, get_tool, vfs):
        """Write creates new file."""
        result = get_tool("fs_write").invoke({"path": "/new.txt", "content": "hello"})
        assert result["status"] == "ok"
        assert result["response"] is True
        # Verify via vfs
        assert vfs.read("/new.txt")["content"] == "hello"

    def test_write_overwrite(self, get_tool, vfs):
        """Write overwrites existing content."""
        vfs.write("/file.txt", "old")
        result = get_tool("fs_write").invoke(
            {"path": "/file.txt", "content": "new", "mode": "overwrite"}
        )
        assert result["status"] == "ok"
        assert vfs.read("/file.txt")["content"] == "new"

    def test_write_append(self, get_tool, vfs):
        """Write appends to existing content."""
        vfs.write("/file.txt", "hello")
        result = get_tool("fs_write").invoke(
            {"path": "/file.txt", "content": " world", "mode": "append"}
        )
        assert result["status"] == "ok"
        assert vfs.read("/file.txt")["content"] == "hello world"

    def test_write_none_creates_empty(self, get_tool, vfs):
        """Write with None content creates empty file."""
        result = get_tool("fs_write").invoke({"path": "/empty.txt"})
        assert result["status"] == "ok"
        assert vfs.info("/empty.txt")["type"] == "file"


class TestFsMkdir:
    """Tests for fs_mkdir tool."""

    def test_mkdir_creates_directory(self, get_tool, vfs):
        """Creates a directory."""
        result = get_tool("fs_mkdir").invoke({"path": "/mydir"})
        assert result["status"] == "ok"
        assert vfs.info("/mydir")["type"] == "directory"

    def test_mkdir_nested(self, get_tool, vfs):
        """Creates nested directories."""
        result = get_tool("fs_mkdir").invoke({"path": "/a/b/c"})
        assert result["status"] == "ok"
        assert vfs.info("/a/b/c")["type"] == "directory"


class TestFsRead:
    """Tests for fs_read tool."""

    def test_read_entire_file(self, get_tool, vfs):
        """Read entire file content."""
        vfs.write("/file.txt", "line1\nline2")
        result = get_tool("fs_read").invoke({"path": "/file.txt"})
        assert result["status"] == "ok"
        assert result["response"]["content"] == "line1\nline2"

    def test_read_line_range(self, get_tool, vfs):
        """Read specific line range."""
        vfs.write("/file.txt", "line0\nline1\nline2\nline3")
        result = get_tool("fs_read").invoke({"path": "/file.txt", "start": 1, "end": 3})
        assert result["status"] == "ok"
        assert result["response"]["content"] == "line1\nline2"

    def test_read_nonexistent(self, get_tool):
        """Error for nonexistent file."""
        result = get_tool("fs_read").invoke({"path": "/nonexistent.txt"})
        assert result["status"] == "error"


class TestFsGlob:
    """Tests for fs_glob tool."""

    def test_glob_matches(self, get_tool, vfs):
        """Find matching files."""
        vfs.write("/a.txt", "a")
        vfs.write("/b.txt", "b")
        vfs.write("/c.py", "c")
        result = get_tool("fs_glob").invoke({"pattern": "/*.txt"})
        assert result["status"] == "ok"
        names = [i["name"] for i in result["response"]]
        assert "a.txt" in names
        assert "b.txt" in names
        assert "c.py" not in names

    def test_glob_no_matches(self, get_tool, vfs):
        """No matches returns empty list."""
        vfs.write("/file.txt", "content")
        result = get_tool("fs_glob").invoke({"pattern": "/*.py"})
        assert result["status"] == "ok"
        assert result["response"] == []


class TestFsGrep:
    """Tests for fs_grep tool."""

    def test_grep_finds_match(self, get_tool, vfs):
        """Find pattern in file."""
        vfs.write("/file.txt", "hello world\nfoo bar")
        result = get_tool("fs_grep").invoke(
            {"grep_pattern": "hello", "path": "/file.txt"}
        )
        assert result["status"] == "ok"
        matches = result["response"]
        assert len(matches) == 1
        assert matches[0]["line_number"] == 0

    def test_grep_no_match(self, get_tool, vfs):
        """No matches returns empty list."""
        vfs.write("/file.txt", "hello world")
        result = get_tool("fs_grep").invoke(
            {"grep_pattern": "notfound", "path": "/file.txt"}
        )
        assert result["status"] == "ok"
        assert result["response"] == []

    def test_grep_ignore_case(self, get_tool, vfs):
        """Case insensitive matching."""
        vfs.write("/file.txt", "HELLO world")
        result = get_tool("fs_grep").invoke(
            {"grep_pattern": "hello", "path": "/file.txt", "ignore_case": True}
        )
        assert result["status"] == "ok"
        assert len(result["response"]) == 1

    def test_grep_directory(self, get_tool, vfs):
        """Search in directory."""
        vfs.mkdir("/dir")
        vfs.write("/dir/a.txt", "match here")
        vfs.write("/dir/b.txt", "no luck")
        result = get_tool("fs_grep").invoke({"grep_pattern": "match", "path": "/dir"})
        assert result["status"] == "ok"
        assert len(result["response"]) == 1

    def test_grep_line_window(self, get_tool, vfs):
        """Line window includes context."""
        vfs.write("/file.txt", "line0\nMATCH\nline2")
        result = get_tool("fs_grep").invoke(
            {"grep_pattern": "MATCH", "path": "/file.txt", "line_window": 1}
        )
        assert result["status"] == "ok"
        snippet = result["response"][0]["snippet"]
        assert "line0" in snippet
        assert "MATCH" in snippet
        assert "line2" in snippet
