# %% [markdown]
# # imports and setup
#

# %%
import sys
from datetime import datetime
from pathlib import Path

from catppuccin.extras.rich_ctp import mocha
from rich import pretty
from rich.console import Console
from rich.pretty import pprint

pretty.install()


parent_dir = Path(__file__).resolve().parent.parent

if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from src.config.settings import get_settings
from src.utils.logger import ChatPrinter, create_logger

console = Console(theme=mocha)
settings = get_settings()
logger = create_logger(path=settings.paths.logs_dir)
printer = ChatPrinter()
logger.debug(f"settings loaded as \n{settings.model_dump_json(indent=2)}")

# %%
from typing import Annotated, Dict, List, Literal, Optional, TypedDict

from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    HumanMessage,
    MessageLikeRepresentation,
    SystemMessage,
    ToolMessage,
    convert_to_openai_messages,
    filter_messages,
    get_buffer_string,
)
from langchain_core.tools import tool
from langchain_core.utils.function_calling import convert_to_openai_tool
from langchain_nebius import ChatNebius
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.types import Command, interrupt
from pydantic import BaseModel, Field, create_model
from pydantic.json_schema import SkipJsonSchema

# %%
from src.backends.filesystem import VirtualFilesystem
from src.prompts import (
    planning_mode_systemm_prompt,
    planning_structured_output,
)
from src.schemas import RESEARCH_PLAN_TEMPLATE, ResearchPlan
from src.schemas.prompts import SystemPromptTemplate
from src.tools.filesystem import create_filesystem_tools
from src.tools.utils import SkipSchema, wrap_tool_with_doc_and_error_handling
from src.utils.stats import accumulate_usage, add_usage_metadata

version = "0.0.1-alpha"

# %%
filesystem_tools = create_filesystem_tools(VirtualFilesystem())

# %% [markdown]
# # state
#


# %%
class TodoItems(TypedDict):
    content: str
    subitems: List[str]


# class UsageMetadata(TypedDict):
#     input_tokens: int
#     output_tokens: int
#     total_tokens: int
#     input_token_details: dict
#     output_token_details: dict


class AgentState(TypedDict):
    # list of messages
    messages: Annotated[List[MessageLikeRepresentation], add_messages]
    # # running statistics
    # # TODO: decide if this is even needed
    # # are we doing mroe than one LLM call per node?
    # # if no we dont need this
    # usage_metadata: Annotated[UsageMetadata, add_usage_metadata] = {
    #     "input_tokens": 0,
    #     "output_tokens": 0,
    #     "total_tokens": 0,
    #     "input_token_details": {},
    #     "output_token_details": {},
    # }
    # current mode
    mode: Literal["ask", "planning", "execution"]
    # whatever the agent needs across all the modes
    todo: List[TodoItems]
    research_plan: str | ResearchPlan
    plan_approval_status: Literal["pending", "rejected", "approved"]
    # thoughts
    thoughts: Annotated[List[AIMessage], add_messages]


# %% [markdown]
# # LLM
#

# %% [markdown]
# ## structured output for ask node
#


# %%
class AskNodeResponse(BaseModel):
    message: str = Field(description="The response to the user message.")
    ready_to_draft_plan: bool = Field(
        description="Classify if you have enough information to draft the research plan given the conversation history. You will recieve this after using the ready_to_draft_plan_tool."
    )


# %%
chat_llm = ChatOpenAI(
    model=settings.models.nebius.tool_user,
    api_key=settings.env.NEBIUS_API_KEY,
    base_url=settings.env.NEBIUS_API_ENDPOINT,
    max_completion_tokens=8192,
    temperature=0.0,
    top_p=0.7,
    streaming=True,
)

# %% [markdown]
# # Graph
#


# %%
@wrap_tool_with_doc_and_error_handling
def think_tool(reflection: str, state: SkipSchema[Dict] = None) -> str:
    """Strategic reflection and thinking tool. Use this tool to reflect on the conversation so far and what you should do next. Ask questions such as:
    - What does the user want me to do next?
    - What information do I have so far?
    - Do I have enough information to give a final answer?
    - If i am missing information, what should I ask for?

    Args:
        reflection (str): Your detailed reflection on the conversation so far. Your reflection should not be more than 2 sentences.

    Returns:
        str: Confirmation that reflection was recorded for decision making
    """
    return f"Reflection recorded: {reflection}"


