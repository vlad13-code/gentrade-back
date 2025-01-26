from python_on_whales import DockerClient
import os
import uuid
from app.util.ft_userdir import get_user_data_directory
from app.util.exceptions import PickleableDockerException


def run_backtest_in_docker(
    strategy_class_name: str, clerk_id: str, date_range: str
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
    try:
        docker.compose.run(
            "freqtrade",
            [
                "backtesting",
                "--userdir",
                "user_data",
                "--strategy",
                strategy_class_name,
                "--timerange",
                date_range,
                "--export",
                "trades",
                # "--export-filename",
                # output_filename,
            ],
            remove=True,
        )
    except Exception as e:
        raise PickleableDockerException("Docker command failed", e)

    # Construct the full path to the result inside user_data
    result_path = os.path.join(user_dir, "user_data", output_filename)

    if not os.path.exists(result_path):
        raise PickleableDockerException(
            f"Backtest result file not found at {result_path}", None
        )

    return result_path


if __name__ == "__main__":
    print(
        run_backtest_in_docker(
            "XrpTradingStrategy",
            "2oFuvIYD6fvQwokCEb61laEDjoM",
            "20250110-20250117",
        )
    )
