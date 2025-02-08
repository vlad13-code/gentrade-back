import os
import json
from typing import Union, Dict, Any
from pydantic import ValidationError

from .ft_base import FTBase
from app.schemas.schema_freqtrade_config import FreqtradeConfig
from app.util.logger import setup_logger


class FTUserConfig(FTBase):
    def __init__(self, user_id: str):
        """
        Initialize FreqTrade configuration management functionality.

        Args:
            user_id (str): The user's ID.
        """
        super().__init__(user_id)
        self.config_path = os.path.join(self.user_dir, "user_data", "config.json")
        self.ensure_user_dir_exists()
        self.logger = setup_logger(__name__)

    def read_config(self) -> FreqtradeConfig:
        """
        Read and parse the user's FreqTrade configuration file.

        Returns:
            FreqtradeConfig: The parsed and validated configuration

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValidationError: If config file doesn't match schema
            OSError: If file cannot be read
            json.JSONDecodeError: If config file is not valid JSON
        """
        self.logger.debug(
            "Reading configuration file",
            extra={"user_id": self.user_id, "config_path": self.config_path},
        )

        if not os.path.exists(self.config_path):
            self.logger.error(
                "Configuration file not found",
                extra={"user_id": self.user_id, "config_path": self.config_path},
            )
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        try:
            with open(self.config_path, "r") as config_file:
                config_data = json.load(config_file)
            config = FreqtradeConfig(**config_data)
            self.logger.debug(
                "Successfully read configuration file",
                extra={"user_id": self.user_id, "config_path": self.config_path},
            )
            return config
        except json.JSONDecodeError as e:
            self.logger.error(
                "Failed to parse config file",
                extra={
                    "user_id": self.user_id,
                    "config_path": self.config_path,
                    "error": str(e),
                    "error_type": "JSONDecodeError",
                },
                exc_info=True,
            )
            raise
        except ValidationError as e:
            self.logger.error(
                "Invalid configuration",
                extra={
                    "user_id": self.user_id,
                    "config_path": self.config_path,
                    "error": str(e),
                    "error_type": "ValidationError",
                },
                exc_info=True,
            )
            raise
        except OSError as e:
            self.logger.error(
                "Failed to read config file",
                extra={
                    "user_id": self.user_id,
                    "config_path": self.config_path,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )
            raise

    def write_config(self, config: Union[FreqtradeConfig, Dict[str, Any]]) -> None:
        """
        Write configuration to the user's config file.

        Args:
            config: Configuration to write (either as FreqtradeConfig or dict)

        Raises:
            ValidationError: If config is invalid
            OSError: If file cannot be written
            TypeError: If config is of invalid type
        """
        self.logger.debug(
            "Writing configuration file",
            extra={"user_id": self.user_id, "config_path": self.config_path},
        )

        try:
            if isinstance(config, dict):
                config = FreqtradeConfig(**config)
            elif not isinstance(config, FreqtradeConfig):
                error_msg = "Config must be either FreqtradeConfig or dict"
                self.logger.error(
                    error_msg,
                    extra={
                        "user_id": self.user_id,
                        "config_path": self.config_path,
                        "error_type": "TypeError",
                        "config_type": type(config).__name__,
                    },
                )
                raise TypeError(error_msg)

            # Create parent directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)

            # Write to a temporary file first
            temp_path = f"{self.config_path}.tmp"
            with open(temp_path, "w") as config_file:
                json.dump(config.model_dump(exclude_none=True), config_file, indent=4)

            # Rename temporary file to actual config file (atomic operation)
            os.replace(temp_path, self.config_path)

            self.logger.info(
                "Successfully wrote configuration file",
                extra={"user_id": self.user_id, "config_path": self.config_path},
            )

        except ValidationError as e:
            self.logger.error(
                "Invalid configuration",
                extra={
                    "user_id": self.user_id,
                    "config_path": self.config_path,
                    "error": str(e),
                    "error_type": "ValidationError",
                },
                exc_info=True,
            )
            raise
        except OSError as e:
            self.logger.error(
                "Failed to write config file",
                extra={
                    "user_id": self.user_id,
                    "config_path": self.config_path,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )
            if os.path.exists(f"{self.config_path}.tmp"):
                try:
                    os.remove(f"{self.config_path}.tmp")
                except OSError:
                    pass
            raise
        except Exception as e:
            self.logger.error(
                "Unexpected error writing config",
                extra={
                    "user_id": self.user_id,
                    "config_path": self.config_path,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )
            raise

    def update_config(self, updates: Dict[str, Any]) -> FreqtradeConfig:
        """
        Update specific fields in the configuration.

        Args:
            updates: Configuration updates to apply

        Returns:
            FreqtradeConfig: Updated configuration

        Raises:
            FileNotFoundError: If config doesn't exist
            ValidationError: If updates are invalid
            OSError: If file operations fail
        """
        self.logger.debug(
            "Updating configuration",
            extra={
                "user_id": self.user_id,
                "config_path": self.config_path,
                "update_keys": list(updates.keys()),
            },
        )

        try:
            current_config = self.read_config()
            current_dict = current_config.model_dump()

            # Deep merge the updates into current config
            self._deep_update(current_dict, updates)

            # Validate and write the updated config
            updated_config = FreqtradeConfig(**current_dict)
            self.write_config(updated_config)

            self.logger.info(
                "Successfully updated configuration",
                extra={
                    "user_id": self.user_id,
                    "config_path": self.config_path,
                    "updated_keys": list(updates.keys()),
                },
            )

            return updated_config

        except Exception as e:
            self.logger.error(
                "Failed to update configuration",
                extra={
                    "user_id": self.user_id,
                    "config_path": self.config_path,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "update_keys": list(updates.keys()),
                },
                exc_info=True,
            )
            raise

    def _deep_update(
        self, base_dict: Dict[str, Any], update_dict: Dict[str, Any]
    ) -> None:
        """
        Recursively update a dictionary with another dictionary.

        Args:
            base_dict: Base dictionary to update
            update_dict: Dictionary with updates to apply
        """
        for key, value in update_dict.items():
            if (
                key in base_dict
                and isinstance(base_dict[key], dict)
                and isinstance(value, dict)
            ):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
