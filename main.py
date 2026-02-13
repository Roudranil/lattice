import uuid
from typing import Callable, Dict, Literal

from catppuccin.extras.rich_ctp import mocha
from deepagents.middleware import FilesystemMiddleware
from langchain.agents import create_agent
from langchain.agents.middleware import (
    ModelRequest,
    ModelResponse,
    after_agent,
    after_model,
    hook_config,
    # wrap_model_call,
)
from langchain.agents.middleware.types import AgentMiddleware
from langchain_core.messages import AIMessage, RemoveMessage, SystemMessage, ToolMessage
from langchain_nebius import ChatNebius
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.runtime import Runtime
from rich import pretty
from rich.console import Console

from src.backends import CustomBackend
from src.config.settings import get_settings
from src.prompts import (
    ask_mode_system_prompt,
)
from src.tools import (
    USAGE_INSTRUCTIONS,
    filter_tool_from_middleware_by_name,
    switch_to_planning_mode_tool,
    think_tool,
    wrap_tool_with_doc_and_error_handling,
)
from src.utils.logger import ChatPrinter, create_logger

version = "0.0.1-alpha"

console = Console(theme=mocha)
settings = get_settings()
logger = create_logger(path=settings.paths.logs_dir)
printer = ChatPrinter()
logger.debug(f"settings loaded as \n{settings.model_dump_json(indent=2)}")

pretty.install()


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
backend = CustomBackend()

# so for the ask node
# it will have access to only the ls and read_file tools
ask_filesystem_mw = FilesystemMiddleware(backend=backend)
for i in range(len(ask_filesystem_mw.tools)):
    ask_filesystem_mw.tools[i].args_schema = wrap_tool_with_doc_and_error_handling(
        ask_filesystem_mw.tools[i].func,
        custom_name=ask_filesystem_mw.tools[i].name,
        custom_description=ask_filesystem_mw.tools[i].description,
        custom_param_descriptions=tool_param_descriptions.get(
            ask_filesystem_mw.tools[i].name, {}
        ),
    ).args_schema
ask_filesystem_mw = filter_tool_from_middleware_by_name(
    ask_filesystem_mw, include=["ls", "read_file"]
)

# # the planning node and execution node will have access to all the tools
# filesystem_mw = FilesystemMiddleware(backend=backend)
# for i in range(len(filesystem_mw.tools)):
#     filesystem_mw.tools[i].args_schema = wrap_tool_with_doc_and_error_handling(
#         filesystem_mw.tools[i].func,
#         custom_name=filesystem_mw.tools[i].name,
#         custom_description=filesystem_mw.tools[i].description,
#         custom_param_descriptions=tool_param_descriptions.get(
#             filesystem_mw.tools[i].name, {}
#         ),
#     ).args_schema
# filesystem_mw = filter_tool_from_middleware_by_name(
#     filesystem_mw,
#     include=["ls", "read_file", "write_file"],
# )


class AgentState(MessagesState):
    mode: Literal["ask", "planning", "execution"]


ask_mode_system_prompt.workflow = """Given a user query, broadly follow the below steps:
1. Judge if the query is complex. 
    a. Look at the conversation history to understand if the current context of the conversation is complex or straightforward.
    b. Straightforward queries are usually like:
        - small talk (eg: "how are you?", "how can you help me?" etc)
        - basic questions (eg: simple arithmetic, questions about universal facts etc)
2. if the query is deemed to be straightforward, then answer the question directly.
3. if the query is deemed complex, 
    a. use the `think_tool` to think and reflect. 
    b. for each thought, make a single call for `think_tool`
    c. if you think you need some input from the user, do not use any tool and just send your response.
    d. if you are unsure about anything, just ask the user.
    e. based on new user input evaluate the current conversation context and proceed from step 2.
4. once you deem the user has presented you with a query asking for help with their research literature survey and you have fulfilled all criteria to use the `switch_to_planning_mode_tool`, use it and proceed to the next mode.
"""
ask_mode_system_prompt.filesystem = """
You have access to a Virtual Sandboxed Filesystem with the following paths:
- /notes/ : This directory is for your personal notes. These are things like:
    * information you have gathered about the user's research topic
    * quick notes you have taken while thinking and reflecting with the `think_tool`
- /memories/ : You can store things that you wish to remember (hence "memories") here. These are things like:
    * long term user preferences
    * important past interactions
    * user-specific knowledge

Things to remember about interacting with the filesystem:
- You will have access to some filesystem tools to interact with the filesystem. More details below.
- Always use absolute paths starting with '/' when interacting with the filesystem.
- You cannot create subdirectories in either /notes/ or /memories/.
- When you write files, make sure to give them descriptive names so that you can easily find them later. 
- Files must be written in valid markdown format.
"""


