import os
import logging
from typing import Optional
from python_on_whales import DockerClient
from sqlalchemy import false
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
        self._docker_compose_client: Optional[DockerClient] = None

    @property
    def docker(self) -> DockerClient:
        """
        Lazy-loaded Docker Compose client.

        Returns:
            DockerClient: Configured Docker Compose client for the user.
        """
        if self._docker_compose_client is None:
            self._docker_compose_client = DockerClient(
                compose_files=[self.docker_compose_path]
            )
        return self._docker_compose_client

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

    def _create_from_template(
        self, template_name: str, target_path: str, replacements: dict = None
    ) -> None:
        """
        Create a file from a template with optional replacements.

        Args:
            template_name (str): Name of the template file.
            target_path (str): Path where the file should be created.
            replacements (dict, optional): Dictionary of replacements to make in the template.

        Raises:
            FileNotFoundError: If template file is missing.
            OSError: If file creation fails.
        """
        template_path = os.path.join(settings.FT_USERDATA_DIR, template_name)
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template file not found: {template_path}")

        os.makedirs(os.path.dirname(target_path), exist_ok=True)

        with open(template_path, "r") as template_file:
            content = template_file.read()

        if replacements:
            for key, value in replacements.items():
                content = content.replace(key, value)

        with open(target_path, "w") as target_file:
            target_file.write(content)

    def initialize_from_templates(self) -> None:
        """
        Initialize user directory with necessary files from templates.

        Raises:
            FileNotFoundError: If template files are missing.
            OSError: If file creation fails.
        """
        try:
            # Initialize user directory using freqtrade
            self.run_docker_command(
                "freqtrade",
                ["create-userdir", "--userdir", "user_data"],
            )

            # Create docker-compose.yml
            self._create_from_template(
                "docker-compose.template",
                self.docker_compose_path,
                {"$user_id": self.user_id},
            )

            # Create config.json
            config_path = os.path.join(self.user_dir, "user_data", "config.json")
            self._create_from_template("config.json.template", config_path)

        except (OSError, FileNotFoundError) as e:
            logging.error(f"Failed to initialize from templates: {e}", exc_info=True)
            raise

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
        # logging.info(f"Running Docker command: {service} {' '.join(command)}")

        try:
            result = {"stdout": [], "stderr": []}
            output_stream = self.docker.compose.run(
                service,
                command,
                tty=False,
                stream=True,
                remove=remove,
            )

            for type, line in output_stream:
                result[type].append(line.decode().strip())

            return result
        except Exception as e:
            # logging.error(f"Docker command failed: {e}", exc_info=True)
            if "TimeoutError" in str(e) or "RequestTimeout" in str(e):
                logging.error(
                    "Connection timeout detected. Please check your network connection and try again."
                )
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
