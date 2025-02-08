class DockerBacktestError(Exception):
    """Exception raised when a backtest fails to run in Docker environment."""

    pass


class PickleableDockerException(Exception):
    def __init__(
        self,
        message,
        original_exception,
        command,
        stdout,
        stderr,
        exit_code,
    ):
        super().__init__(message)
        self.original_exception = str(original_exception)  # Ensure it's a string
        self.command = command
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code

    def __str__(self):
        return f"{self.args[0]}: {self.original_exception}"

    def __reduce__(self):
        return (self.__class__, (self.args[0], self.original_exception))


class DataDownloadTimeoutError(Exception):
    """Raised when data download times out."""

    def __init__(self, message: str, original_error: Exception | None = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)
