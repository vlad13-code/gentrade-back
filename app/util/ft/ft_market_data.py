import logging
from typing import List

from app.util.logger import setup_logger
from .ft_base import FTBase
from .verification.data_download_verifier import DataDownloadVerifier
from .verification.schemas import VerificationResult


class FTMarketData(FTBase):
    def __init__(self, user_id: str):
        """
        Initialize market data management functionality.

        Args:
            user_id (str): The user's ID.
        """
        super().__init__(user_id)
        self.ensure_user_dir_exists()
        self.verifier = DataDownloadVerifier(base_dir="ft_userdata")
        self.logger = setup_logger(__name__)

    def _generate_expected_files(
        self, pairs: List[str], timeframes: List[str], trading_mode: str = "futures"
    ) -> List[str]:
        """
        Generate list of expected file paths based on pairs and timeframes.

        Args:
            pairs (List[str]): List of trading pairs
            timeframes (List[str]): List of timeframes
            trading_mode (str, optional): Trading mode (futures, spot). Defaults to "futures".

        Returns:
            List[str]: List of expected file paths
        """
        expected_files = []
        for pair in pairs:
            # Replace / with _ and handle :USDT suffix
            formatted_pair = pair.replace("/", "_").replace(":", "_")

            for tf in timeframes:
                file_name = f"_common_data/{trading_mode}/{formatted_pair}-{tf}-{trading_mode}.feather"
                expected_files.append(file_name)

                # For futures mode, also check for mark and funding rate files
                if trading_mode == "futures":  # Funding rate is in 8h timeframe
                    mark_file = (
                        f"_common_data/{trading_mode}/{formatted_pair}-8h-mark.feather"
                    )
                    funding_file = f"_common_data/{trading_mode}/{formatted_pair}-8h-funding_rate.feather"
                    expected_files.append(mark_file)
                    expected_files.append(funding_file)

        return expected_files

    def download(
        self,
        pairs: List[str],
        timeframes: List[str],
        date_range: str,
        exchange: str = "binance",
        trading_mode: str = "futures",
    ) -> VerificationResult:
        """
        Download market data for specified pairs and timeframes.

        Args:
            pairs (List[str]): List of trading pairs (e.g. ["BTC/USDT", "ETH/USDT"]).
            timeframes (List[str]): List of timeframes (e.g. ["1m", "5m", "1h"]).
            date_range (str): Date range in freqtrade format (e.g. "20200101-20200201").
            exchange (str, optional): Exchange to download from. Defaults to "binance".
            trading_mode (str, optional): Trading mode (futures, spot). Defaults to "futures".

        Returns:
            VerificationResult: Result of the download verification

        Raises:
            ValueError: If input parameters are invalid.
            PickleableDockerException: If the data download fails.
        """
        self.logger.debug(
            "Starting market data download",
            extra={
                "user_id": self.user_id,
                "pairs": pairs,
                "timeframes": timeframes,
                "date_range": date_range,
                "exchange": exchange,
                "trading_mode": trading_mode,
            },
        )

        # Input validation
        if not pairs:
            self.logger.error(
                "Pairs list cannot be empty",
                extra={"user_id": self.user_id, "error_type": "ValueError"},
            )
            raise ValueError("Pairs list cannot be empty")
        if not timeframes:
            self.logger.error(
                "Timeframes list cannot be empty",
                extra={"user_id": self.user_id, "error_type": "ValueError"},
            )
            raise ValueError("Timeframes list cannot be empty")
        if not date_range:
            self.logger.error(
                "Date range cannot be empty",
                extra={"user_id": self.user_id, "error_type": "ValueError"},
            )
            raise ValueError("Date range cannot be empty")

        # Generate expected file paths
        expected_files = self._generate_expected_files(pairs, timeframes, trading_mode)

        # Check for already downloaded files
        verification_result = self.verifier.verify_download(
            expected_files=expected_files,
            date_range=date_range,
            timeframes=timeframes,
        )
        if verification_result.success:
            self.logger.info(
                "Market data already downloaded, skipping download",
                extra={
                    "user_id": self.user_id,
                    "verified_files": verification_result.verified_files,
                    "verification_time": verification_result.verification_time,
                },
            )
            return verification_result

        try:
            docker_command = [
                "download-data",
                "--datadir",
                "/freqtrade/common_data",
                "--pairs",
                *pairs,
                "--timeframes",
                *timeframes,
                "--timerange",
                date_range,
                "--exchange",
                exchange,
                "--trading-mode",
                trading_mode,
            ]

            self.logger.debug(
                "Executing Docker command for data download",
                extra={"user_id": self.user_id, "docker_command": docker_command},
            )

            # Execute Docker command
            log_summary = self.run_docker_command("freqtrade", docker_command)

            self.logger.debug(
                "Docker command completed",
                extra={
                    "errors": log_summary.errors,
                    "warnings": log_summary.warnings,
                },
            )

            # Verify the download
            verification_result = self.verifier.verify_download(
                docker_result=log_summary,
                expected_files=expected_files,
                date_range=date_range,
                timeframes=timeframes,
            )

            if not verification_result.success:
                self.logger.error(
                    "Data download verification failed",
                    extra={
                        "user_id": self.user_id,
                        "error_type": verification_result.error_type,
                        "error_message": verification_result.error_message,
                        "verified_files": verification_result.verified_files,
                        "verification_time": verification_result.verification_time,
                    },
                )
            else:
                self.logger.info(
                    "Data download verification succeeded",
                    extra={
                        "user_id": self.user_id,
                        "verified_files": verification_result.verified_files,
                        "verification_time": verification_result.verification_time,
                    },
                )

            return verification_result

        except Exception as e:
            self.logger.error(
                "Failed to download market data",
                extra={
                    "user_id": self.user_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "pairs": pairs,
                    "timeframes": timeframes,
                    "date_range": date_range,
                    "exchange": exchange,
                    "trading_mode": trading_mode,
                },
                exc_info=True,
            )
            raise


if __name__ == "__main__":
    import logging

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%d%b'%y %H:%M:%S",
    )

    ft_market_data = FTMarketData("2oFuvIYD6fvQwokCEb61laEDjoM")
    ft_market_data.download(
        pairs=["BTC/USDT:USDT", "ETH/USDT:USDT", "XRP/USDT:USDT"],
        timeframes=["1h", "4h"],
        date_range="20250128-20250205",
        trading_mode="futures",
    )
