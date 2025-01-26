class DockerBacktestError(Exception):
    """Exception raised when a backtest fails to run in Docker environment."""

    pass


class PickleableDockerException(Exception):
    def __init__(self, message, original_exception):
        super().__init__(message)
        self.original_exception = str(original_exception)  # Ensure it's a string

    def __str__(self):
        return f"{self.args[0]}: {self.original_exception}"

    def __reduce__(self):
        return (self.__class__, (self.args[0], self.original_exception))
