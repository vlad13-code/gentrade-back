from langgraph.graph import START, END, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import AIMessage, SystemMessage

from app.agents.strategy.tools.strategy_draft_output import strategy_draft_output_tool
from app.agents.strategy.schemas import CreateStrategyDraftState, StrategyDraft
from app.agents.strategy.prompts.strategy_draft import strategy_draft_instructions
from app.agents.model import model


async def create_strategy_draft(state: CreateStrategyDraftState):
    """Create a strategy draft"""

    feedback = state.get("feedback", "")
    structured_model = model.with_structured_output(StrategyDraft)

    system_message = strategy_draft_instructions.format(human_feedback=feedback)
    strategy_draft = await structured_model.ainvoke(
        [SystemMessage(content=system_message)] + state["messages"]
    )

    # Force call for outputting strategy to frontend.
    # This will initiate on_tool_start event that frontend understands
    tool_call_ai_message = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "StrategyDraftOutputTool",
                "args": {},
                "id": "strategy_draft_output_tool_call",
                "type": "tool_call",
            }
        ],
    )

    return {
        "strategy_draft": strategy_draft,
        "messages": [tool_call_ai_message],
    }


def human_feedback(state: CreateStrategyDraftState):
    """No-op node that should be interrupted on"""
    pass


def should_continue(state: CreateStrategyDraftState):
    """Return the next node to execute"""

    feedback = state.get("feedback", None)
    if feedback:
        return "create_strategy_draft"

    return END


strategy_builder = StateGraph(CreateStrategyDraftState)
strategy_builder.add_node("create_strategy_draft", create_strategy_draft)
strategy_builder.add_node("tools", ToolNode([strategy_draft_output_tool]))
strategy_builder.add_node("human_feedback", human_feedback)
strategy_builder.add_edge(START, "create_strategy_draft")
strategy_builder.add_conditional_edges(
    "create_strategy_draft",
    tools_condition,
    {"tools": "tools", END: END},
)
strategy_builder.add_edge("tools", "human_feedback")
strategy_builder.add_conditional_edges(
    "human_feedback",
    should_continue,
    {"create_strategy_draft": "create_strategy_draft", END: END},
)

memory = MemorySaver()
graph_strategy = strategy_builder.compile(
    # interrupt_before=["human_feedback"],
    checkpointer=memory
)

if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv

    load_dotenv()

    async def main() -> None:
        # from uuid import uuid4
        # from pprint import pprint
        # inputs = {"input": "Create a basic trading strategy"}
        # result = await graph_strategy.ainvoke(
        #     inputs,
        #     config=RunnableConfig(configurable={"thread_id": uuid4()}),
        # )
        # pprint(result["strategy"].code)
        graph_strategy.get_graph(xray=1).draw_mermaid_png(
            output_file_path="graph_strategy.png"
        )

    asyncio.run(main())
