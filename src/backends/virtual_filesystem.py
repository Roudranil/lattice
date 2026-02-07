# import warnings and ignore the UserWarning recieved when importing fs
# warning text:
# .venv/lib/python3.11/site-packages/fs/__init__.py:4: UserWarning: pkg_resources is deprecated as an API.
# See https://setuptools.pypa.io/en/latest/pkg_resources.html.
# The pkg_resources package is slated for removal as early as 2025-11-30.
# Refrain from using this package or pin to Setuptools<81.
#   __import__("pkg_resources").declare_namespace(__name__)  # type: ignore
import warnings

warnings.simplefilter("ignore", category=UserWarning)

# now we can import fs without seeing these warnings
import re
from typing import Dict, List, Literal, Optional

from fs import path as fs_path
from fs.memoryfs import MemoryFS

from src.schemas.virtual_filesystem import FileContent, Info


class VirtualFilesystem:
    def __init__(self):
        """
        Instantiates a virtual filesystem backend with public methods that can be exposed as tools
        """
        self.fs = MemoryFS()
        self.cwd = "/"

        # create some pre-existing directories that the agent can use
        # /memories -> for memories in the current thread
        # /artifacts -> in case there are any references to any artifacts
        self.fs.makedirs("/memories")
        self.fs.makedirs("/artifacts")

    def _resolve(self, path: str) -> str:
        """Resolve a path to an absolute normalized path.

        Converts relative paths to absolute by joining with current working
        directory. Absolute paths are normalized but otherwise unchanged.

        Args:
            path (str): The path to resolve. Can be relative or absolute.

        Returns:
            str: The normalized absolute path.
        """
        if path.startswith("/"):
            return fs_path.normpath(path)
        return fs_path.normpath(fs_path.join(self.cwd, path))

    def info(self, path: str = "/") -> Dict:
        """Get metadata information about a file or directory.

        Args:
            path (str): Path to the file or directory. Defaults to root "/".

        Returns:
            Dict: Dictionary containing 'name', 'path', and 'type' (file/directory).

        Raises:
            FSError: If the path does not exist.
        """
        info = self.fs.getinfo(self._resolve(path))
        info = Info(
            name=info.name,
            type="directory" if info.is_dir else "file",
            path=self._resolve(path),
        )
        return info.model_dump()

    def ls(self, path: str = "/") -> List[Dict]:
        """List contents of a directory.

        Args:
            path (str, optional): Path to the directory. Defaults to root "/".

        Returns:
            List[Dict]: List of info dictionaries for each item in the directory.
            Each dict contains 'name', 'path', and 'type' keys.

        Raises:
            FSError: If the path does not exist or is not a directory.
        """
        result = self.fs.listdir(self._resolve(path))
        out = []
        for r in result:
            out.append(self.info(fs_path.join(self._resolve(path), r)))
        return out

    def write(
        self,
        path: str,
        content: Optional[str] = None,
        mode: Literal["append", "overwrite"] = "overwrite",
    ) -> bool:
        """Write content to a file, creating it if it doesn't exist.

        Two-part behavior:
        1. If the file doesn't exist, create it (empty)
        2. If content is provided, update the file based on mode

        Args:
            path (str): Path to the file to write.
            content (Optional[str], optional): Text content to write. If None, only ensures file exists. Defaults to None.
            mode (Literal["append", "overwrite"], optional): Write mode - 'append' to add to end, 'overwrite' to replace. Defaults to 'overwrite'.

        Returns:
            bool: True on success.

        Raises:
            FSError: If parent directory doesn't exist or path is invalid.
        """
        resolved = self._resolve(path)

        # Step 1: Ensure file exists
        if not self.fs.exists(resolved):
            self.fs.create(resolved)

        # Step 2: Update content if provided
        if content is not None:
            if mode == "append":
                self.fs.appendtext(resolved, content)
            else:
                self.fs.writetext(resolved, content)

        return self.info(resolved)

    def mkdir(self, path: str) -> bool:
        """Create a directory, including any necessary parent directories.

        Args:
            path (str): Path to the directory to create.

        Returns:
            bool: True on success.

        Raises:
            FSError: If directory already exists or path is invalid.
        """
        self.fs.makedirs(self._resolve(path))
        return self.info(self._resolve(path))

    def read(
        self, path: str, start: Optional[int] = None, end: Optional[int] = None
    ) -> Dict:
        """Read text content from a file, optionally a specific line range.

        Uses 0-indexed line numbers with Python slice semantics.

        Args:
            path (str): Path to the file to read.
            start (Optional[int], optional): Starting line index (0-indexed, inclusive). Defaults to 0.
            end (Optional[int], optional): Ending line index (0-indexed, exclusive). Defaults to total lines.

        Returns:
            Dict: Dictionary with 'info' (file metadata), 'start', 'end', and 'content'.

        Raises:
            FSError: If the file does not exist.
        """
        full_content = self.fs.readtext(self._resolve(path))
        lines = full_content.split("\n")
        if start is None:
            start = 0
        if end is None:
            end = len(lines)
        start = max(0, start)
        end = max(min(len(lines), end), start + 1)
        subset_content = "\n".join(lines[start:end])
        out = FileContent(
            info=self.info(self._resolve(path)),
            start=start,
            end=end,
            content=subset_content,
        )
        return out.model_dump()

    def glob(self, pattern: str) -> List[Dict]:
        """Find files matching a glob pattern.

        The pattern is resolved relative to the current working directory.
        Standard glob wildcards are supported: *, **, ?

        Args:
            pattern: Glob pattern to match (e.g., '*.py', 'dir/**/*.txt').

        Returns:
            List of info dictionaries for each matching file/directory.
        """
        # Resolve the parent directory, keep the pattern portion intact
        if "/" in pattern:
            parent = fs_path.dirname(pattern)
            glob_part = fs_path.basename(pattern)
            resolved_parent = self._resolve(parent)
            full_pattern = fs_path.join(resolved_parent, glob_part)
        else:
            # Pattern like "*.py" - resolve relative to cwd
            full_pattern = fs_path.join(self.cwd, pattern)

        matches = self.fs.glob(full_pattern)
        return [self.info(match.path) for match in matches]

    def _process_file(
        self,
        file_path: str,
        pattern: re.Pattern,
        character_window: Optional[int] = None,
        line_window: Optional[int] = None,
    ) -> List[Dict]:
        """Process a single file for grep pattern matches.

        Internal method used by grep() to search within files.

        Args:
            file_path (str): Absolute path to the file to search.
            pattern (re.Pattern): Compiled regex pattern to search for.
            character_window (Optional[int], optional): Context characters around match. Mutually exclusive with line_window. Defaults to None.
            line_window (Optional[int], optional): Context lines around match. Takes precedence over character_window. Defaults to None.

        Returns:
            List of match dictionaries with keys: 'path', 'snippet', 'line_number', 'match_range'.
        """
        content = self.read(file_path)["content"]
        lines = content.split("\n")
        results = []
        for row, line in enumerate(lines):
            for match in pattern.finditer(line):
                match_start = match.start()
                match_end = match.end()
                if line_window is not None:
                    start = max(0, row - line_window)
                    end = min(len(lines), row + line_window + 1)
                    snippet = "\n".join(lines[start:end])
                elif character_window is not None:
                    char_start = max(0, match_start - character_window)
                    char_end = min(len(line), match_end + character_window)
                    snippet = line[char_start:char_end]
                else:
                    snippet = line
                results.append(
                    {
                        "path": file_path,
                        "snippet": snippet,
                        "line_number": row,
                        "match_range": [match_start, match_end],
                        "match": match.group(0),
                    }
                )
        return results

    def grep(
        self,
        grep_pattern: str,
        path: str,
        file_name_pattern: Optional[str | List] = None,
        character_window: Optional[int] = None,
        line_window: Optional[int] = None,
        ignore_case: bool = False,
    ) -> List[Dict]:
        """Search for regex pattern matches within files.

        Searches a file or recursively walks a directory to find matches.
        Note: When path is a file, file_name_pattern is ignored.

        Args:
            grep_pattern (str): Regex pattern to search for.
            path (str): Path to file or directory to search.
            file_name_pattern (Optional[str  |  List], optional): Glob pattern(s) to filter files when searching directories. Defaults to None.
            character_window (Optional[int], optional): Number of characters to include around match. Defaults to None.
            line_window (Optional[int], optional): Number of lines to include around match (takes precedence). Defaults to None.
            ignore_case (bool, optional): Whether to perform case-insensitive matching. Defaults to False.

        Returns:
            List[Dict]: List of match dicts with 'path', 'snippet', 'line_number', 'match_range'.
        """
        results = []
        compiled = re.compile(grep_pattern, flags=re.IGNORECASE if ignore_case else 0)
        resolved = self._resolve(path)
        info = self.info(resolved)
        if info["type"] == "file":
            out = self._process_file(resolved, compiled, character_window, line_window)
            if out:
                results.extend(out)
        else:
            if file_name_pattern is None:
                filters = None
            elif isinstance(file_name_pattern, list):
                filters = file_name_pattern
            else:
                filters = [file_name_pattern]
            walker = self.fs.walk
            files = walker.files(path=resolved, filter=filters)
            for f in sorted(files):
                out = self._process_file(f, compiled, character_window, line_window)
                if out:
                    results.extend(out)
        return results
