from functools import wraps
from typing import Callable, TypeVar, ParamSpec
from fastapi import HTTPException, status

from app.db.models.users import UsersORM
from app.db.services.service_users import UsersService
from app.db.utils.unitofwork import IUnitOfWork
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
        uow = next((arg for arg in args if isinstance(arg, IUnitOfWork)), None)
        if not uow:
            uow = kwargs.get("uow")

        user_auth = next((arg for arg in args if isinstance(arg, UserSchemaAuth)), None)
        if not user_auth:
            user_auth = kwargs.get("user")

        if not uow or not user_auth:
            return await func(*args, **kwargs)

        # Get authenticated user
        user: UsersORM = await UsersService()._get_user_by_clerk_id(
            uow, user_auth.clerk_id
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or unauthorized",
            )

        # Replace UserSchemaAuth with UsersORM in args/kwargs
        new_args = [user if isinstance(arg, UserSchemaAuth) else arg for arg in args]
        new_kwargs = {
            k: user if isinstance(v, UserSchemaAuth) else v for k, v in kwargs.items()
        }

        return await func(*new_args, **new_kwargs)

    return wrapper
