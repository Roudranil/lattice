from deepagents.middleware.filesystem import (
    READ_FILE_TOOL_DESCRIPTION,
    EDIT_FILE_TOOL_DESCRIPTION,
    GLOB_TOOL_DESCRIPTION,
    LIST_FILES_TOOL_DESCRIPTION,
    GREP_TOOL_DESCRIPTION,
)

USAGE_INSTRUCTIONS = {
    # -- thinking tools --
    # think
    "think_tool": {
        "desc": "Think and reflect",
        "usage": """Use this tool to reflect and think strategically.""",
    },
    # -- mode switching tools --
    # switch to planning mode
    "switch_to_planning_mode_tool": {
        "desc": "Switch to planning mode",
        "usage": """"use this tool when you want to switch modes to PLANNING from ASK.""",
    },
    # switch to execution mode
    # switch to ask mode
    # -- filesystem tools --
    "ls": {
        "desc": "List all files in a directory",
        "usage": "Use this tool for exploring the filesystem and finding the right file to read or edit.You should almost ALWAYS use this tool before using the `read_file` or `edit_file` tools.",
    },
    "read_file": {
        "desc": "Reads a file from the filesystem",
        "usage": "Use this tool to read files from the filesystem. Always use this tool before using the `edit_file` tool. There is a limit on contents returned (see tool schema). If you want to search, use the `grep` tool.",
    },
    "write_file": {
        "desc": "Writes to a new file in the filesystem",
        "usage": "Use this tool to write to files in the filesystem. Always use this tool after using the `read_file` tool to ensure you have the latest file contents. Always write files in valid markdown format. Never use emojis.",
    },
    "edit_file": {
        "desc": "Performs exact string replacements in files",
        "usage": "Use this tool to edit files in the filesystem. Always use this tool after using the `read_file` tool to ensure you have the latest file contents. Always write files in valid markdown format. Never use emojis.",
    },
    "glob": {
        "desc": "Find files matching a glob pattern",
        "usage": "use this tool to search for files in the filesystem using standard glob patterns.",
    },
    "grep": {
        "desc": "Search for a text pattern across files",
        "usage": "Use this tool to search for specific patterns of text across files in the filesystem. ",
    },
}