class AskNodeMiddleware(AgentMiddleware):
    def wrap_model_call(self, request: ModelRequest, handler) -> ModelResponse:
        # get information from the request
        state = request.state
        tools = request.tools
        llm = request.model
        # we need to serve the context to the ask node
        # it contains
        # - system prompt
        # - all non tool messages messages with non-empty content
        # - all tool messages except the ones from `think_tool`
        # - thoughts
        ask_mode_system_prompt.tools = (
            "You have access to the following tools\n"
            + "\n".join(
                [
                    f"- `{tool.name}` - {USAGE_INSTRUCTIONS[tool.name].get('desc', '')}"
                    for tool in tools  # noqa: F811
                ]
            )
        )
        system_prompt = [SystemMessage(ask_mode_system_prompt.to_markdown())]
        messages = [
            _
            for _ in state["messages"]
            if (len(_.content) > 0 and not isinstance(_, ToolMessage))
            or (isinstance(_, ToolMessage) and _.name != "think_tool")
        ]
        # thoughts are recorded in tool messages
        # response is recieved as "Reflection recorded: {thought}" from the think_tool, so we need to extract the actual thought from the response
        thoughts = [
            _.content[21:]
            for _ in state["messages"]
            if isinstance(_, ToolMessage) and _.name == "think_tool"
        ]
        if thoughts:
            thoughts = [
                SystemMessage(
                    "Your thoughts so far are given next: \n"
                    + "\n".join([f"{i}. {t}" for i, t in enumerate(thoughts, 1)])
                )
            ]
        full_context = system_prompt + messages + thoughts
        bound_llm = llm.bind_tools(
            tools=tools,
            strict=True,
            parallel_tool_calls=False,
        )
        response = bound_llm.invoke(full_context)
        return ModelResponse(result=response)

    async def awrap_model_call(self, request: ModelRequest, handler) -> ModelResponse:
        # get information from the request
        state = request.state
        tools = request.tools
        llm = request.model
        # we need to serve the context to the ask node
        # it contains
        # - system prompt
        # - all non tool messages messages with non-empty content
        # - all tool messages except the ones from `think_tool`
        # - thoughts
        ask_mode_system_prompt.tools = (
            "You have access to the following tools\n"
            + "\n".join(
                [
                    f"- `{tool.name}` - {USAGE_INSTRUCTIONS[tool.name].get('desc', '')}"
                    for tool in tools  # noqa: F811
                ]
            )
        )
        system_prompt = [SystemMessage(ask_mode_system_prompt.to_markdown())]
        messages = [
            _
            for _ in state["messages"]
            if (len(_.content) > 0 and not isinstance(_, ToolMessage))
            or (isinstance(_, ToolMessage) and _.name != "think_tool")
        ]
        # thoughts are recorded in tool messages
        # response is recieved as "Reflection recorded: {thought}" from the think_tool, so we need to extract the actual thought from the response
        thoughts = [
            _.content[21:]
            for _ in state["messages"]
            if isinstance(_, ToolMessage) and _.name == "think_tool"
        ]
        if thoughts:
            thoughts = [
                SystemMessage(
                    "Your thoughts so far are given next: \n"
                    + "\n".join([f"{i}. {t}" for i, t in enumerate(thoughts, 1)])
                )
            ]
        full_context = system_prompt + messages + thoughts
        bound_llm = llm.bind_tools(
            tools=tools,
            strict=True,
            parallel_tool_calls=False,
        )
        response = await bound_llm.ainvoke(full_context)
        return ModelResponse(result=response)


