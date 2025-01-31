import os
import logging
from typing import Optional
from python_on_whales import DockerClient
from app.config import settings
from app.util.exceptions import PickleableDockerException


class FTBase:
    def __init__(self, user_id: str):
        """
        Initialize base FreqTrade functionality.

        Args:
            user_id (str): The user ID to manage FreqTrade data for.

        Raises:
            ValueError: If user_id is empty.
        """
        if not user_id:
            raise ValueError("User ID cannot be empty.")

        self.user_id = user_id
        self.user_dir = self._get_user_data_directory()
        self.strategies_dir = self._get_strategies_dir()
        self.docker_compose_path = os.path.join(self.user_dir, "docker-compose.yml")
        self._docker_client: Optional[DockerClient] = None

    @property
    def docker(self) -> DockerClient:
        """
        Lazy-loaded Docker client.

        Returns:
            DockerClient: Configured Docker client for the user.
        """
        if self._docker_client is None:
            self._docker_client = DockerClient(
                compose_files=[self.docker_compose_path],
                client_type="docker",
            )
        return self._docker_client

    def _get_user_data_directory(self) -> str:
        """
        Get the full path to a user's FreqTrade data directory.

        Returns:
            str: The absolute path to the user's FreqTrade data directory.
        """
        if not self.user_id.startswith("user_"):
            user_data_dir = os.path.join(
                settings.FT_USERDATA_DIR, f"user_{self.user_id}"
            )
        else:
            user_data_dir = os.path.join(settings.FT_USERDATA_DIR, self.user_id)

        return user_data_dir

    def _get_strategies_dir(self) -> str:
        """
        Constructs the full path to the user's strategies directory.

        Returns:
            str: The full path to the user's strategies directory.
        """
        return os.path.join(self.user_dir, "user_data", "strategies")

    def ensure_user_dir_exists(self) -> None:
        """
        Ensure the user directory exists.

        Raises:
            OSError: If directory creation fails.
        """
        os.makedirs(self.user_dir, exist_ok=True)
        os.makedirs(self.strategies_dir, exist_ok=True)

    def run_docker_command(
        self, service: str, command: list[str], remove: bool = True
    ) -> None:
        """
        Run a Docker command safely with proper error handling.

        Args:
            service (str): The service name in docker-compose.
            command (list[str]): The command to run.
            remove (bool, optional): Whether to remove the container after execution. Defaults to True.

        Raises:
            PickleableDockerException: If the Docker command fails.
        """
        try:
            self.docker.compose.run(
                service,
                command,
                remove=remove,
            )
        except Exception as e:
            logging.error(f"Docker command failed: {e}", exc_info=True)
            raise PickleableDockerException("Docker command failed", e)

    @staticmethod
    def to_camel_case(strategy_name: str) -> str:
        """
        Converts a strategy name to CamelCase format.

        Args:
            strategy_name (str): The strategy name to convert.

        Returns:
            str: The strategy name in CamelCase format.
        """
        words = [
            word
            for word in strategy_name.replace("-", " ").replace("_", " ").split()
            if word
        ]
        return "".join(word.capitalize() for word in words)

    def __del__(self):
        """Cleanup Docker client on object destruction."""
        if self._docker_client is not None:
            self._docker_client.close()
