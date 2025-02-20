from enum import Enum
from pydantic import BaseModel, Field


class MarketType(str, Enum):
    """Market type enumeration"""

    SPOT = "spot"
    MARGIN = "margin"
    FUTURES = "futures"


class TradingPairInfo(BaseModel):
    """Trading pair information from an exchange"""

    symbol: str = Field(
        ..., description="Trading pair symbol with delimiter (e.g., 'ETH/BTC')"
    )
    market_type: MarketType = Field(..., description="Market type of the pair")

    # Status
    active: bool = Field(..., description="Whether the market is currently active")
    status: str = Field(..., description="Market status (e.g., 'TRADING')")
