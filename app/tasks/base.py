from celery import Task
import time
from typing import Any

from app.util.logger import setup_logger, set_correlation_id

logger = setup_logger("tasks.base")


class BaseTask(Task):
    """Base task class that includes logging functionality."""

    def log_task_start(self, args: Any, kwargs: Any) -> None:
        """Log the start of a task."""
        logger.info(
            f"Starting task {self.name}",
            extra={
                "data": {
                    "task_id": self.request.id,
                    "task_name": self.name,
                    "args": args,
                    "kwargs": kwargs,
                }
            },
        )

    def log_task_success(self, start_time: float) -> None:
        """Log the successful completion of a task."""
        duration = time.time() - start_time
        logger.info(
            f"Task {self.name} completed successfully",
            extra={
                "data": {
                    "task_id": self.request.id,
                    "task_name": self.name,
                    "duration": f"{duration:.3f}s",
                }
            },
        )

    def log_task_failure(self, start_time: float, error: Exception) -> None:
        """Log the failure of a task."""
        duration = time.time() - start_time
        logger.error(
            f"Task {self.name} failed",
            extra={
                "data": {
                    "task_id": self.request.id,
                    "task_name": self.name,
                    "error": str(error),
                    "duration": f"{duration:.3f}s",
                }
            },
        )

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Override to add logging around task execution."""
        headers = self.request.headers or {}
        correlation_id = headers.get("correlation_id")
        if correlation_id:
            set_correlation_id(correlation_id)

        start_time = time.time()
        self.log_task_start(args, kwargs)

        try:
            result = super().__call__(*args, **kwargs)
            self.log_task_success(start_time)
            return result

        except Exception as e:
            self.log_task_failure(start_time, e)
            raise

    def on_retry(
        self, exc: Exception, task_id: str, args: Any, kwargs: Any, einfo: Any
    ) -> None:
        """Called when the task is to be retried."""
        logger.warning(
            f"Retrying task {self.name}",
            extra={
                "data": {
                    "task_id": task_id,
                    "task_name": self.name,
                    "error": str(exc),
                    "args": args,
                    "kwargs": kwargs,
                }
            },
        )

    def on_failure(
        self, exc: Exception, task_id: str, args: Any, kwargs: Any, einfo: Any
    ) -> None:
        """Called when the task fails."""
        logger.error(
            f"Task {self.name} failed permanently",
            extra={
                "data": {
                    "task_id": task_id,
                    "task_name": self.name,
                    "error": str(exc),
                    "args": args,
                    "kwargs": kwargs,
                }
            },
        )


# Example usage:
# @app.task(base=LoggedTask)
# def my_task():
#     pass
