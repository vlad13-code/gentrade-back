from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.runnables import (
    RunnableConfig,
    RunnableLambda,
    RunnableSerializable,
)
from langgraph.graph import END, StateGraph
from langgraph.store.base import BaseStore
from langgraph.checkpoint.memory import MemorySaver

from app.agents.main.schemas import RouterResponse, AgentState, get_agent_descriptions
from app.agents.strategy.graph_strategy import strategy_builder
from app.agents.main.prompts.base import router_instructions
from app.agents.model import model


async def main_router(state: AgentState) -> RouterResponse:
    structured_model = model.with_structured_output(RouterResponse)

    system_message = router_instructions.format(agents=get_agent_descriptions())
    router_response = await structured_model.ainvoke(
        [SystemMessage(content=system_message)]
    )

    return {"agent": router_response.agent}


def get_model() -> RunnableSerializable[AgentState, AIMessage]:
    preprocessor = RunnableLambda(
        lambda state: state["messages"],
        name="StateModifier",
    )
    return preprocessor | model


async def acall_model(
    state: AgentState, config: RunnableConfig, *, store: BaseStore
) -> AgentState:
    model_runnable = get_model()
    response = await model_runnable.ainvoke(state, config)

    if state["is_last_step"] and response.tool_calls:
        return {
            "messages": [
                AIMessage(
                    id=response.id,
                    content="Sorry, need more steps to process this request.",
                )
            ]
        }
    return {"messages": [response]}


agent = StateGraph(AgentState)
agent.add_node("router", main_router)
agent.add_node("model", acall_model)
agent.add_node("strategy", strategy_builder.compile())
agent.set_entry_point("router")
agent.add_conditional_edges(
    "router", lambda route: route["agent"], {"model": "model", "strategy": "strategy"}
)
agent.add_edge("model", END)
agent.add_edge("strategy", END)

graph_main = agent.compile(checkpointer=MemorySaver())


if __name__ == "__main__":
    import asyncio

    from dotenv import load_dotenv
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

    load_dotenv()

    async def main() -> None:

        inputs = {
            "messages": [HumanMessage(content="Hey")],
            "input": [
                HumanMessage(content="Hey"),
            ],
        }

        from uuid import uuid4

        # async for event in graph_main.astream_events(
        #     inputs,
        #     RunnableConfig(configurable={"thread_id": uuid4()}),
        #     version="v2",
        #     # stream_mode="values",
        # ):
        #     print(event)
        #     print("\n")

        config = RunnableConfig(configurable={"thread_id": uuid4()})
        result = await graph_main.ainvoke(
            inputs,
            config=config,
        )

        state = await graph_main.aget_state(config)

        result["messages"][-1].pretty_print()

        # Draw the agent graph as png
        # requires:
        # brew install graphviz
        # export CFLAGS="-I $(brew --prefix graphviz)/include"
        # export LDFLAGS="-L $(brew --prefix graphviz)/lib"
        # pip install pygraphviz

        # graph_main.get_graph(xray=1).draw_mermaid_png(output_file_path="graph_main.png")

        # from pprint import pprint

        # pprint(
        #     graph_main.get_state(
        #         {"configurable": {"thread_id": "989772d1-eeca-4d1c-8abe-9351953075eb"}}
        #     ).values
        # )

    asyncio.run(main())
