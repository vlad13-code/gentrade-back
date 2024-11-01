import logging
from app.db.models.users import UsersORM
from app.schemas.schema_users import UserSchemaAdd, UserSchema
from app.db.utils.unitofwork import IUnitOfWork


class UsersService:
    async def _get_user_by_clerk_id(
        self, uow: IUnitOfWork, clerk_id: str
    ) -> UsersORM | None:
        """
        Retrieve a user by their clerk ID.

        Args:
            uow (IUnitOfWork): The unit of work for database operations.
            clerk_id (str): The clerk ID of the user.

        Returns:
            UsersORM | None: The user object if found, otherwise None.
        """
        try:
            user = await uow.users.find_one(clerk_id=clerk_id)
            return user
        except Exception as e:
            logging.error(f"Error finding user with clerk_id {clerk_id}: {e}")

        return None

    async def add_user(self, uow: IUnitOfWork, user: UserSchemaAdd):
        """
        Add a new user to the database.

        Args:
            uow (IUnitOfWork): The unit of work for database operations.
            user (UserSchemaAdd): The user data to be added.

        Returns:
            int: The ID of the newly added user.
        """
        user_dict = user.model_dump()
        async with uow:
            user_id = await uow.users.add_one(user_dict)
            await uow.commit()
            return user_id

    async def delete_user(self, uow: IUnitOfWork, clerk_id: str):
        """
        Delete a user by their clerk ID.

        Args:
            uow (IUnitOfWork): The unit of work for database operations.
            clerk_id (str): The clerk ID of the user to be deleted.
        """
        async with uow:
            user = await self._get_user_by_clerk_id(uow, clerk_id)
            if not user:
                return
            await uow.users.delete_one(user.id)
            await uow.commit()
