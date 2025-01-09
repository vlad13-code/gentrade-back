from pydantic import BaseModel, Field
from langgraph.graph import MessagesState


class StrategyDraft(BaseModel):
    name: str = Field(description="Unique strategy name.")
    file: str = Field(description="Python file containing the strategy.")
    description: str = Field(
        description="Detailed strategy description, including indicators and logic."
    )
    indicators: str = Field(
        description="List of technical indicators and their settings."
    )
    entry_signals: str = Field(
        description="Text description of conditions and logic for entry signals."
    )
    exit_signals: str = Field(
        description="Text description of conditions and logic for exit signals."
    )
    minimal_roi: str = Field(description="Minimal ROI in percentage.")
    stoploss: str = Field(description="Stoploss percentage.")
    timeframe: str = Field(description="Strategy timeframe, e.g., '1m', '5m'.")
    can_short: bool = Field(description="Indicates if shorting is supported.")


class CreateStrategyDraftState(MessagesState):
    input: str
    feedback: str
    strategy_draft: StrategyDraft


class StrategyCode(BaseModel):
    code: str = Field(description="The complete Python code for the FreqTrade strategy")


class GenerateStrategyCodeState(MessagesState):
    """State for strategy generation graph"""

    strategy_draft: StrategyDraft
    strategy_code: StrategyCode