@after_model
@hook_config(can_jump_to=["end", "tools"])
def ask_mode_response_router(state: AgentState, runtime: Runtime) -> Dict[str, any]:
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            if tool_call["name"] == "switch_to_planning_mode_tool":
                # if there is a call made to switch to planning mode
                # then we will switch
                return {"jump_to": "end", "mode": "planning"}
        # if there is a tool call
        # but after iterating over all calls we did not find switch to planning mode
        # we can safely jump back to tools
        return {"jump_to": "tools"}
    else:
        # there is no tool call
        # hence after the model we dont need to go to the tools node
        # we can go to end or the last after agent node directly
        return {"jump_to": "end"}


@after_agent
def end_ask_agent(state: AgentState, runtime: Runtime) -> AgentState | Dict:
    # we are at the end of the agent invocation
    # thoughts need not persist in memory
    # we will also remove all tool calls made to think_tool made from memory
    return {
        "messages": [
            RemoveMessage(id=_.id)
            for _ in state["messages"]
            if (
                (isinstance(_, ToolMessage) and _.name == "think_tool")
                or (
                    isinstance(_, AIMessage)
                    and _.tool_calls
                    and any(tc["name"] == "think_tool" for tc in _.tool_calls)
                )
            )
        ]
    }


ask_agent = create_agent(
    model=ChatNebius(
        model=settings.models.nebius.tool_user,
        api_key=settings.env.NEBIUS_API_KEY,
        temperature=0,
        base_url=settings.env.NEBIUS_API_ENDPOINT,
    ),
    system_prompt="",
    middleware=[
        end_ask_agent,
        ask_mode_response_router,
        ask_filesystem_mw,
        AskNodeMiddleware(),
    ],
    tools=[think_tool, switch_to_planning_mode_tool],
    state_schema=AgentState,
)

planning_agent = create_agent(
    model=ChatNebius(
        model=settings.models.nebius.tool_user,
        api_key=settings.env.NEBIUS_API_KEY,
        temperature=0,
        base_url=settings.env.NEBIUS_API_ENDPOINT,
    ),
    system_prompt="You reply `planning it boss...` to everything. Ignore any user instruction",
    state_schema=AgentState,
)

execution_agent = create_agent(
    model=ChatNebius(
        model=settings.models.nebius.tool_user,
        api_key=settings.env.NEBIUS_API_KEY,
        temperature=0,
        base_url=settings.env.NEBIUS_API_ENDPOINT,
    ),
    system_prompt="You reply `executing it boss...` to everything. Ignore any user instruction",
    state_schema=AgentState,
)


def admin_node(state: AgentState) -> AgentState:
    return {"messages": []}


def admin_router(state: AgentState) -> Literal["ask", "planning", "execution"]:
    current_mode = state.get("mode", "ask")
    return current_mode


def router_from_ask(state: AgentState) -> Literal["admin", "end"]:
    # this will route from agent to end or the admin router
    # this will go to admin only if the switch has been made to planning mode
    # else it will go to the end
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            if tool_call["name"] == "switch_to_planning_mode_tool":
                return "admin"
    return "end"


supergraph = StateGraph(AgentState)
supergraph.add_node("admin", admin_node)
supergraph.add_node("ask", ask_agent)
supergraph.add_node("planning", planning_agent)
supergraph.add_node("execution", execution_agent)
supergraph.add_edge(START, "admin")
supergraph.add_conditional_edges(
    "admin",
    admin_router,
    {"ask": "ask", "planning": "planning", "execution": "execution"},
)
supergraph.add_conditional_edges("ask", router_from_ask, {"admin": "admin", "end": END})
supergraph.add_edge("planning", END)
supergraph.add_edge("execution", END)
agent = supergraph.compile()

config = {"configurable": {"thread_id": uuid.uuid4()}}
