import os
import logging
from app.util.ft_userdir import get_user_data_directory


def get_user_strategies_dir(user_id: str) -> str:
    """
    Constructs the full path to the user's strategies directory.

    Args:
        user_id (str): The ID of the user.

    Returns:
        str: The full path to the user's strategies directory.
    """
    user_data_dir = get_user_data_directory(user_id)
    strategies_dir = os.path.join(user_data_dir, "user_data", "strategies")
    return strategies_dir


def to_camel_case(strategy_name: str) -> str:
    """
    Converts a strategy name to CamelCase format.

    Args:
        strategy_name (str): The strategy name to convert.

    Returns:
        str: The strategy name in CamelCase format.
    """
    # Split by common separators and filter out empty strings
    words = [
        word
        for word in strategy_name.replace("-", " ").replace("_", " ").split()
        if word
    ]
    # Capitalize first letter of each word and join
    return "".join(word.capitalize() for word in words)


def write_strategy_file(strategy_code: str, user_id: str, strategy_name: str) -> str:
    """
    Writes the strategy code to the user's Freqtrade strategy directory.

    Args:
        strategy_code (str): The code of the strategy to be written.
        user_id (str): The ID of the user.
        strategy_name (str): The name of the strategy file (without extension).

    Returns:
        str: The name of the written strategy file.

    Raises:
        ValueError: If any of the inputs are invalid.
        OSError: If the file cannot be written.
    """
    if not strategy_code:
        raise ValueError("Strategy code cannot be empty.")
    if not user_id:
        raise ValueError("User ID cannot be empty.")
    if not strategy_name:
        raise ValueError("Strategy name cannot be empty.")

    strategies_dir = get_user_strategies_dir(user_id)

    camel_case_name = to_camel_case(strategy_name)
    strategy_file_path = os.path.join(strategies_dir, f"{camel_case_name}.py")
    os.makedirs(strategies_dir, exist_ok=True)

    try:
        with open(strategy_file_path, "w") as strategy_file:
            strategy_file.write(strategy_code)
    except OSError as e:
        logging.error(
            f"Failed to write strategy file: {strategy_file_path}", exc_info=True
        )
        raise

    return f"{camel_case_name}.py"


def delete_strategy_file(user_id: str, strategy_file: str) -> None:
    """
    Deletes the strategy file from the user's Freqtrade strategy directory.

    Args:
        user_id (str): The ID of the user.
        strategy_file (str): The name of the strategy file to delete (without extension).

    Raises:
        ValueError: If any of the inputs are invalid.
        FileNotFoundError: If the strategy file does not exist.
        OSError: If the file cannot be deleted.
    """
    if not user_id:
        raise ValueError("User ID cannot be empty.")
    if not strategy_file:
        raise ValueError("Strategy file cannot be empty.")

    strategies_dir = get_user_strategies_dir(user_id)
    strategy_file_path = os.path.join(strategies_dir, strategy_file)

    if not os.path.exists(strategy_file_path):
        logging.warning(f"Strategy file does not exist: {strategy_file_path}")
        raise FileNotFoundError(f"Strategy file does not exist: {strategy_file_path}")

    try:
        os.remove(strategy_file_path)
    except OSError as e:
        logging.error(
            f"Failed to delete strategy file: {strategy_file_path}", exc_info=True
        )
        raise
