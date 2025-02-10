import logging
import colorlog
import uuid
import os
from datetime import datetime, timezone
from typing import Optional, Any, Dict
from pythonjsonlogger import jsonlogger
from contextvars import ContextVar

# Context variables for storing request-scoped data
correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")
user_id: ContextVar[str] = ContextVar("user_id", default="")
strategy_id: ContextVar[int] = ContextVar("strategy_id", default=0)
backtest_id: ContextVar[int] = ContextVar("backtest_id", default=0)


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter that adds additional fields to log records."""

    def add_fields(
        self,
        log_record: Dict[str, Any],
        record: logging.LogRecord,
        message_dict: Dict[str, Any],
    ) -> None:
        """Add custom fields to the log record."""
        super().add_fields(log_record, record, message_dict)

        # Add timestamp in ISO8601 format
        now = datetime.now(timezone.utc).isoformat()
        log_record["timestamp"] = now

        # Add log level
        log_record["level"] = record.levelname

        # Add component name (logger name)
        log_record["component"] = record.name

        # Add context variables if they exist
        try:
            log_record["correlation_id"] = correlation_id.get()
        except LookupError:
            log_record["correlation_id"] = ""

        try:
            if user_id.get():
                log_record["user_id"] = user_id.get()
        except LookupError:
            pass

        try:
            if strategy_id.get():
                log_record["strategy_id"] = strategy_id.get()
        except LookupError:
            pass

        try:
            if backtest_id.get():
                log_record["backtest_id"] = backtest_id.get()
        except LookupError:
            pass

        # Add extra data if provided
        if hasattr(record, "data"):
            log_record["data"] = record.data


def setup_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Set up a logger instance with both console and JSON handlers.

    Args:
        name (str, optional): Logger name. If None, defaults to the root 'app' logger.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger_name = f"app.{name}" if name else "app"
    logger = logging.getLogger(logger_name)

    # Set to DEBUG to capture all - handlers will filter
    logger.setLevel(logging.DEBUG)

    # Prevent duplicate logs
    logger.propagate = False

    # Only add handlers if they don't exist
    if not logger.handlers:
        # Console Handler (Colored)
        console_handler = logging.StreamHandler()
        console_formatter = colorlog.ColoredFormatter(
            "%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(name)s%(reset)s - "
            "%(log_color)s%(message)s%(reset)s",
            log_colors={
                "DEBUG": "white",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
            secondary_log_colors={},
            style="%",
        )
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.DEBUG)
        logger.addHandler(console_handler)

        # JSON Handler (File)
        # Create logs directory if it doesn't exist
        logs_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(logs_dir, exist_ok=True)

        # Create a new log file for each day
        log_file = os.path.join(
            logs_dir, f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        )
        json_handler = logging.FileHandler(log_file)
        json_formatter = CustomJsonFormatter(
            "%(timestamp)s %(level)s %(name)s %(correlation_id)s "
            "%(message)s %(data)s"
        )
        json_handler.setFormatter(json_formatter)
        json_handler.setLevel(logging.DEBUG)
        logger.addHandler(json_handler)

    return logger


def set_correlation_id(new_id: Optional[str] = None) -> str:
    """Set a new correlation ID or generate one if not provided."""
    new_correlation_id = new_id or str(uuid.uuid4())
    correlation_id.set(new_correlation_id)
    return new_correlation_id


def get_correlation_id() -> str:
    """Get the current correlation ID from the context."""
    try:
        return correlation_id.get()
    except LookupError:
        return ""


def set_user_id(new_id: str) -> None:
    """Set the user ID in the context."""
    user_id.set(new_id)


def set_strategy_id(new_id: int) -> None:
    """Set the strategy ID in the context."""
    strategy_id.set(new_id)


def set_backtest_id(new_id: int) -> None:
    """Set the backtest ID in the context."""
    backtest_id.set(new_id)


# Example usage:
# logger = setup_logger(__name__)
# logger.info("User created", extra={"data": {"email": "user@example.com"}})
