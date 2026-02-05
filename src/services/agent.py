from typing import Any, Dict, List, Optional

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    convert_to_openai_messages,
)

from src.utils.logger import create_logger

logger = create_logger(name="AgentService", path="./logs", filename="agent.log")


def convert_to_langchain(messages: List[Dict[str, Any]]) -> List[BaseMessage]:
    """convert api message dicts to langchain messages"""
    mapping = {
        "system": SystemMessage,
        "user": HumanMessage,
        "assistant": AIMessage,
    }
    result = []
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        msg_class = mapping.get(role, HumanMessage)
        result.append(msg_class(content=content))
    return result


def invoke_agent(
    messages: List[Dict[str, Any]], thread_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    invoke the langgraph agent with messages
    if thread_id is provided, uses checkpointer for persistence
    """
    # import here to avoid circular deps and allow main.py to be the source of truth
    from main import agent

    langchain_messages = convert_to_langchain(messages)
    config = {}
    if thread_id:
        config = {"configurable": {"thread_id": thread_id}}

    logger.debug(f"invoking agent with {len(messages)} messages, thread={thread_id}")
    result = agent.invoke({"messages": langchain_messages}, config=config)

    output_messages = convert_to_openai_messages(result.get("messages", []))
    logger.debug(f"agent returned {len(output_messages)} messages")
    return {"messages": output_messages}


def get_thread_state(thread_id: str) -> Dict[str, Any]:
    """get current state for a thread from the checkpointer"""
    from main import agent

    config = {"configurable": {"thread_id": thread_id}}
    state = agent.get_state(config)

    # state.values contains the current state dict
    values = state.values if state.values else {}
    next_nodes = list(state.next) if state.next else []

    # convert messages if present
    if "messages" in values:
        values = {"messages": convert_to_openai_messages(values["messages"])}

    return {"values": values, "next": next_nodes}
