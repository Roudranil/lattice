from typing import Dict
from langchain.tools import ToolRuntime

from .utils import SkipSchema, wrap_tool_with_doc_and_error_handling


@wrap_tool_with_doc_and_error_handling
def think_tool(reflection: str, runtime: ToolRuntime) -> str:
    """Strategic reflection and thinking tool. Use your reflections to refine your next course of action. You should pass exactly one thought to this tool at a single time. To maintain a clear line of reasoning, your thought should be short and at maximum 2 - 3 simple sentences only. If you are reviewing your past thoughts with this tool, then make sure to critique your past thoughts. You should ideally think about:
    - what information you need to answer the user's question
    - if you have those information available
    - if you need more information, how should you collect it
    - once you have all information, how should you respond
    - what follow up's can the user come up with
    - how can you tackle those follow up's

    Args:
        reflection (str): Your detailed reflection on the conversation so far. Your thought should not be more than 2 sentences.

    Returns:
        str: Confirmation that reflection was recorded for decision making
    """
    return f"Reflection recorded: {reflection}"


@wrap_tool_with_doc_and_error_handling
def switch_to_ask_mode_tool(
    switch: bool, summary_for_ask_agent: str, runtime: ToolRuntime
) -> bool:
    """This tool should be used to communicate that you want to switch to ASK mode. Here is a simple flowchart to follow if you want to decide whether to use this tool:
    - has the user explicitly requested to move to planning? if yes, switch to planning.
    - have you gathered all the clarifications and informations you needed from the user to help with their research survey? if yes, switch to planning. otherwise stay in your current mode.
    - is the user asking just general questions? if yes, stay in your current mode.
    - if your current response would have been anything like "I am ready to draft the research plan", use this tool to switch mode.
    If you are unsure about anything at any point, feel free to use the `think_tool` to think and reflect or just ask the user.

    Args:
        switch (bool): Your boolean decision to switch
        summary_for_ask_agent (str): You will provide a short summary of the current conversation to the ask agent including the following information:
            - what the user wants based on the conversation so far
            - what information you have so far based on the conversation so far
            - what information you are missing to give a final answer based on the conversation so far
            - what you want to ask the user to get the missing information based on the conversation so far (this will be set as goal for the ask agent)
            - any relevant context that the ask agent should know based on the conversation so far

    Returns:
        bool: Confirmation that your decision was recorded
    """
    # does not really matter what this tool returns.
    # all it matters is that we intercept this.
    return switch


@wrap_tool_with_doc_and_error_handling
def switch_to_planning_mode_tool(
    switch: bool, summary_for_planning_agent: str, runtime: ToolRuntime
) -> bool:
    """This tool should be used to communicate that you want to switch to PLANNING mode.

    Args:
        switch (bool): Your boolean decision to switch
        summary_for_planning_agent (str): You will provide a short summary of the current conversation to the planning agent including the following information:
            - what the user wants based on the conversation so far
            - what information you have so far based on the conversation so far
            - any relevant context that the planning agent should know based on the conversation so far

    Returns:
        bool: Confirmation that your decision was recorded
    """
    # does not really matter what this tool returns.
    # all it matters is that we intercept this.
    return switch


@wrap_tool_with_doc_and_error_handling
def switch_to_execution_mode_tool(
    switch: bool, summary_for_execution_agent: str, runtime: ToolRuntime
) -> bool:
    """This tool should be used to communicate that you want to switch to EXECUTION mode.

    Args:
        switch (bool): Your boolean decision to switch
        summary_for_execution_agent (str): You will provide a short summary of the current conversation to the execution agent including the following information:
            - what the user wants based on the conversation so far
            - what information you have so far based on the conversation so far
            - any relevant context that the execution agent should know based on the conversation so far

    Returns:
        bool: Confirmation that your decision was recorded
    """
    # does not really matter what this tool returns.
    # all it matters is that we intercept this.
    return switch
