"""
LangChain tool wrappers for VirtualFilesystem operations.

These tools provide LLM-accessible filesystem operations on a shared
VirtualFilesystem instance. All tools return FSResponse-structured
dictionaries with 'status', 'error', and 'response' keys.

Usage:
    from src.backends.virtual_filesystem import VirtualFilesystem
    from src.tools.filesystem_tools import create_filesystem_tools

    vfs = VirtualFilesystem()
    tools = create_filesystem_tools(vfs)
    # tools can now be bound to an LLM
"""

from typing import Dict, List, Literal, Optional

from langchain_core.tools import tool

from src.backends.virtual_filesystem import VirtualFilesystem
from src.schemas.virtual_filesystem import FSResponse


def _wrap_response(func):
    """Wrap function result in FSResponse structure."""

    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return FSResponse(status="ok", error=None, response=result).model_dump()
        except Exception as e:
            return FSResponse(status="error", error=str(e), response=None).model_dump()

    return wrapper


def create_filesystem_tools(vfs: VirtualFilesystem) -> List:
    """Create LangChain tools bound to a VirtualFilesystem instance.

    Args:
        vfs (VirtualFilesystem): The filesystem instance to operate on.

    Returns:
        List: List of LangChain tool functions.
    """

    @tool
    def fs_info(path: str = "/") -> Dict:
        """Get metadata information about a file or directory.

        Args:
            path (str): Path to the file or directory. Defaults to root "/".

        Returns:
            Dict: FSResponse with 'status', 'error', and 'response' containing
                  'name', 'path', and 'type' (file/directory).
        """
        return _wrap_response(vfs.info)(path)

    @tool
    def fs_ls(path: str = "/") -> Dict:
        """List contents of a directory.

        Args:
            path (str): Path to the directory. Defaults to root "/".

        Returns:
            Dict: FSResponse with list of info dicts for each item.
        """
        return _wrap_response(vfs.ls)(path)

    @tool
    def fs_write(
        path: str,
        content: Optional[str] = None,
        mode: Literal["append", "overwrite"] = "overwrite",
    ) -> Dict:
        """Write content to a file, creating it if it doesn't exist.

        If file doesn't exist, it is created. If content is provided, file is
        updated based on mode.

        Args:
            path (str): Path to the file to write.
            content (Optional[str]): Text content to write. If None, only ensures file exists.
            mode (Literal["append", "overwrite"]): 'append' adds to end, 'overwrite' replaces.

        Returns:
            Dict: FSResponse with True on success.
        """
        return _wrap_response(vfs.write)(path, content, mode)

    @tool
    def fs_mkdir(path: str) -> Dict:
        """Create a directory, including any necessary parent directories.

        Args:
            path (str): Path to the directory to create.

        Returns:
            Dict: FSResponse with True on success.
        """
        return _wrap_response(vfs.mkdir)(path)

    @tool
    def fs_read(
        path: str,
        start: Optional[int] = None,
        end: Optional[int] = None,
    ) -> Dict:
        """Read text content from a file, optionally a specific line range.

        Uses 0-indexed line numbers with Python slice semantics.

        Args:
            path (str): Path to the file to read.
            start (Optional[int]): Starting line index (0-indexed, inclusive).
            end (Optional[int]): Ending line index (0-indexed, exclusive).

        Returns:
            Dict: FSResponse with 'info', 'start', 'end', and 'content'.
        """
        return _wrap_response(vfs.read)(path, start, end)

    @tool
    def fs_glob(pattern: str) -> Dict:
        """Find files matching a glob pattern.

        Pattern is resolved relative to current working directory.
        Supports wildcards: *, **, ?

        Args:
            pattern (str): Glob pattern (e.g., '*.py', 'dir/**/*.txt').

        Returns:
            Dict: FSResponse with list of matching file/directory info dicts.
        """
        return _wrap_response(vfs.glob)(pattern)

    @tool
    def fs_grep(
        grep_pattern: str,
        path: str,
        file_name_pattern: Optional[str] = None,
        character_window: Optional[int] = None,
        line_window: Optional[int] = None,
        ignore_case: bool = False,
    ) -> Dict:
        """Search for regex pattern matches within files.

        Searches a file or recursively walks a directory to find matches.
        When path is a file, file_name_pattern is ignored.

        Args:
            grep_pattern (str): Regex pattern to search for.
            path (str): Path to file or directory to search.
            file_name_pattern (Optional[str]): Glob pattern to filter files in directories.
            character_window (Optional[int]): Characters of context around match.
            line_window (Optional[int]): Lines of context around match (takes precedence).
            ignore_case (bool): Case-insensitive matching. Defaults to False.

        Returns:
            Dict: FSResponse with list of matches containing 'path', 'snippet',
                  'line_number', 'match_range'.
        """
        return _wrap_response(vfs.grep)(
            grep_pattern,
            path,
            file_name_pattern,
            character_window,
            line_window,
            ignore_case,
        )

    return [fs_info, fs_ls, fs_write, fs_mkdir, fs_read, fs_glob, fs_grep]
