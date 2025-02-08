from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, StateGraph
from langgraph.store.base import BaseStore
from langgraph.checkpoint.memory import MemorySaver

from app.agents.main.schemas import RouterResponse, AgentState, get_agent_descriptions
from app.agents.strategy.graph_strategy_draft import strategy_builder
from app.agents.main.prompts.base import router_instructions
from app.agents.model import model
from app.agents.utils.logging import (
    log_agent_step,
    log_agent_prompt,
    log_agent_response,
)


async def main_router(state: AgentState) -> RouterResponse:
    log_agent_step(
        "main_router",
        "start",
        input_data={
            "messages": [m.content for m in state["messages"]],
            "is_last_step": state.get("is_last_step", False),
        },
    )

    structured_model = model.with_structured_output(RouterResponse)

    system_message = router_instructions.format(agents=get_agent_descriptions())
    log_agent_prompt(
        "main_router",
        "router_prompt",
        router_instructions,
        {"agents": get_agent_descriptions()},
    )

    router_response = await structured_model.ainvoke(
        [SystemMessage(content=system_message)] + state["messages"]
    )

    log_agent_step(
        "main_router", "complete", output_data={"selected_agent": router_response.agent}
    )

    return {"agent": router_response.agent}


async def acall_model(
    state: AgentState, config: RunnableConfig, *, store: BaseStore
) -> AgentState:
    log_agent_step(
        "model",
        "start",
        input_data={
            "messages": [m.content for m in state["messages"]],
            "is_last_step": state.get("is_last_step", False),
        },
    )

    response = await model.ainvoke(state["messages"], config)

    log_agent_response(
        "model",
        "model_response",
        response.content,
        {
            "completion_tokens": getattr(response, "completion_tokens", None),
            "prompt_tokens": getattr(response, "prompt_tokens", None),
            "total_tokens": getattr(response, "total_tokens", None),
        },
    )

    if state["is_last_step"] and response.tool_calls:
        log_agent_step(
            "model", "error", error=Exception("Need more steps to process this request")
        )
        return {
            "messages": [
                AIMessage(
                    id=response.id,
                    content="Sorry, need more steps to process this request.",
                )
            ]
        }

    log_agent_step(
        "model",
        "complete",
        output_data={
            "response_id": response.id,
            "has_tool_calls": bool(response.tool_calls),
        },
    )
    return {"messages": [response]}


agent = StateGraph(AgentState)
agent.add_node("router", main_router)
agent.add_node("model", acall_model)
agent.add_node("strategy_draft", strategy_builder.compile())
agent.set_entry_point("router")
agent.add_conditional_edges(
    "router",
    lambda route: route["agent"],
    {"model": "model", "strategy_draft": "strategy_draft"},
)
agent.add_edge("model", END)
agent.add_edge("strategy_draft", END)

graph_main = agent.compile(checkpointer=MemorySaver())


if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv

    load_dotenv()

    async def main() -> None:

        # inputs = {
        #     "messages": [HumanMessage(content="Hey")],
        #     "input": [
        #         HumanMessage(content="Hey"),
        #     ],
        # }

        # from uuid import uuid4

        # async for event in graph_main.astream_events(
        #     inputs,
        #     RunnableConfig(configurable={"thread_id": uuid4()}),
        #     version="v2",
        #     # stream_mode="values",
        # ):
        #     print(event)
        #     print("\n")

        # config = RunnableConfig(configurable={"thread_id": uuid4()})
        # result = await graph_main.ainvoke(
        #     inputs,
        #     config=config,
        # )

        # state = await graph_main.aget_state(config)

        # result["messages"][-1].pretty_print()

        # Draw the agent graph as png
        # requires:
        # brew install graphviz
        # export CFLAGS="-I $(brew --prefix graphviz)/include"
        # export LDFLAGS="-L $(brew --prefix graphviz)/lib"
        # pip install pygraphviz

        graph_main.get_graph(xray=1).draw_mermaid_png(output_file_path="graph_main.png")

        # from pprint import pprint

        # pprint(
        #     graph_main.get_state(
        #         {"configurable": {"thread_id": "989772d1-eeca-4d1c-8abe-9351953075eb"}}
        #     ).values
        # )

    asyncio.run(main())
