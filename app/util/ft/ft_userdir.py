import os
import shutil
import logging
from app.config import settings
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
            return

        self.ensure_user_dir_exists()

        try:
            # Create docker-compose.yml
            docker_template_path = os.path.join(
                settings.FT_USERDATA_DIR, "docker-compose.template"
            )
            if not os.path.exists(docker_template_path):
                raise FileNotFoundError(
                    f"Template file not found: {docker_template_path}"
                )

            with open(docker_template_path, "r") as template_file:
                content = template_file.read()
            content = content.replace("$user_id", self.user_id)

            with open(self.docker_compose_path, "w") as docker_compose_file:
                docker_compose_file.write(content)

            # Create config.json
            config_template_path = os.path.join(
                settings.FT_USERDATA_DIR, "config.json.template"
            )
            if not os.path.exists(config_template_path):
                raise FileNotFoundError(
                    f"Template file not found: {config_template_path}"
                )

            config_path = os.path.join(self.user_dir, "user_data", "config.json")
            os.makedirs(os.path.dirname(config_path), exist_ok=True)

            with open(config_template_path, "r") as template_file:
                content = template_file.read()

            with open(config_path, "w") as config_file:
                config_file.write(content)

            # Initialize user directory using freqtrade
            self.run_docker_command(
                "freqtrade",
                ["create-userdir", "--userdir", "user_data"],
            )

        except OSError as e:
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
