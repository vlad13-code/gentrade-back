import logging
from typing import List
from .ft_base import FTBase


class FTMarketData(FTBase):
    def __init__(self, user_id: str):
        """
        Initialize market data management functionality.

        Args:
            user_id (str): The user's ID.
        """
        super().__init__(user_id)
        self.ensure_user_dir_exists()

    def download(
        self,
        pairs: List[str],
        timeframes: List[str],
        date_range: str,
        exchange: str = "binance",
    ) -> None:
        """
        Download market data for specified pairs and timeframes.

        Args:
            pairs (List[str]): List of trading pairs (e.g. ["BTC/USDT", "ETH/USDT"]).
            timeframes (List[str]): List of timeframes (e.g. ["1m", "5m", "1h"]).
            date_range (str): Date range in freqtrade format (e.g. "20200101-20200201").
            exchange (str, optional): Exchange to download from. Defaults to "binance".

        Raises:
            ValueError: If input parameters are invalid.
            PickleableDockerException: If the data download fails.
        """
        if not pairs:
            raise ValueError("Pairs list cannot be empty")
        if not timeframes:
            raise ValueError("Timeframes list cannot be empty")
        if not date_range:
            raise ValueError("Date range cannot be empty")

        pairs_str = " ".join(pairs)
        timeframes_str = " ".join(timeframes)
        user_dir = self._get_user_data_directory()

        try:
            self.run_docker_command(
                "freqtrade",
                [
                    "download-data",
                    "--userdir",
                    user_dir,
                    "--pairs",
                    pairs_str,
                    "--timeframes",
                    timeframes_str,
                    "--timerange",
                    date_range,
                    "--exchange",
                    exchange,
                    "--data-format-ohlcv",
                    "json",
                ],
            )
        except Exception as e:
            logging.error(f"Failed to download market data: {e}", exc_info=True)
            raise
