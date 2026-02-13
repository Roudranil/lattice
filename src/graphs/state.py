from typing import List, Literal

from langgraph.graph import MessagesState


class AgentState(MessagesState):
    mode: Literal["ask", "planning", "execution"]
    thoughts: List[str]
