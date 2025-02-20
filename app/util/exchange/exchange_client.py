import ccxt.async_support as ccxt
from typing import Optional

from app.schemas.schema_exchanges import (
    MarketType,
    TradingPairInfo,
)
from app.util.exceptions import ExchangeAPIError


class ExchangeClient:
    """Client for interacting with cryptocurrency exchange APIs using CCXT"""

    def __init__(self):
        self.exchange: Optional[ccxt.Exchange] = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.exchange:
            await self.exchange.close()

    async def _init_exchange(self, exchange_id: str) -> None:
        """Initialize exchange instance"""
        if not hasattr(ccxt, exchange_id):
            raise ExchangeAPIError(f"Exchange {exchange_id} is not supported by CCXT")

        exchange_class = getattr(ccxt, exchange_id)
        self.exchange = exchange_class(
            {
                "enableRateLimit": True,  # Enable built-in rate limiter
            }
        )

    async def get_trading_pairs(self, exchange_id: str) -> list[TradingPairInfo]:
        """Fetch trading pairs from any supported exchange"""
        try:
            await self._init_exchange(exchange_id)

            # Load markets
            markets = await self.exchange.load_markets()

            pairs = []
            for symbol, market in markets.items():
                if market.get("spot"):
                    market_type = MarketType.SPOT
                elif market.get("future") or market.get("swap"):
                    market_type = MarketType.FUTURES
                elif market.get("margin"):
                    market_type = MarketType.MARGIN

                # Create trading pair info
                pair = TradingPairInfo(
                    symbol=market["symbol"],  # Contains delimiter (e.g., 'ETH/BTC')
                    market_type=market_type,
                    # Status
                    active=market.get("active", False),
                    status=market.get("info", {}).get("status", "UNKNOWN"),
                )
                pairs.append(pair)

            return pairs

        except ccxt.BaseError as e:
            raise ExchangeAPIError(f"CCXT error: {str(e)}")
        finally:
            if self.exchange:
                await self.exchange.close()
