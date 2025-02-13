from app.db.utils.decorators import require_user
from app.db.models.users import UsersORM
from app.schemas.schema_users import UserSchemaAdd
from app.db.utils.unitofwork import IUnitOfWork
from app.util.logger import setup_logger, set_user_id
from fastapi import HTTPException, status
from pydantic import ValidationError
from app.schemas.schema_user_settings import (
    UserSettingsSchema,
)
from app.util.ft.ft_config import FTUserConfig
from app.util.ft.ft_userdir import FTUserDir
from app.db.utils.user_ops import get_user_by_clerk_id

logger = setup_logger("services.users")


class UsersService:

    async def add_user(self, uow: IUnitOfWork, user: UserSchemaAdd):
        """
        Add a new user to the database.

        Args:
            uow (IUnitOfWork): The unit of work for database operations.
            user (UserSchemaAdd): The user data to be added.

        Returns:
            int: The ID of the newly added user.
        """
        logger.info(
            "Creating new user",
            extra={"data": {"clerk_id": user.clerk_id, "email": user.email}},
        )
        user_dict = user.model_dump()
        async with uow:
            try:
                user_id = await uow.users.add_one(user_dict)
                await uow.commit()

                # Set user ID in logging context
                set_user_id(user.clerk_id)

                logger.info(
                    "User created successfully",
                    extra={"data": {"user_id": user_id, "clerk_id": user.clerk_id}},
                )
                return user_id
            except Exception as e:
                logger.error(
                    "Error creating user",
                    extra={
                        "data": {
                            "clerk_id": user.clerk_id,
                            "error": str(e),
                            "error_type": type(e).__name__,
                        }
                    },
                )
                raise

    async def delete_user(self, uow: IUnitOfWork, clerk_id: str):
        """
        Delete a user by their clerk ID.

        Args:
            uow (IUnitOfWork): The unit of work for database operations.
            clerk_id (str): The clerk ID of the user to be deleted.
        """
        logger.info("Deleting user", extra={"data": {"clerk_id": clerk_id}})
        async with uow:
            try:
                user = await get_user_by_clerk_id(uow, clerk_id)
                if not user:
                    logger.warning(
                        "User not found for deletion",
                        extra={"data": {"clerk_id": clerk_id}},
                    )
                    return

                await uow.users.delete_one(user.id)
                await uow.commit()
                logger.info(
                    "User deleted successfully",
                    extra={"data": {"user_id": user.id, "clerk_id": clerk_id}},
                )
            except Exception as e:
                logger.error(
                    "Error deleting user",
                    extra={
                        "data": {
                            "clerk_id": clerk_id,
                            "error": str(e),
                            "error_type": type(e).__name__,
                        }
                    },
                )
                raise
