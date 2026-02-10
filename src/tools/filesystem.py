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

from src.backends.filesystem import VirtualFilesystem
from src.schemas.filesystem import FSResponse

from .utils import wrap_tool_with_doc_and_error_handling


def create_filesystem_tools(vfs: VirtualFilesystem) -> List:
    """Create LangChain tools bound to a VirtualFilesystem instance.

    Args:
        vfs (VirtualFilesystem): The filesystem instance to operate on.

    Returns:
        List: List of LangChain tool functions.
    """

    @wrap_tool_with_doc_and_error_handling
    def fs_info(path: str = "/") -> Dict:
        """Get metadata information about a file or directory.

        Args:
            path (str): Path to the file or directory. Defaults to root "/".

        Returns:
            Dict: dict with the keys "status", "error" and "response".
            "response" is a info dict with the below keys on success:
            name (str): name of the file
            path (str): absolute path to the file
            type (str): file or directory

        Examples:
        ```
        input:
            {"path": "/"}
        output:
            {'status': 'ok', 'error': None, 'response': {'name': '', 'path': '/', 'type': 'directory'}}
        ```
        """
        return vfs.info(path)

    @wrap_tool_with_doc_and_error_handling
    def fs_ls(path: str = "/") -> Dict:
        """List contents of a directory.

        Args:
            path (str): Path to the directory. Defaults to root "/".

        Returns:
            Dict: dict with the keys "status", "error" and "response".
            "response" is a list of info dicts with the below keys for each file:
            name (str): name of the file
            path (str): absolute path to the file
            type (str): file or directory

        Examples:
        ```
        input:
            {"path": "/"}
        output:
            {
                'status': 'ok',
                'error': None,
                'response': [
                    {'name': 'memories', 'path': '/memories', 'type': 'directory'},
                    {'name': 'artifacts', 'path': '/artifacts', 'type': 'directory'}
                ]
            }
        ```
        """
        return vfs.ls(path)

    @wrap_tool_with_doc_and_error_handling
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
            Dict: dict with the keys "status", "error" and "response".
            "response" is a info dict with the below keys on success:
            name (str): name of the file
            path (str): absolute path to the file
            type (str): file or directory

        Examples:
        ```
        input:
            {"path": "/RESEARCH_PLAN.md", "content": "# Research plan", "mode": "overwrite"}
        output:
            {
                'status': 'ok',
                'error': None,
                'response': {'name': 'RESEARCH_PLAN.md', 'path': '/RESEARCH_PLAN.md', 'type': 'file'}
            }
        ```
        """
        return vfs.write(path, content, mode)

    @wrap_tool_with_doc_and_error_handling
    def fs_mkdir(path: str) -> Dict:
        """Create a directory, including any necessary parent directories.

        Args:
            path (str): Path to the directory to create.

        Returns:
            Dict: dict with the keys "status", "error" and "response".
            "response" is a info dict with the below keys on success:
            name (str): name of the file
            path (str): absolute path to the file
            type (str): file or directory

        Examples:
        ```
        input:
            {"path": "/artifacts/notes/"}
        output:
            {'status': 'ok', 'error': None, 'response': {'name': 'notes', 'path': '/artifacts/notes', 'type': 'directory'}}
        """
        return vfs.mkdir(path)

    @wrap_tool_with_doc_and_error_handling
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
            Dict: dict with the keys "status", "error" and "response".
            "response" contains the following keys: 'info' dict, 'start', 'end', and 'content'.

        Examples:
        ```
        output:
            {
                'status': 'ok',
                'error': None,
                'response': {
                    'info': {'name': 'note.md', 'path': '/artifacts/notes/note.md', 'type': 'file'},
                    'start': 0,
                    'end': 1,
                    'content': 'Lorem ipsum dolor sit amet, consectetur adipiscing elit'
                }
            }
        ```
        """
        return vfs.read(path, start, end)

    @wrap_tool_with_doc_and_error_handling
    def fs_glob(pattern: str) -> Dict:
        """Find files matching a glob pattern.

        Pattern is resolved relative to current working directory.
        Supports wildcards: *, **, ?

        Args:
            pattern (str): Glob pattern (e.g., '*.py', 'dir/**/*.txt').

        Returns:
            Dict: dict with the keys "status", "error" and "response".
            "response" is a list of info dicts with the below keys:
            name (str): name of the file
            path (str): absolute path to the file
            type (str): file or directory

        Examples:
        ```
        input:
            {"pattern": "**/*note*"}
        output:
            {
                'status': 'ok',
                'error': None,
                'response': [
                    {'name': 'mynote2.py', 'path': '/artifacts/mynote2.py', 'type': 'file'},
                    {'name': 'note.md', 'path': '/artifacts/notes/note.md', 'type': 'file'},
                    {'name': 'mynote.md', 'path': '/artifacts/notes/mynote.md', 'type': 'file'}
                ]
            }
        """
        return vfs.glob(pattern)

    @wrap_tool_with_doc_and_error_handling
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
            grep_pattern (str): Regex pattern to search for. Does not support grepping across lines. Only patterns that grep in a single line will work.
            path (str): Path to file or directory to search.
            file_name_pattern (Optional[str]): Glob pattern to filter files in directories.
            character_window (Optional[int]): Characters of context around match.
            line_window (Optional[int]): Lines of context around match (takes precedence).
            ignore_case (bool): Case-insensitive matching. Defaults to False.

        Returns:
            Dict: dict with the keys "status", "error" and "response".
            "response" is a list of dicts with the below keys:
            path (str): path to the matched file
            snippet (str): the matched snippet including windows
            line_number (str): the line number where the match was found
            match_range (list): list[start, end] to denote the indices on that line where the match was found.
            match (Optional[str]): the exact string matched (without windows)

        Examples:
        ```
        input:
            {"path": "/", "grep_pattern": "ipsum", "character_window": 2}
        output:
            {
                'status': 'ok',
                'error': None,
                'response': [
                    {'path': '/artifacts/mynote2.py', 'snippet': 'm ipsum d', 'line_number': 0, 'match_range': [6, 11]},
                    {'path': '/artifacts/mynote2.py', 'snippet': 'ipsum d', 'line_number': 1, 'match_range': [0, 5]},
                    {'path': '/artifacts/notes/note.md', 'snippet': 'm ipsum d', 'line_number': 0, 'match_range': [6, 11]}
                ]
            }
        ```
        """
        return vfs.grep(
            grep_pattern,
            path,
            file_name_pattern,
            character_window,
            line_window,
            ignore_case,
        )

    return [fs_info, fs_ls, fs_write, fs_mkdir, fs_read, fs_glob, fs_grep]
