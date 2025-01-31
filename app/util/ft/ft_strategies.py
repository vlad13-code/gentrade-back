import os
import logging
from .ft_base import FTBase


class FTStrategies(FTBase):
    def __init__(self, user_id: str):
        """
        Initialize strategy management functionality.

        Args:
            user_id (str): The user's ID.
        """
        super().__init__(user_id)
        self.ensure_user_dir_exists()

    def write_strategy(self, strategy_code: str, strategy_name: str) -> str:
        """
        Writes the strategy code to the user's Freqtrade strategy directory.

        Args:
            strategy_code (str): The code of the strategy to be written.
            strategy_name (str): The name of the strategy file (without extension).

        Returns:
            str: The name of the written strategy file.

        Raises:
            ValueError: If any of the inputs are invalid.
            OSError: If the file cannot be written.
        """
        if not strategy_code:
            raise ValueError("Strategy code cannot be empty.")
        if not strategy_name:
            raise ValueError("Strategy name cannot be empty.")

        camel_case_name = self.to_camel_case(strategy_name)
        strategy_file_path = os.path.join(self.strategies_dir, f"{camel_case_name}.py")

        try:
            with open(strategy_file_path, "w") as strategy_file:
                strategy_file.write(strategy_code)
        except OSError as e:
            logging.error(
                f"Failed to write strategy file: {strategy_file_path}", exc_info=True
            )
            raise OSError(f"Failed to write strategy file: {e}") from e

        return f"{camel_case_name}.py"

    def delete_strategy(self, strategy_file: str) -> None:
        """
        Deletes the strategy file from the user's Freqtrade strategy directory.

        Args:
            strategy_file (str): The name of the strategy file to delete (with extension).

        Raises:
            ValueError: If any of the inputs are invalid.
            FileNotFoundError: If the strategy file does not exist.
            OSError: If the file cannot be deleted.
        """
        if not strategy_file:
            raise ValueError("Strategy file cannot be empty.")

        strategy_file_path = os.path.join(self.strategies_dir, strategy_file)

        if not os.path.exists(strategy_file_path):
            raise FileNotFoundError(
                f"Strategy file does not exist: {strategy_file_path}"
            )

        try:
            os.remove(strategy_file_path)
        except OSError as e:
            logging.error(
                f"Failed to delete strategy file: {strategy_file_path}", exc_info=True
            )
            raise OSError(f"Failed to delete strategy file: {e}") from e

    def list_strategies(self) -> list[str]:
        """
        List all strategy files in the user's strategy directory.

        Returns:
            list[str]: List of strategy file names.

        Raises:
            OSError: If the directory cannot be read.
        """
        try:
            if not os.path.exists(self.strategies_dir):
                return []
            return [f for f in os.listdir(self.strategies_dir) if f.endswith(".py")]
        except OSError as e:
            logging.error(f"Failed to list strategies: {e}", exc_info=True)
            raise OSError(f"Failed to list strategies: {e}") from e

    def read_strategy(self, strategy_file: str) -> str:
        """
        Read the contents of a strategy file.

        Args:
            strategy_file (str): The name of the strategy file to read (with extension).

        Returns:
            str: The contents of the strategy file.

        Raises:
            ValueError: If the strategy file name is empty.
            FileNotFoundError: If the strategy file does not exist.
            OSError: If the file cannot be read.
        """
        if not strategy_file:
            raise ValueError("Strategy file cannot be empty.")

        strategy_file_path = os.path.join(self.strategies_dir, strategy_file)

        if not os.path.exists(strategy_file_path):
            raise FileNotFoundError(
                f"Strategy file does not exist: {strategy_file_path}"
            )

        try:
            with open(strategy_file_path, "r") as f:
                return f.read()
        except OSError as e:
            logging.error(
                f"Failed to read strategy file: {strategy_file_path}", exc_info=True
            )
            raise OSError(f"Failed to read strategy file: {e}") from e
