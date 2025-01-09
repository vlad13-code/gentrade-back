import os
import shutil
from python_on_whales import DockerClient

from app.config import settings


def get_user_data_directory(user_id: str) -> str:
    """
    Get the full path to a user's FreqTrade data directory.

    Args:
        user_id (str): The unique identifier for the user.

    Returns:
        str: The absolute path to the user's FreqTrade data directory.

    Raises:
        ValueError: If user_id is empty.
    """
    if not user_id:
        raise ValueError("User ID cannot be empty.")

    return os.path.join(settings.FT_USERDATA_DIR, user_id)


def user_dir_exists(user_id: str) -> bool:
    """
    Check if a user's FreqTrade directory exists.

    Args:
        user_id (str): The unique identifier for the user.

    Returns:
        bool: True if the directory exists, False otherwise.

    Raises:
        ValueError: If user_id is empty.
    """
    user_dir = get_user_data_directory(user_id)
    return os.path.exists(user_dir)


def init_ft_userdir(user_id: str):
    """
    Initialize the FreqTrade user directory for a given user ID with a docker-compose.yml file and user_data folder.
    If the directory already exists, this function will do nothing.

    Args:
        user_id (str): The unique identifier for the user.

    Returns:
        None
    """
    if user_dir_exists(user_id):
        return

    user_dir = get_user_data_directory(user_id)
    os.makedirs(user_dir, exist_ok=True)

    template_path = os.path.join(settings.FT_USERDATA_DIR, "docker-compose.template")
    with open(template_path, "r") as template_file:
        content = template_file.read()
    content = content.replace("$user_id", user_id)

    docker_compose_path = os.path.abspath(os.path.join(user_dir, "docker-compose.yml"))
    with open(docker_compose_path, "w") as docker_compose_file:
        docker_compose_file.write(content)

    docker = DockerClient(
        compose_files=[docker_compose_path],
        client_type="docker",
    )
    docker.compose.run(
        "freqtrade",
        ["create-userdir", "--userdir", "user_data"],
        remove=True,
    )


def remove_ft_userdir(user_id: str):
    """
    Remove the FreqTrade user directory for a given user ID.

    Args:
        user_id (str): The unique identifier for the user.
    """
    user_dir = get_user_data_directory(user_id)
    shutil.rmtree(user_dir)
