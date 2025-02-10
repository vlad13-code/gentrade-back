import os
import uuid
from typing import Optional
from python_on_whales import DockerClient, DockerException
from app.config import settings
from app.util.exceptions import PickleableDockerException
from .verification.log_parser import JsonlLogParser, LogSummary
from app.util.logger import setup_logger
from pathlib import Path


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
        self.logs_dir = self._get_logs_dir()

        self.docker_compose_path = os.path.join(self.user_dir, "docker-compose.yml")

        self._docker_compose_client: Optional[DockerClient] = None
        self.logger = setup_logger("ft.base")
        self.log_parser = JsonlLogParser()

    @property
    def docker(self) -> DockerClient:
        """
        Lazy-loaded Docker Compose client.

        Returns:
            DockerClient: Configured Docker Compose client for the user.
        """
        if self._docker_compose_client is None:
            self.logger.debug(
                f"Initializing Docker client with compose file: {self.docker_compose_path}",
                extra={"data": {"compose_file": self.docker_compose_path}},
            )
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

    def _get_logs_dir(self) -> str:
        """
        Constructs the full path to the user's logs directory.

        Returns:
            str: The full path to the user's logs directory.
        """
        return os.path.join(self.user_dir, "user_data", "logs")

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
            self.logger.error(
                "Template file not found",
                extra={"data": {"template_path": template_path}},
            )
            raise FileNotFoundError(f"Template file not found: {template_path}")

        os.makedirs(os.path.dirname(target_path), exist_ok=True)

        with open(template_path, "r") as template_file:
            content = template_file.read()

        if replacements:
            for key, value in replacements.items():
                content = content.replace(key, value)

        with open(target_path, "w") as target_file:
            target_file.write(content)

        self.logger.info(
            "Created file from template",
            extra={
                "data": {
                    "template": template_name,
                    "target_path": target_path,
                    "replacements": replacements,
                }
            },
        )

    def initialize_from_templates(self) -> None:
        """
        Initialize user directory with necessary files from templates.

        Raises:
            FileNotFoundError: If template files are missing.
            OSError: If file creation fails.
        """
        self.logger.info(
            "Initializing user directory from templates",
            extra={"data": {"user_id": self.user_id}},
        )
        try:
            # Create docker-compose.yml
            self._create_from_template(
                "docker-compose.template",
                self.docker_compose_path,
                {"$user_id": self.user_id},
            )

            # Create config.json
            config_path = os.path.join(self.user_dir, "user_data", "config.json")
            self._create_from_template("config.json.template", config_path)

            self.logger.info(
                "User directory initialized successfully",
                extra={"data": {"user_id": self.user_id, "user_dir": self.user_dir}},
            )

        except (OSError, FileNotFoundError) as e:
            self.logger.error(
                "Failed to initialize from templates",
                extra={"data": {"error": str(e), "error_type": type(e).__name__}},
            )
            raise

    def ensure_user_dir_exists(self) -> None:
        """
        Ensure the user directory exists.

        Raises:
            OSError: If directory creation fails.
        """
        try:
            os.makedirs(self.user_dir, exist_ok=True)
            os.makedirs(self.strategies_dir, exist_ok=True)
        except OSError as e:
            self.logger.error(
                "Failed to create user directories",
                extra={
                    "data": {
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "user_dir": self.user_dir,
                        "strategies_dir": self.strategies_dir,
                    }
                },
            )
            raise

    def run_docker_command(
        self, service: str, command: list[str], remove: bool = True
    ) -> LogSummary:
        """
        Run a Docker command safely with proper error handling.

        Args:
            service (str): The service name in docker-compose.
            command (list[str]): The command to run.
            remove (bool, optional): Whether to remove the container after execution. Defaults to True.

        Raises:
            PickleableDockerException: If the Docker command fails.

        Returns:
            DockerLogSummary: The log summary of the Docker command.
        """

        # Create a unique log file for each run
        log_file = f"ft_logs_{uuid.uuid4()}.log"
        jsonl_file = Path(self.logs_dir) / f"{log_file}.jsonl"

        # Add the logfile argument to the command
        command.append("--logfile")
        command.append(log_file)

        self.logger.info(
            f"Running Docker command: {' '.join(command)}",
            extra={
                "data": {
                    "service": service,
                    "command": command,
                }
            },
        )

        try:
            self.docker.compose.run(
                service,
                command,
                tty=False,
                remove=remove,
            )

            log_summary: LogSummary = self.log_parser.process_log_file(
                jsonl_file.absolute()
            )
            os.remove(jsonl_file.absolute())

            return log_summary

        except DockerException as e:
            log_summary: LogSummary = self.log_parser.process_log_file(
                jsonl_file.absolute()
            )
            os.remove(jsonl_file.absolute())

            self.logger.error(
                f"Docker command failed: {log_summary.errors[0].message}",
                extra={
                    "data": {
                        "service": service,
                        "command": " ".join(command),
                        "errors": [
                            f"{error.name}: {error.message}"
                            for error in log_summary.errors
                        ],
                        "warnings": [
                            f"{warning.name}: {warning.message}"
                            for warning in log_summary.warnings
                        ],
                    }
                },
            )
            raise PickleableDockerException(
                message=f"{log_summary.errors[0].name}: {log_summary.errors[0].message}",
                original_exception=e,
                command=command,
                exit_code=getattr(e, "return_code", -1),
                stdout=getattr(e, "stdout", ""),
                stderr=getattr(e, "stderr", str(e)),
            ) from e

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