# %%
short_system_prompt = SystemPromptTemplate(
    name="Assistant",
    node_name="Helper",
    description="You are a helpful and thoughtful assistant who thinks before answering",
    tools="""You have access to the following tools:
- `think_tool`: Use this tool to reflect and think strategically. Use your reflections to refine your next course of action. You should pass exactly one thought to this tool at a single time. To maintain a clear line of reasoning, your thought should be short and at maximum 2 - 3 simple sentences only. If you are reviewing your past thoughts with this tool, then make sure to critique your past thoughts.
""",
    workflow="""Given a user query, broadly follow the below steps:
1. Judge if the query is complex. 
    a. Look at the conversation history to understand if the current context of the conversation is complex or straightforward.
    b. Straightforward queries are usually like:
        - small talk (eg: "how are you?", "how can you help me?" etc)
        - basic questions (eg: simple arithmetic, questions about universal facts etc)
2. if the query is deemed to be straightforward, then answer the question directly.
3. if the query is deemed complex, 
    a. use the `think_tool` to think and reflect. You should ideally think about:
        - what information you need to answer the user's question
        - if you have those information available
        - if you need more information, how should you collect it
        - once you have all information, how should you respond
        - what follow up's can the user come up with
        - how can you tackle those follow up's
    b. for each thought, make a single call for `think_tool`
""",
)
logger.debug(short_system_prompt.to_markdown())

# %%
chat_llm = ChatOpenAI(
    model=settings.models.nebius.tool_user,
    api_key=settings.env.NEBIUS_API_KEY,
    base_url=settings.env.NEBIUS_API_ENDPOINT,
    max_completion_tokens=8192,
    temperature=0.0,
    top_p=0.7,
)


# %%
def ask_node(state: AgentState) -> AgentState | Dict:
    full_context = (
        [SystemMessage(content=short_system_prompt.to_markdown())]
        + state["messages"]
        + [SystemMessage("Following are your previous thoughts")]
        + state["thoughts"]
    )
    bound_llm = bound_llm = chat_llm.bind_tools(
        tools=[
            think_tool,
        ],
        strict=True,
        tool_choice="auto",
        parallel_tool_calls=True,
    )
    response = bound_llm.invoke(full_context)
    thoughts = []
    if response.tool_calls:
        for tool_call in response.tool_calls:
            if tool_call["name"] == "think_tool":
                thoughts.append(tool_call["args"]["reflection"])
    return {"messages": [response], "thoughts": thoughts}


tool_node = ToolNode([think_tool])


def tool_or_end_router(state: AgentState) -> Literal["tool", "end"]:
    last_message: AIMessage = state["messages"][-1]
    # if there are no tool calls then go to end
    # else go back to tools
    if last_message.tool_calls:
        return "tool"
    else:
        return "end"


graph = StateGraph(AgentState)
graph.add_node("ask", ask_node)
graph.add_node("tool", tool_node)
graph.add_edge(START, "ask")
graph.add_edge("tool", "ask")
graph.add_conditional_edges("ask", tool_or_end_router, {"tool": "tool", "end": END})
agent = graph.compile()

# %%
msg = """
🧩 The Two Doors Riddle

You are standing in front of two closed doors.

One door leads to treasure.
The other door leads to danger.

There are two guards:

• One guard always tells the truth.
• One guard always lies.

You do NOT know which guard is which.
Each guard stands in front of one door.

You are allowed to ask ONLY ONE yes/no question to ONLY ONE guard.

After asking the question, you must choose a door.

Question:
What question should you ask to guarantee choosing the treasure door?

(hint: use the think_tool to think and critique your answer. Use it maximum of 10 times.)"""
printer.user(msg)
all_msgs = []
all_tokens = []
for chunk in agent.stream(
    {"messages": [HumanMessage(msg)]},
    stream_mode="updates",
):
    for step, data in chunk.items():
        messages = data.get("messages", [])
        for m in messages:
            if isinstance(m, AIMessage):
                # Tool calls interrupt streaming
                if m.tool_calls:
                    printer._ensure_stream_closed()
                    for t in m.tool_calls:
                        printer.tool(t["name"], status="running", args=t["args"])
                # Sometimes final structured content arrives here
                # (only print if not already streamed token-wise)
                if m.content and not m.tool_calls:
                    # Only print if stream wasn't used
                    if not printer._ai_stream_active:
                        printer.ai(m.content)
                # Usage metadata normally arrives here
                if m.usage_metadata:
                    printer._ensure_stream_closed()
                    printer.token_usage(
                        m.usage_metadata.get("input_tokens", 0),
                        m.usage_metadata.get("output_tokens", 0),
                        latency=0,
                    )
            elif isinstance(m, ToolMessage):
                printer.tool(
                    m.name,
                    status="finished",
                )

# %%
