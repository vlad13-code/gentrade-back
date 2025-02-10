import asyncio
import celery
import celery.states
from app.celery.celery_rmq_connector import CeleryRMQConnector
from app.config import settings
import traceback
import logging
from app.tasks.base import BaseTask
import time

logger = logging.getLogger(__name__)


class AsyncTask(BaseTask):
    async def apply_async(self, *args, **kwargs):
        """Asynchronously send a task to the queue"""
        app: AsyncCelery = self._get_app()
        return await app.send_task(self.name, args=args, kwargs=kwargs)

    async def async_run(self, *args, **kwargs):
        """Run the task asynchronously"""

        # Set correlation_id from kwargs if present
        correlation_id = kwargs.get("correlation_id")
        if correlation_id:
            from app.util.logger import set_correlation_id

            set_correlation_id(correlation_id)

        start_time = time.time()
        self.log_task_start(args, kwargs)
        try:
            result = await self.run(*args, **kwargs)
            self.update_state(state=celery.states.SUCCESS)
            self.log_task_success(start_time)
            return result
        except Exception as exc:
            self.update_state(
                state=celery.states.FAILURE,
                meta={
                    "exc_type": type(exc).__name__,
                    "exc_message": str(exc),
                    "traceback": traceback.format_exc(),
                },
            )
            self.log_task_failure(start_time, exc)
            raise

    def __call__(self, *args, **kwargs):
        """Override to run async tasks in the event loop"""
        # Set correlation_id from kwargs if present
        correlation_id = kwargs.get("correlation_id")
        if correlation_id:
            from app.util.logger import set_correlation_id

            set_correlation_id(correlation_id)

        return self._get_app().loop.run_until_complete(self.async_run(*args, **kwargs))

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when the task fails"""
        super().on_failure(exc, task_id, args, kwargs, einfo)


class AsyncCelery(celery.Celery):
    task_cls = AsyncTask

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._loop = None
        self._rmq_connector = None

    @property
    def loop(self):
        if self._loop is None:
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
        return self._loop

    @property
    def rmq_connector(self):
        if self._rmq_connector is None:
            self._rmq_connector = CeleryRMQConnector(self.conf.broker_url)
        return self._rmq_connector

    async def send_task(self, name, args=None, kwargs=None, **options):
        """Send a task message asynchronously"""
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}

        task_id = await self.rmq_connector.send_task(
            task_name=name,
            queue_name=options.get("queue", "celery"),
            task_kwargs=kwargs,
            expires=options.get("expires"),
        )
        return task_id


celery_app = AsyncCelery(
    "gentrade",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.backtests"],
)

celery_app.conf.update(
    worker_redirect_stdouts=False,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
