import os
import shutil
from app.util.logger import setup_logger
from .ft_base import FTBase


class FTUserDir(FTBase):
    def __init__(self, user_id: str):
        """
        Initialize user directory management functionality.

        Args:
            user_id (str): The user's ID.
        """
        super().__init__(user_id)
        self.logger = setup_logger(__name__)

    def exists(self) -> bool:
        """
        Check if a user's FreqTrade directory exists.

        Returns:
            bool: True if the directory exists, False otherwise.
        """
        exists = os.path.exists(self.user_dir)
        self.logger.debug(
            "Checked user directory existence",
            extra={
                "user_id": self.user_id,
                "directory": self.user_dir,
                "exists": exists,
            },
        )
        return exists

    def initialize(self) -> None:
        """
        Initialize the FreqTrade user directory with docker-compose.yml and user_data folder.
        If the directory already exists, this function will do nothing.

        Raises:
            OSError: If directory creation or file operations fail.
            FileNotFoundError: If template files are missing.
        """
        if self.exists():
            self.logger.info(
                "User directory already exists",
                extra={"user_id": self.user_id, "directory": self.user_dir},
            )
            return

        try:
            self.logger.info(
                "Initializing user directory",
                extra={"user_id": self.user_id, "directory": self.user_dir},
            )
            self.initialize_from_templates()
            self.run_docker_command(
                "freqtrade",
                ["create-userdir", "--userdir", "user_data"],
            )
            self.ensure_user_dir_exists()
            self.logger.info(
                "Successfully initialized user directory",
                extra={"user_id": self.user_id, "directory": self.user_dir},
            )
        except (OSError, FileNotFoundError) as e:
            self.logger.error(
                "Failed to initialize user directory",
                extra={
                    "user_id": self.user_id,
                    "directory": self.user_dir,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )
            self.remove()  # Clean up partially created directory
            raise OSError(f"Failed to initialize user directory: {e}") from e

    def remove(self) -> None:
        """
        Remove the FreqTrade user directory.

        Raises:
            OSError: If directory removal fails.
        """
        try:
            if self.exists():
                self.logger.info(
                    "Removing user directory",
                    extra={"user_id": self.user_id, "directory": self.user_dir},
                )
                shutil.rmtree(self.user_dir)
                self.logger.info(
                    "Successfully removed user directory",
                    extra={"user_id": self.user_id, "directory": self.user_dir},
                )
        except OSError as e:
            self.logger.error(
                "Failed to remove user directory",
                extra={
                    "user_id": self.user_id,
                    "directory": self.user_dir,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )
            raise OSError(f"Failed to remove user directory: {e}") from e


if __name__ == "__main__":
    import logging

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%d%b'%y %H:%M:%S",
    )
    ft_user_dir = FTUserDir("2oFuvIYD6fvQwokCEb61laEDjoM")
    ft_user_dir.initialize()
