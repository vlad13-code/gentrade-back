from typing import Literal

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import (
    RunnableConfig,
    RunnableLambda,
    RunnableSerializable,
)
from langchain_openai import ChatOpenAI
from langgraph.graph import END, MessagesState, StateGraph
from langgraph.managed import IsLastStep
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.store.base import BaseStore
from langgraph.checkpoint.memory import MemorySaver

from app.agents.main.prompts.base import instructions
from app.agents.main.tools.calculator import calculator
from app.config import settings


class AgentState(MessagesState, total=False):
    input: list[HumanMessage | AIMessage | SystemMessage]
    is_last_step: IsLastStep


# NOTE: models with streaming=True will send tokens as they are generated
# if the /stream endpoint is called with stream_tokens=True (the default)
models: dict[str, BaseChatModel] = {}
if settings.OPENAI_API_KEY is not None:
    models["gpt-4o-mini"] = ChatOpenAI(
        model="gpt-4o-mini", temperature=0.0, streaming=True
    )

if not models:
    print("No LLM available. Please set API keys to enable at least one LLM.")
    if settings.MODE == "dev":
        print("FastAPI initialized failed. Please use Ctrl + C to exit uvicorn.")
    exit(1)


tools = [calculator]


def wrap_model(model: BaseChatModel) -> RunnableSerializable[AgentState, AIMessage]:
    model = model.bind_tools(tools)
    preprocessor = RunnableLambda(
        lambda state: [SystemMessage(content=instructions)]
        + state["messages"]
        + state["input"],
        name="StateModifier",
    )
    return preprocessor | model


async def acall_model(
    state: AgentState, config: RunnableConfig, *, store: BaseStore
) -> AgentState:
    m = models[config["configurable"].get("model", "gpt-4o-mini")]
    model_runnable = wrap_model(m)
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


# Define the graph
agent = StateGraph(AgentState)
agent.add_node("model", acall_model)
agent.add_node("tools", ToolNode(tools))
agent.add_conditional_edges(
    "model",
    tools_condition,
)
agent.set_entry_point("model")
# agent.add_edge("tools", "model")


# After "model", if there are tool calls, run "tools". Otherwise END.
def pending_tool_calls(state: AgentState) -> Literal["tools", "done"]:
    last_message = state["messages"][-1]
    if not isinstance(last_message, AIMessage):
        raise TypeError(f"Expected AIMessage, got {type(last_message)}")
    if last_message.tool_calls:
        return "tools"
    return "done"


agent.add_conditional_edges(
    "model", pending_tool_calls, {"tools": "tools", "done": END}
)
agent.add_edge("model", END)


graph_main = agent.compile(checkpointer=MemorySaver())


if __name__ == "__main__":
    import asyncio
    from uuid import uuid4

    from dotenv import load_dotenv

    load_dotenv()

    async def main() -> None:
        from IPython.display import Image, display

        # inputs = {"messages": [("user", "Find me a recipe for chocolate chip cookies")]}
        # result = await graph_main.ainvoke(
        #     inputs,
        #     config=RunnableConfig(configurable={"thread_id": uuid4()}),
        # )
        # result["messages"][-1].pretty_print()

        # Draw the agent graph as png
        # requires:
        # brew install graphviz
        # export CFLAGS="-I $(brew --prefix graphviz)/include"
        # export LDFLAGS="-L $(brew --prefix graphviz)/lib"
        # pip install pygraphviz
        #
        graph_main.get_graph(xray=1).draw_mermaid_png(output_file_path="graph_main.png")

    asyncio.run(main())
