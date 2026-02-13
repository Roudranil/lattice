from typing import Dict

from langchain.agents import create_agent
from langchain.agents.middleware import (
    ModelRequest,
    ModelResponse,
    after_agent,
    after_model,
    hook_config,
)
from langchain.agents.middleware.types import AgentMiddleware
from langchain_core.messages import AIMessage, RemoveMessage, SystemMessage, ToolMessage
from langgraph.runtime import Runtime

from src import __version__
from src.backends import CustomBackend
from src.prompts import ask_mode_system_prompt
from src.tools import (
    USAGE_INSTRUCTIONS,
    FileSystemToolsMiddleware,
    switch_to_planning_mode_tool,
    think_tool,
)
from src.utils.run_async import run_async_safely

from .state import AgentState

backend = CustomBackend()
filesystem_mw = FileSystemToolsMiddleware(
    backend=backend, include_tools_by_name=["ls", "read_file"]
)


# define our own middlewares
class AskNodeMiddleware(AgentMiddleware):
    def wrap_model_call(self, request: ModelRequest, handler) -> ModelResponse:
        return run_async_safely(self.awrap_model_call(request, handler))

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


def create_ask_agent(model):
    return create_agent(
        model=model,
        system_prompt="",
        middleware=[
            end_ask_agent,
            ask_mode_response_router,
            filesystem_mw,
            AskNodeMiddleware(),
        ],
        tools=[think_tool, switch_to_planning_mode_tool],
        state_schema=AgentState,
    )
