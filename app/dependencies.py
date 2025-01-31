from typing import Annotated

from fastapi import Depends

from fastapi_clerk_auth import (
    ClerkConfig,
    ClerkHTTPBearer,
    HTTPAuthorizationCredentials,
)

from app.db.utils.unitofwork import IUnitOfWork, UnitOfWork
from app.schemas.schema_users import UserSchemaAuth
from app.config import settings
from typing import AsyncGenerator

from app.celery.celery_rmq_connector import CeleryRMQConnector

"""
Clerk authentication
"""
clerk_config = ClerkConfig(jwks_url=settings.CLERK_JWKS_URL)
clerk_auth_guard = ClerkHTTPBearer(config=clerk_config)


async def check_auth(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(clerk_auth_guard)]
):
    return UserSchemaAuth(clerk_id=credentials.decoded["sub"])


"""
Celery dependency
"""


async def get_celery_connector() -> AsyncGenerator[CeleryRMQConnector, None]:
    """
    FastAPI dependency that provides a CeleryRMQConnector instance.
    """
    connector = CeleryRMQConnector(settings.CELERY_BROKER_URL)
    try:
        yield connector
    finally:
        if connector._rmq:
            await connector._rmq.close()


UOWDep = Annotated[IUnitOfWork, Depends(UnitOfWork)]
UserAuthDep = Annotated[UserSchemaAuth, Depends(check_auth)]
CeleryDep = Annotated[CeleryRMQConnector, Depends(get_celery_connector)]
