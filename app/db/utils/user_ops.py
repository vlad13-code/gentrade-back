from app.db.models.users import UsersORM
from app.db.utils.unitofwork import IUnitOfWork
from app.util.logger import setup_logger

logger = setup_logger("utils.user_ops")


async def get_user_by_clerk_id(uow: IUnitOfWork, clerk_id: str) -> UsersORM | None:
    """
    Retrieve a user by their clerk ID.

    Args:
        uow (IUnitOfWork): The unit of work for database operations.
        clerk_id (str): The clerk ID of the user.

    Returns:
        UsersORM | None: The user object if found, otherwise None.
    """
    try:
        logger.debug(
            "Looking up user by clerk ID", extra={"data": {"clerk_id": clerk_id}}
        )
        user = await uow.users.find_one(clerk_id=clerk_id)
        if user:
            logger.debug(
                "User found",
                extra={"data": {"clerk_id": clerk_id, "user_id": user.id}},
            )
        else:
            logger.debug("User not found", extra={"data": {"clerk_id": clerk_id}})
        return user
    except Exception as e:
        logger.error(
            "Error finding user",
            extra={
                "data": {
                    "clerk_id": clerk_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            },
        )
    return None
