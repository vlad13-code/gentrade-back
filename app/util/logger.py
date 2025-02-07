import logging
import colorlog


def setup_logger(name: str = None) -> logging.Logger:
    """
    Set up a colored logger instance.

    Args:
        name (str, optional): Logger name. Defaults to None.

    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name or __name__)

    if not logger.handlers:  # Only add handler if the logger doesn't have one
        # Create console handler
        console_handler = logging.StreamHandler()

        # Create formatter
        formatter = colorlog.ColoredFormatter(
            "%(asctime)s - %(log_color)s%(levelname)s%(reset)s - %(name)s - %(message)s",
            datefmt="%d%b'%y %H:%M:%S",
            reset=True,
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
            secondary_log_colors={},
            style="%",
        )

        # Add formatter to console handler
        console_handler.setFormatter(formatter)

        # Add console handler to logger
        logger.addHandler(console_handler)

        # Set level to DEBUG to capture all levels
        logger.setLevel(logging.DEBUG)

        # Disable propagation to prevent duplicate logging when a name is provided
        if name:
            logger.propagate = False

    return logger
