from python_on_whales import DockerClient
import os
import uuid
from app.util.ft_userdir import get_user_data_directory


def run_backtest_in_docker(
    strategy_file_path: str, clerk_id: str, date_range: str
) -> str:
    """
    Runs a freqtrade backtest in Docker and returns the path to the results file

    Args:
        strategy_file_path: Path to the strategy file
        clerk_id: User's clerk ID for directory management
        date_range: Date range in freqtrade format (e.g. "20200101-20200201")

    Returns:
        str: Path to the results JSON file
    """
    user_dir = get_user_data_directory(clerk_id)
    docker_compose_path = os.path.join(user_dir, "docker-compose.yml")

    docker = DockerClient(
        compose_files=[docker_compose_path],
        client_type="docker",
    )

    output_filename = f"backtest_{uuid.uuid4()}.json"
    docker.compose.run(
        "freqtrade",
        [
            "backtesting",
            "--userdir",
            "user_data",
            "--strategy",
            strategy_file_path,
            "--timerange",
            date_range,
            "--export",
            "json",
            "--exportfilename",
            output_filename,
        ],
        remove=True,
    )

    # Construct the full path to the result inside user_data
    return os.path.join(user_dir, "user_data", output_filename)
