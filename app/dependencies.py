import jwt
from typing import Annotated

from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi import HTTPException, Depends, status

from app.db.utils.unitofwork import IUnitOfWork, UnitOfWork
from app.schemas.schema_users import UserSchemaAuth
from app.config import settings


async def check_auth(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(HTTPBearer())]
) -> UserSchemaAuth:
    if not settings.CLERK_JWT_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong",
        )

    if bearer := credentials.credentials:
        try:
            session = jwt.decode(
                bearer,
                key=settings.CLERK_JWT_KEY,
                leeway=1000000,
                algorithms=["RS256"],
            )
            return UserSchemaAuth(clerk_id=session["sub"])
        except jwt.exceptions.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate user",
            )
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate user",
    )


UOWDep = Annotated[IUnitOfWork, Depends(UnitOfWork)]
UserAuthDep = Annotated[UserSchemaAuth, Depends(check_auth)]
