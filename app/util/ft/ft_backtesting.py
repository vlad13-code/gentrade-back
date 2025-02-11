import os
import uuid

from app.util.ft.verification.log_parser import LogSummary
from app.util.logger import setup_logger
from .ft_base import FTBase
from app.util.exceptions import PickleableDockerException
from .ft_market_data import FTMarketData


class FTBacktesting(FTBase):
    def __init__(self, clerk_id: str):
        """
        Initialize backtesting functionality.

        Args:
            clerk_id (str): The user's Clerk ID.
        """
        super().__init__(clerk_id)
        self.ensure_user_dir_exists()
        self.logger = setup_logger("ft.backtesting")

    def run_backtest(self, strategy_class_name: str, date_range: str) -> str:
        """
        Runs a freqtrade backtest in Docker and returns the path to the results file.

        Args:
            strategy_class_name (str): Name of the strategy class.
            date_range (str): Date range in freqtrade format (e.g. "20200101-20200201").

        Returns:
            str: Path to the results file.

        Raises:
            PickleableDockerException: If the backtest fails or results are not found.
            ValueError: If input parameters are invalid.
        """
        output_filename = f"backtest_{uuid.uuid4()}.json"
        result_path = os.path.join(
            self.user_dir, "user_data", "backtest_results", output_filename
        )

        self.logger.info(
            "Starting backtest",
            extra={
                "data": {
                    "strategy": strategy_class_name,
                    "date_range": date_range,
                    "result_path": result_path,
                }
            },
        )

        if not strategy_class_name:
            self.logger.error(
                "Invalid strategy name",
                extra={"data": {"strategy": strategy_class_name}},
            )
            raise ValueError("Strategy class name cannot be empty")

        if not date_range:
            self.logger.error(
                "Invalid date range", extra={"data": {"date_range": date_range}}
            )
            raise ValueError("Date range cannot be empty")

        try:
            log_summary: LogSummary = self.run_docker_command(
                "freqtrade",
                [
                    "backtesting",
                    "--datadir",
                    "/freqtrade/common_data",
                    "--strategy",
                    strategy_class_name,
                    "--timerange",
                    date_range,
                    "--export",
                    "trades",
                    "--export-filename",
                    output_filename,
                ],
            )

            if log_summary.warnings:
                self.logger.warning(
                    f"Backtest finished with {log_summary.total_warnings} warnings listed below"
                )
                for warning in log_summary.warnings:
                    self.logger.warning(
                        f"{warning.name}: {warning.message}",
                        extra={
                            "data": {
                                "name": warning.name,
                                "timestamp": warning.timestamp,
                            }
                        },
                    )

            if not os.path.exists(result_path):
                self.logger.error(
                    "Backtest finished without errors but no result file was created",
                    extra={
                        "data": {
                            "result_path": result_path,
                            "strategy": strategy_class_name,
                            "date_range": date_range,
                        }
                    },
                )
        except PickleableDockerException as e:
            raise e

        self.logger.info(
            "Backtest completed successfully",
            extra={
                "data": {
                    "strategy": strategy_class_name,
                    "date_range": date_range,
                    "result_path": result_path,
                    "warning_count": len(log_summary.warnings),
                }
            },
        )

        return result_path

    def cleanup_results(self, result_path: str) -> None:
        """
        Clean up backtest result files.

        Args:
            result_path (str): Path to the result file to clean up.

        Raises:
            OSError: If file deletion fails.
        """
        self.logger.info(
            "Cleaning up backtest results", extra={"data": {"result_path": result_path}}
        )
        try:
            if os.path.exists(result_path):
                os.remove(result_path)
                self.logger.info(
                    "Result file deleted", extra={"data": {"result_path": result_path}}
                )
        except OSError as e:
            self.logger.error(
                "Failed to clean up result file",
                extra={
                    "data": {
                        "result_path": result_path,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    }
                },
            )
            raise


if __name__ == "__main__":
    ft_market_data = FTMarketData("2oFuvIYD6fvQwokCEb61laEDjoM")
    ft_market_data.download(
        pairs=["BTC/USDT:USDT", "ETH/USDT:USDT", "XRP/USDT:USDT"],
        timeframes=["1h"],
        date_range="20250128-20250205",
        trading_mode="futures",
    )
    try:
        ft_backtesting = FTBacktesting("2oFuvIYD6fvQwokCEb61laEDjoM")
        ft_backtesting.run_backtest("SampleStrategy", "20250128-20250205")
    except PickleableDockerException as e:
        pass
