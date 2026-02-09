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
