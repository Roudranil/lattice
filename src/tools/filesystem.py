from deepagents.backends import BackendProtocol
from deepagents.middleware import FilesystemMiddleware
from langchain.agents.middleware.types import AgentMiddleware

from .utils import wrap_tool_with_doc_and_error_handling

tool_param_descriptions = {
    "ls": {"path": "Absolute path to the directory to list. Must start with '/'. "},
    "read_file": {
        "file_path": "Absolute path to the file to read. Must start with '/'",
        "offset": "Line number to start reading from (0-indexed). Default: 0.",
        "limit": "Maximum number of lines to read. Default: 2000.",
    },
    "write_file": {
        "file_path": "Absolute path where the file should be created. Must start with '/'.",
        "content": "String content to write to the file.",
    },
    "edit_file": {
        "file_path": "Absolute path to the file to edit. Must start with '/'.",
        "old_string": "Exact string to search for and replace. Must match exactly including whitespace and indentation.",
        "new_content": "String to replace old_string with. Must be different from old_string.",
        "replace_all": "If True, replace all occurrences. If False (default), old_string must be unique in the file or the edit fails.",
    },
    "glob": {
        "pattern": "Glob pattern to match files against (e.g., `'*.py'`, `'**/*.txt'`).",
        "path": "Base directory to search from. Defaults to root (`/`).",
    },
    "grep": {
        "pattern": ' Literal string to search for (NOT regex). Performs exact substring matching within file content. Example: "TODO" matches any line containing "TODO", but not "TODOS" or "TO DO".',
        "path": 'Optional directory path to search in. If None, searches in current working directory. Example: "/workspace/src".',
        "glob": """Optional glob pattern to filter which FILES to search.
Filters by filename/path, not content.
Supports standard glob wildcards:
- `*` matches any characters in filename
- `**` matches any directories recursively
- `?` matches single character
- `[abc]` matches one character from set""",
        "output_mode": """Specifies format of grep output. Options:
- file_with_matches: file paths only, default
- content: matching lines with content
- count: match counts per file""",
    },
}


class FileSystemToolsMiddleware(FilesystemMiddleware):
    def __init__(
        self,
        *,
        backend: BackendProtocol = None,
        system_prompt: str = None,
        custom_tool_descriptions: dict = None,
        tool_token_limit_before_evict: int = 20000,
        include_tools_by_name: str = [],
        exclude_tools_by_name: str = ["execute"],
    ):
        super().__init__(
            backend=backend,
            system_prompt=system_prompt,
            custom_tool_descriptions=custom_tool_descriptions,
            tool_token_limit_before_evict=tool_token_limit_before_evict,
        )

        # filter from the default filesystem tools
        # like, by default "execute" tool is excluded
        # and then reassing the schemas for them
        include_set = set(include_tools_by_name)
        exclude_set = set(exclude_tools_by_name)
        if include_set:
            self.tools = [
                tool
                for tool in self.tools
                if getattr(tool, "name", None) in include_set
            ]
        if exclude_set:
            self.tools = [
                tool
                for tool in self.tools
                if getattr(tool, "name", None) not in exclude_set
            ]
        for i in range(len(self.tools)):
            self.tools[i].args_schema = wrap_tool_with_doc_and_error_handling(
                self.tools[i].func,
                custom_name=self.tools[i].name,
                custom_description=self.tools[i].description,
                custom_param_descriptions=tool_param_descriptions.get(
                    self.tools[i].name, {}
                ),
            ).args_schema

    # need to implement the write todos and research plans tool
    # they need to be sync and async
    def _create_write_todos_tool(self):
        pass

    def _create_write_research_plan(self):
        pass
