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
from app.util.logger import setup_logger, set_user_id

# Setup logger
logger = setup_logger("dependencies")

"""
Clerk authentication
"""
clerk_config = ClerkConfig(jwks_url=settings.CLERK_JWKS_URL)
clerk_auth_guard = ClerkHTTPBearer(config=clerk_config)


async def check_auth(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(clerk_auth_guard)]
) -> UserSchemaAuth:
    """
    Validate the authentication token and set up user context for logging.
    """
    clerk_id = credentials.decoded["sub"]
    # Set the user ID in the logging context
    set_user_id(clerk_id)

    logger.debug("User authenticated", extra={"data": {"clerk_id": clerk_id}})

    return UserSchemaAuth(clerk_id=clerk_id)


"""
Celery dependency
"""


async def get_celery_connector() -> AsyncGenerator[CeleryRMQConnector, None]:
    """
    FastAPI dependency that provides a CeleryRMQConnector instance.
    """
    connector = CeleryRMQConnector(settings.CELERY_BROKER_URL)
    try:
        logger.debug("Creating Celery RMQ connector")
        yield connector
    finally:
        if connector._rmq:
            logger.debug("Closing Celery RMQ connector")
            await connector._rmq.close()


UOWDep = Annotated[IUnitOfWork, Depends(UnitOfWork)]
UserAuthDep = Annotated[UserSchemaAuth, Depends(check_auth)]
CeleryDep = Annotated[CeleryRMQConnector, Depends(get_celery_connector)]
