from langgraph.graph import START, END, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage

from app.agents.strategy.schemas import GenerateStrategyCodeState, StrategyCode
from app.agents.strategy.prompts.strategy_code import strategy_code_instructions
from app.agents.model import model
from app.agents.utils.logging import (
    log_agent_step,
    log_agent_prompt,
    log_agent_response,
)


async def generate_strategy_code(state: GenerateStrategyCodeState):
    """Generate FreqTrade strategy code from a strategy draft"""
    draft = state["strategy_draft"]

    log_agent_step(
        "strategy_generator",
        "start",
        input_data={
            "strategy_name": draft.name,
            "timeframe": draft.timeframe,
            "can_short": draft.can_short,
            "indicator_count": len(draft.indicators),
            "entry_signal_count": len(draft.entry_signals),
            "exit_signal_count": len(draft.exit_signals),
        },
    )

    system_prompt = strategy_code_instructions.format(
        name=draft.name,
        description=draft.description,
        indicators=draft.indicators,
        entry_signals=draft.entry_signals,
        exit_signals=draft.exit_signals,
        minimal_roi=draft.minimal_roi,
        stoploss=draft.stoploss,
        timeframe=draft.timeframe,
        can_short=draft.can_short,
    )

    log_agent_prompt(
        "strategy_generator",
        "strategy_code_prompt",
        strategy_code_instructions,
        {
            "name": draft.name,
            "description": draft.description,
            "indicators": draft.indicators,
            "entry_signals": draft.entry_signals,
            "exit_signals": draft.exit_signals,
            "minimal_roi": draft.minimal_roi,
            "stoploss": draft.stoploss,
            "timeframe": draft.timeframe,
            "can_short": draft.can_short,
        },
    )

    structured_model = model.with_structured_output(StrategyCode)
    strategy = await structured_model.ainvoke([SystemMessage(content=system_prompt)])

    log_agent_response(
        "strategy_generator",
        "strategy_code_response",
        strategy.code,
        {
            "completion_tokens": getattr(strategy, "completion_tokens", None),
            "prompt_tokens": getattr(strategy, "prompt_tokens", None),
            "total_tokens": getattr(strategy, "total_tokens", None),
        },
    )

    log_agent_step(
        "strategy_generator",
        "complete",
        output_data={"strategy_name": draft.name, "code_length": len(strategy.code)},
    )

    return {
        "strategy_code": strategy,
        "strategy_draft": draft,
    }


# Build the graph
strategy_generator = StateGraph(GenerateStrategyCodeState)

# Add nodes
strategy_generator.add_node("generate_strategy_code", generate_strategy_code)

# Add edges
strategy_generator.add_edge(START, "generate_strategy_code")
strategy_generator.add_edge("generate_strategy_code", END)

# Compile the graph
memory = MemorySaver()
graph_strategy_code = strategy_generator.compile()

if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv

    load_dotenv()

    async def main() -> None:
        graph_strategy_code.get_graph(xray=1).draw_mermaid_png(
            output_file_path="graph_strategy.png"
        )

    asyncio.run(main())
