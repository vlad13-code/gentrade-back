from fastapi import HTTPException, status
import ccxt.async_support as ccxt
import asyncio
from app.schemas.schema_exchanges import (
    TradingPairInfo,
    MarketType,
)
from app.util.exchange.exchange_client import ExchangeClient
from app.util.logger import setup_logger

logger = setup_logger("services.exchanges")


class ExchangeService:
    """Service for managing exchange-related operations"""

    # Get list of supported exchanges from CCXT
    SUPPORTED_EXCHANGES = set(ccxt.exchanges)

    @staticmethod
    def _validate_exchange(exchange_id: str) -> None:
        """Validate if the exchange is supported"""
        if exchange_id not in ExchangeService.SUPPORTED_EXCHANGES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Exchange {exchange_id} is not supported. Please use one of the supported exchanges.",
            )

    def _filter_by_market_type(
        self, pairs: list[TradingPairInfo], market_type: MarketType
    ) -> list[TradingPairInfo]:
        """Filter pairs by market type"""

        return [
            pair for pair in pairs if pair.market_type == market_type and pair.active
        ]

    async def get_trading_pairs(
        self, exchange_id: str, market_type: MarketType
    ) -> list[TradingPairInfo]:
        """Get trading pairs for a specific exchange"""
        self._validate_exchange(exchange_id)

        async with ExchangeClient() as client:
            try:
                pairs = await client.get_trading_pairs(exchange_id)

                # Apply market type filter
                filtered_pairs = self._filter_by_market_type(pairs, market_type)

                return filtered_pairs
            except Exception as e:
                logger.error(f"Error fetching trading pairs: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error fetching trading pairs: {str(e)}",
                )


async def test():
    service = ExchangeService()
    pairs = await service.get_trading_pairs("binance")
    print(pairs)


if __name__ == "__main__":
    asyncio.run(test())
