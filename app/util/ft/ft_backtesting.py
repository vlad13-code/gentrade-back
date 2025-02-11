import os
import shutil
import uuid

from app.util.ft.ft_backtest_parser import FTBacktestParser
from app.util.ft.verification.log_parser import LogSummary, JsonlLogParser
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

        self.output_filename = f"backtest_{uuid.uuid4()}.json"
        self.result_path = (
            f"{self.docker_backtest_results_folder}/{self.output_filename}"
        )

    def _extract_backtest_result_name(self, log_summary: LogSummary) -> str | None:
        """
        Extract the backtest result name from the log summary.

        Args:
            log_summary (LogSummary): Summary of the log entries.

        Returns:
            str | None: The extracted filename from the log entry without .meta.json extension,
                       or None if no matching entry is found.
        """
        log_parser = JsonlLogParser(log_summary)
        log_entries = log_parser.get_entries_by_component("freqtrade.misc")

        for entry in log_entries:
            if "dumping json to" in entry.message.lower():
                # Extract the filename from the full path in the message
                json_path = entry.message.split('"')[1]
                filename = os.path.basename(json_path)
                # Remove both .meta.json extensions if present
                return filename.replace(".meta.json", "")

        return None

    def _validate_strategy_file(self, strategy_file: str) -> bool:
        """
        Validate the strategy file.
        """
        strategy_file_path = os.path.join(self.strategies_dir, strategy_file)
        return os.path.exists(strategy_file_path)

    def run_backtest(self, strategy_file: str, date_range: str) -> str:
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

        self.logger.info(
            "Starting backtest",
            extra={
                "data": {
                    "strategy": strategy_file,
                    "date_range": date_range,
                    "result_path": self.result_path,
                }
            },
        )

        if not strategy_file or not self._validate_strategy_file(strategy_file):
            self.logger.error(
                "Invalid strategy name or file does not exist",
                extra={"data": {"strategy": strategy_file}},
            )
            raise ValueError("Invalid strategy name or file does not exist")

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
                    strategy_file.replace(".py", ""),
                    "--timerange",
                    date_range,
                    "--export",
                    "trades",
                    "--export-filename",
                    self.result_path,
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

            result_name = self._extract_backtest_result_name(log_summary)
            if result_name:
                self.result_path = os.path.join(
                    self.local_backtest_results_folder, f"{result_name}.meta.json"
                )
                backtest_parser = FTBacktestParser(
                    self.local_backtest_results_folder, result_name
                )
                self.logger.info(
                    "Backtest completed successfully",
                    extra={
                        "data": {
                            "strategy": strategy_file,
                            "date_range": date_range,
                            "result_path": self.result_path,
                            "warning_count": len(log_summary.warnings),
                        }
                    },
                )
                return backtest_parser.parse_zip()

            if not os.path.exists(self.result_path):
                self.logger.error(
                    "Backtest finished without errors but no result file was created",
                    extra={
                        "data": {
                            "result_path": self.result_path,
                            "strategy": strategy_file,
                            "date_range": date_range,
                        }
                    },
                )
        except PickleableDockerException as e:
            raise e

        return None

    def cleanup_results(self) -> None:
        """
        Clean up backtest result files.

        Args:
            result_path (str): Path to the result file to clean up.

        Raises:
            OSError: If file deletion fails.
        """
        self.logger.info("Cleaning up backtest results folder")
        try:
            if os.path.exists(self.local_backtest_results_folder):
                shutil.rmtree(self.local_backtest_results_folder)
        except OSError as e:
            self.logger.error(
                "Failed to clean up backtest results folder",
                extra={"data": {"error": str(e), "error_type": type(e).__name__}},
            )
            raise

        self.logger.info("Backtest results cleaned up")


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
        ft_backtesting.run_backtest("EmaTradingStrategy.py", "20250203-20250210")
    except PickleableDockerException as e:
        pass
