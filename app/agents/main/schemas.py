from typing import Literal

from pydantic import BaseModel
from langgraph.graph import MessagesState
from langgraph.managed import IsLastStep

routed_agents = {
    "strategy_draft": "Designed for creating trading strategies based on user input",
    "model": "Designed for using the chat model to answer questions",
}

AgentType = Literal["strategy_draft", "model"]


class RouterResponse(BaseModel):
    agent: AgentType


class AgentState(MessagesState, total=False):
    is_last_step: IsLastStep
    agent: AgentType


def get_agent_descriptions():
    return "\n".join(
        f"{name} - {description}" for name, description in routed_agents.items()
    )
