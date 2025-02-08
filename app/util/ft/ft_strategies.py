import os
from app.util.logger import setup_logger
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
        self.logger = setup_logger(__name__)

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
            self.logger.error(
                "Strategy code cannot be empty",
                extra={
                    "user_id": self.user_id,
                    "strategy_name": strategy_name,
                    "error_type": "ValueError",
                },
            )
            raise ValueError("Strategy code cannot be empty.")
        if not strategy_name:
            self.logger.error(
                "Strategy name cannot be empty",
                extra={"user_id": self.user_id, "error_type": "ValueError"},
            )
            raise ValueError("Strategy name cannot be empty.")

        camel_case_name = self.to_camel_case(strategy_name)
        strategy_file_path = os.path.join(self.strategies_dir, f"{camel_case_name}.py")

        self.logger.debug(
            "Writing strategy file",
            extra={
                "user_id": self.user_id,
                "strategy_name": strategy_name,
                "strategy_file": f"{camel_case_name}.py",
                "file_path": strategy_file_path,
            },
        )

        try:
            with open(strategy_file_path, "w") as strategy_file:
                strategy_file.write(strategy_code)

            self.logger.info(
                "Successfully wrote strategy file",
                extra={
                    "user_id": self.user_id,
                    "strategy_name": strategy_name,
                    "strategy_file": f"{camel_case_name}.py",
                    "file_path": strategy_file_path,
                },
            )
        except OSError as e:
            self.logger.error(
                "Failed to write strategy file",
                extra={
                    "user_id": self.user_id,
                    "strategy_name": strategy_name,
                    "strategy_file": f"{camel_case_name}.py",
                    "file_path": strategy_file_path,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
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
            self.logger.error(
                "Strategy file cannot be empty",
                extra={"user_id": self.user_id, "error_type": "ValueError"},
            )
            raise ValueError("Strategy file cannot be empty.")

        strategy_file_path = os.path.join(self.strategies_dir, strategy_file)

        self.logger.debug(
            "Attempting to delete strategy file",
            extra={
                "user_id": self.user_id,
                "strategy_file": strategy_file,
                "file_path": strategy_file_path,
            },
        )

        if not os.path.exists(strategy_file_path):
            self.logger.error(
                "Strategy file does not exist",
                extra={
                    "user_id": self.user_id,
                    "strategy_file": strategy_file,
                    "file_path": strategy_file_path,
                    "error_type": "FileNotFoundError",
                },
            )
            raise FileNotFoundError(
                f"Strategy file does not exist: {strategy_file_path}"
            )

        try:
            os.remove(strategy_file_path)
            self.logger.info(
                "Successfully deleted strategy file",
                extra={
                    "user_id": self.user_id,
                    "strategy_file": strategy_file,
                    "file_path": strategy_file_path,
                },
            )
        except OSError as e:
            self.logger.error(
                "Failed to delete strategy file",
                extra={
                    "user_id": self.user_id,
                    "strategy_file": strategy_file,
                    "file_path": strategy_file_path,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
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
        self.logger.debug(
            "Listing strategy files",
            extra={"user_id": self.user_id, "strategies_dir": self.strategies_dir},
        )

        try:
            if not os.path.exists(self.strategies_dir):
                self.logger.info(
                    "Strategies directory does not exist",
                    extra={
                        "user_id": self.user_id,
                        "strategies_dir": self.strategies_dir,
                    },
                )
                return []

            strategies = [
                f for f in os.listdir(self.strategies_dir) if f.endswith(".py")
            ]
            self.logger.debug(
                "Successfully listed strategy files",
                extra={
                    "user_id": self.user_id,
                    "strategies_dir": self.strategies_dir,
                    "strategy_count": len(strategies),
                    "strategies": strategies,
                },
            )
            return strategies
        except OSError as e:
            self.logger.error(
                "Failed to list strategies",
                extra={
                    "user_id": self.user_id,
                    "strategies_dir": self.strategies_dir,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )
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
            self.logger.error(
                "Strategy file cannot be empty",
                extra={"user_id": self.user_id, "error_type": "ValueError"},
            )
            raise ValueError("Strategy file cannot be empty.")

        strategy_file_path = os.path.join(self.strategies_dir, strategy_file)

        self.logger.debug(
            "Reading strategy file",
            extra={
                "user_id": self.user_id,
                "strategy_file": strategy_file,
                "file_path": strategy_file_path,
            },
        )

        if not os.path.exists(strategy_file_path):
            self.logger.error(
                "Strategy file does not exist",
                extra={
                    "user_id": self.user_id,
                    "strategy_file": strategy_file,
                    "file_path": strategy_file_path,
                    "error_type": "FileNotFoundError",
                },
            )
            raise FileNotFoundError(
                f"Strategy file does not exist: {strategy_file_path}"
            )

        try:
            with open(strategy_file_path, "r") as f:
                content = f.read()
            self.logger.debug(
                "Successfully read strategy file",
                extra={
                    "user_id": self.user_id,
                    "strategy_file": strategy_file,
                    "file_path": strategy_file_path,
                    "content_length": len(content),
                },
            )
            return content
        except OSError as e:
            self.logger.error(
                "Failed to read strategy file",
                extra={
                    "user_id": self.user_id,
                    "strategy_file": strategy_file,
                    "file_path": strategy_file_path,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )
            raise OSError(f"Failed to read strategy file: {e}") from e
