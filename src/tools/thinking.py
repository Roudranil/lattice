from typing import Dict

from .utils import SkipSchema, wrap_tool_with_doc_and_error_handling


@wrap_tool_with_doc_and_error_handling
def think_tool(reflection: str, state: SkipSchema[Dict] = None) -> str:
    """Strategic reflection and thinking tool. Use this tool to reflect on the conversation so far and what you should do next. Ask questions such as:
    - What does the user want me to do next?
    - What information do I have so far?
    - Do I have enough information to give a final answer?
    - If i am missing information, what should I ask for?

    Args:
        reflection (str): Your detailed reflection on the conversation so far. Your thought should not be more than 2 sentences.

    Returns:
        str: Confirmation that reflection was recorded for decision making
    """
    return f"Reflection recorded: {reflection}"


@wrap_tool_with_doc_and_error_handling
def switch_to_ask_mode_tool(switch: bool) -> bool:
    """This tool should be used to communicate that you want to switch to ASK mode.

    Args:
        switch (bool): Your boolean decision to switch

    Returns:
        bool: Confirmation that your decision was recorded
    """
    # does not really matter what this tool returns.
    # all it matters is that we intercept this.
    return switch


@wrap_tool_with_doc_and_error_handling
def switch_to_planning_mode_tool(switch: bool) -> bool:
    """This tool should be used to communicate that you want to switch to PLANNING mode.

    Args:
        switch (bool): Your boolean decision to switch

    Returns:
        bool: Confirmation that your decision was recorded
    """
    # does not really matter what this tool returns.
    # all it matters is that we intercept this.
    return switch


@wrap_tool_with_doc_and_error_handling
def switch_to_execution_mode_tool(switch: bool) -> bool:
    """This tool should be used to communicate that you want to switch to EXECUTION mode.

    Args:
        switch (bool): Your boolean decision to switch

    Returns:
        bool: Confirmation that your decision was recorded
    """
    # does not really matter what this tool returns.
    # all it matters is that we intercept this.
    return switch
