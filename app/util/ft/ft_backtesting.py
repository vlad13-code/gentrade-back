import os
import uuid
import logging
from .ft_base import FTBase
from app.util.exceptions import PickleableDockerException


class FTBacktesting(FTBase):
    def __init__(self, clerk_id: str):
        """
        Initialize backtesting functionality.

        Args:
            clerk_id (str): The user's Clerk ID.
        """
        super().__init__(clerk_id)
        self.ensure_user_dir_exists()

    def run_backtest(self, strategy_class_name: str, date_range: str) -> str:
        """
        Runs a freqtrade backtest in Docker and returns the path to the results file.

        Args:
            strategy_class_name (str): Name of the strategy class.
            date_range (str): Date range in freqtrade format (e.g. "20200101-20200201").

        Returns:
            str: Path to the results JSON file.

        Raises:
            PickleableDockerException: If the backtest fails or results are not found.
            ValueError: If input parameters are invalid.
        """
        if not strategy_class_name:
            raise ValueError("Strategy class name cannot be empty")
        if not date_range:
            raise ValueError("Date range cannot be empty")

        output_filename = f"backtest_{uuid.uuid4()}.json"
        result_path = os.path.join(self.user_dir, "user_data", output_filename)

        self.run_docker_command(
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

        if not os.path.exists(result_path):
            raise PickleableDockerException(
                f"Backtest result file not found at {result_path}", None
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
        try:
            if os.path.exists(result_path):
                os.remove(result_path)
        except OSError as e:
            logging.error(f"Failed to clean up result file {result_path}: {e}")
            raise
