from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class StrategyDraftSchemaAdd(BaseModel):
    name: str = Field(description="Unique strategy name.")
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

    chat_id: Optional[int] = Field(description="Chat ID.")
    tool_call_id: Optional[str] = Field(description="Tool call ID.")


class StrategySchemaAdd(BaseModel):
    name: str
    code: str
    file: str
    user_id: int
    draft: dict
    chat_id: int


class StrategySchema(BaseModel):
    id: int
    name: str
    draft: StrategyDraftSchemaAdd
    createdAt: datetime
    updatedAt: datetime
