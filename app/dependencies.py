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


clerk_config = ClerkConfig(jwks_url=settings.CLERK_JWKS_URL)
clerk_auth_guard = ClerkHTTPBearer(config=clerk_config)


async def check_auth(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(clerk_auth_guard)]
):
    return UserSchemaAuth(clerk_id=credentials.decoded["sub"])


UOWDep = Annotated[IUnitOfWork, Depends(UnitOfWork)]
UserAuthDep = Annotated[UserSchemaAuth, Depends(check_auth)]
