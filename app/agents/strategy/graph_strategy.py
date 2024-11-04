from typing import List
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from langgraph.graph import START, END, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from app.agents.strategy.prompts.base import strategy_instructions
from app.agents.model import model


class Strategy(BaseModel):
    name: str = Field(description="The name of the strategy")
    file: str = Field(description="Strategy python file filename")
    code: str = Field(description="Python code for the strategy")
    description: str = Field(description="Description of the strategy")


class CreateStrategyState(TypedDict):
    input: str
    feedback: str
    strategy: Strategy


async def create_strategy(state: CreateStrategyState):
    """Create a strategy"""

    feedback = state.get("feedback", "")
    human_prompt = state["input"]

    structured_model = model.with_structured_output(Strategy)

    system_message = strategy_instructions.format(human_feedback=feedback)

    strategy = await structured_model.ainvoke(
        [SystemMessage(content=system_message)] + [HumanMessage(content=human_prompt)]
    )

    return {"strategy": strategy}


def human_feedback(state: CreateStrategyState):
    """No-op node that should be interrupted on"""
    pass


def should_continue(state: CreateStrategyState):
    """Return the next node to execute"""

    feedback = state.get("feedback", None)
    if feedback:
        return "create_strategy"

    return END


builder = StateGraph(CreateStrategyState)
builder.add_node("create_strategy", create_strategy)
builder.add_node("human_feedback", human_feedback)
builder.add_edge(START, "create_strategy")
builder.add_edge("create_strategy", "human_feedback")
builder.add_conditional_edges(
    "human_feedback", should_continue, ["create_strategy", END]
)

memory = MemorySaver()
graph_strategy = builder.compile(
    interrupt_before=["human_feedback"], checkpointer=memory
)

if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv
    from uuid import uuid4
    from pprint import pprint

    load_dotenv()

    async def main() -> None:
        inputs = {"input": "Create a basic trading strategy"}
        result = await graph_strategy.ainvoke(
            inputs,
            config=RunnableConfig(configurable={"thread_id": uuid4()}),
        )
        pprint(result["strategy"].code)
        # graph_strategy.get_graph(xray=1).draw_mermaid_png(
        #     output_file_path="graph_strategy.png"
        # )

    asyncio.run(main())
