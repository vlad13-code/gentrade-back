from typing import Annotated
from langchain_core.tools import BaseTool, tool
from langgraph.prebuilt import InjectedState


def strategy_draft_output_tool_func(state: Annotated[dict, InjectedState]) -> str:
    """
    Generates a basic trading strategy.

    This function creates a basic trading strategy in Python. The strategy
    includes the necessary code to define the strategy and its parameters.

    Returns:
        dict: The strategy name and description.
    """

    return state["strategy_draft"].model_dump()


strategy_draft_output_tool: BaseTool = tool(strategy_draft_output_tool_func)
strategy_draft_output_tool.name = "StrategyDraftOutputTool"
