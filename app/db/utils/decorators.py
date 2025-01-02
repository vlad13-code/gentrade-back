from functools import wraps
from typing import Callable, TypeVar, ParamSpec
from fastapi import HTTPException, status

from app.db.models.users import UsersORM
from app.db.services.service_users import UsersService
from app.db.utils.unitofwork import UnitOfWork
from app.schemas.schema_users import UserSchemaAuth

P = ParamSpec("P")
R = TypeVar("R")


def require_user(func: Callable[P, R]) -> Callable[P, R]:
    """
    Decorator that handles user authentication by clerk_id.
    Injects authenticated UsersORM instance into the decorated function.
    Raises HTTPException with 401 status if user is not found.
    """

    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        # Find uow and user in arguments
        uow = next((arg for arg in args if isinstance(arg, UnitOfWork)), None)
        if not uow:
            uow = kwargs.get("uow")
            if not uow:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="UnitOfWork not found in arguments",
                )

        # Find user in both args and kwargs
        user_auth = next((arg for arg in args if isinstance(arg, UserSchemaAuth)), None)
        if not user_auth and "user" in kwargs:
            user_auth = kwargs["user"]
            if not isinstance(user_auth, UserSchemaAuth):
                return await func(*args, **kwargs)

        if not user_auth:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User authentication required",
            )

        async with uow:
            # Get authenticated user
            user: UsersORM = await UsersService()._get_user_by_clerk_id(
                uow, user_auth.clerk_id
            )
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or unauthorized",
                )

            # Create new args and kwargs with the authenticated user
            new_args = tuple(
                user if isinstance(arg, UserSchemaAuth) else arg for arg in args
            )
            new_kwargs = dict(kwargs)
            if "user" in new_kwargs and isinstance(new_kwargs["user"], UserSchemaAuth):
                new_kwargs["user"] = user

            return await func(*new_args, **new_kwargs)

    return wrapper
