import os
import shutil
import logging
from .ft_base import FTBase


class FTUserDir(FTBase):
    def __init__(self, user_id: str):
        """
        Initialize user directory management functionality.

        Args:
            user_id (str): The user's ID.
        """
        super().__init__(user_id)

    def exists(self) -> bool:
        """
        Check if a user's FreqTrade directory exists.

        Returns:
            bool: True if the directory exists, False otherwise.
        """
        return os.path.exists(self.user_dir)

    def initialize(self) -> None:
        """
        Initialize the FreqTrade user directory with docker-compose.yml and user_data folder.
        If the directory already exists, this function will do nothing.

        Raises:
            OSError: If directory creation or file operations fail.
            FileNotFoundError: If template files are missing.
        """
        if self.exists():
            logging.info(f"User directory {self.user_dir} already exists")
            return

        try:
            self.initialize_from_templates()
            self.run_docker_command(
                "freqtrade",
                ["create-userdir", "--userdir", "user_data"],
            )
            self.ensure_user_dir_exists()
        except (OSError, FileNotFoundError) as e:
            logging.error(f"Failed to initialize user directory: {e}", exc_info=True)
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
                shutil.rmtree(self.user_dir)
        except OSError as e:
            logging.error(f"Failed to remove user directory: {e}", exc_info=True)
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
