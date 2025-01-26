from typing import AsyncGenerator
from fastapi import Depends

from app.celery_rmq_connector import CeleryRMQConnector
from app.config import settings


async def get_celery_connector() -> AsyncGenerator[CeleryRMQConnector, None]:
    """
    FastAPI dependency that provides a CeleryRMQConnector instance.
    Usage:
        @router.post("/endpoint")
        async def endpoint(
            celery: CeleryRMQConnector = Depends(get_celery_connector)
        ):
            ...
    """
    connector = CeleryRMQConnector(settings.CELERY_BROKER_URL)
    try:
        yield connector
    finally:
        if connector._rmq:
            await connector._rmq.close()
