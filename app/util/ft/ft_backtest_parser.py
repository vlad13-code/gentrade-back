import json
import zipfile
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, Optional

from app.util.logger import setup_logger


class BacktestResultError(Exception):
    """Custom exception for errors during backtest result processing."""

    pass


class FTBacktestParser:
    """
    Parses Freqtrade backtest results. Extracts the associated ZIP file,
    parses JSON data, and cleans up temporary files.
    """

    def __init__(self, backtests_folder: str, result_name: str | Path):
        """
        Initializes the parser with the path to the backtest result JSON file.

        Args:
            result_path: Path to the backtest result JSON file (e.g., .../backtest_*.json).

        Raises:
            FileNotFoundError: If the result_path does not exist.
            ValueError: If the result_path does not follow the expected naming convention.
        """
        self.logger = setup_logger(__name__)
        self.result_path = Path(backtests_folder, result_name)

        self.zip_path = self.result_path.with_suffix(".zip")
        if not self.zip_path.exists():
            self.logger.error(f"Associated ZIP file not found: {self.zip_path}")
            raise FileNotFoundError(f"Associated ZIP file not found: {self.zip_path}")

        self.data: Optional[Dict[str, Any]] = None

    def _extract_zip(self) -> Path:
        """
        Extracts the associated ZIP file to a temporary directory.

        Returns:
            Path: The path to the temporary directory containing the extracted files.

        Raises:
            BacktestResultError: If ZIP extraction fails.
        """
        self.logger.debug(f"Extracting backtest result ZIP: {self.zip_path}")
        temp_dir = Path(tempfile.mkdtemp())
        try:
            with zipfile.ZipFile(self.zip_path, "r") as zip_ref:
                zip_ref.extractall(temp_dir)
            self.logger.debug(f"Extracted ZIP to: {temp_dir}")
            return temp_dir
        except zipfile.BadZipFile as e:
            self.logger.error(f"Failed to extract ZIP file: {self.zip_path} - {e}")
            raise BacktestResultError(
                f"Failed to extract ZIP file: {self.zip_path}"
            ) from e

    def parse_zip(self) -> Dict[str, Any]:
        """
        Extracts and parses the backtest result from the ZIP file.

        Returns:
            Dict[str, Any]: Parsed backtest data from the single JSON file.

        Raises:
            BacktestResultError: If parsing fails or no JSON file is found.
        """
        if self.data:
            return self.data

        temp_dir = self._extract_zip()
        try:
            json_files = [f for f in os.listdir(temp_dir) if f.endswith(".json")]

            if not json_files:
                raise BacktestResultError(
                    "No JSON files found in the backtest result ZIP"
                )

            if len(json_files) > 1:
                self.logger.warning(
                    f"Multiple JSON files found in backtest result ZIP: {json_files}"
                )

            # Always use the first JSON file (typically the .meta.json file)
            filepath = temp_dir / json_files[0]
            try:
                with open(filepath, "r") as f:
                    self.data = json.load(f)
            except (OSError, json.JSONDecodeError) as e:
                self.logger.error(f"Failed to parse {filepath}: {e}")
                raise BacktestResultError(f"Failed to parse {filepath}") from e

            return self.data
        finally:
            self._cleanup_temp_dir(temp_dir)

    def _cleanup_temp_dir(self, temp_dir: Path) -> None:
        """
        Removes the temporary directory and its contents.

        Args:
            temp_dir: The path to temporary directory.
        """
        try:
            self.logger.debug(f"Cleaning up temporary directory: {temp_dir}")
            for file in temp_dir.iterdir():
                file.unlink()
            temp_dir.rmdir()
        except OSError as e:
            self.logger.warning(f"Failed to remove temporary directory {temp_dir}: {e}")
