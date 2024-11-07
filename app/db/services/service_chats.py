# pylint: disable=import-error
from app.db.models.chats import ChatsORM
from app.db.services.service_users import UsersService
from app.schemas.schema_chats import ChatSchemaAddUpdate, ChatSchema, ChatListItem
from app.schemas.schema_users import UserSchemaAuth
from app.db.utils.unitofwork import IUnitOfWork
import logging


class ChatsService:
    async def add_chat(
        self, uow: IUnitOfWork, chat: ChatSchemaAddUpdate, user: UserSchemaAuth
    ) -> int | None:
        """
        Add a new chat to the database.

        Args:
            uow (IUnitOfWork): The unit of work for database operations.
            chat (ChatSchemaAddUpdate): The chat data to be added.
            user (UserSchemaAuth): The authenticated user.

        Returns:
            int: The ID of the newly added chat, or None if an error occurred.
        """
        async with uow:
            user = await UsersService()._get_user_by_clerk_id(uow, user.clerk_id)
            if not user:
                return None

            chat.user_id = user.id
            chat_dict = chat.model_dump()
            try:
                chat_id = await uow.chats.add_one(chat_dict)
                await uow.commit()
                return chat_id
            except Exception as e:
                logging.error(f"Error adding chat: {e}")
                return None

    async def update_chat(
        self, uow: IUnitOfWork, chat: ChatSchemaAddUpdate, user: UserSchemaAuth
    ) -> int | None:
        """
        Update an existing chat in the database.

        Args:
            uow (IUnitOfWork): The unit of work for database operations.
            chat (ChatSchemaAddUpdate): The updated chat data.
            user (UserSchemaAuth): The authenticated user.

        Returns:
            int: The ID of the updated chat, or None if an error occurred.
        """
        async with uow:
            user = await UsersService()._get_user_by_clerk_id(uow, user.clerk_id)
            if not user:
                return None

            chat.user_id = user.id
            chat_dict = chat.model_dump()
            try:
                existing_chat: ChatsORM = await uow.chats.find_one(
                    thread_id=chat.thread_id
                )
                chat_id = await uow.chats.edit_one(existing_chat.id, chat_dict)
                await uow.commit()
                return chat_id
            except Exception as e:
                logging.error(f"Error updating chat: {e}")
                return None

    async def get_chat_list(
        self, uow: IUnitOfWork, clerk_id: str
    ) -> list[ChatListItem] | None:
        """
        Retrieve a list of chats for a user, ordered by update time.

        Args:
            uow (IUnitOfWork): The unit of work for database operations.
            clerk_id (str): The clerk ID of the user.

        Returns:
            list[ChatListItem]: A list of chat list items for the user.
        """
        async with uow:
            user = await UsersService()._get_user_by_clerk_id(uow, clerk_id)
            if not user:
                return []

            try:
                chats = await uow.chats.find_all_by_ordered(
                    order_by="updatedAt", order_direction="desc", user_id=user.id
                )
                return [
                    ChatListItem.model_validate(chat, from_attributes=True)
                    for chat in chats
                ]
            except Exception as e:
                logging.error(
                    f"Error retrieving chat list for clerk_id {clerk_id}: {e}"
                )
                return []

    async def get_chat(self, uow: IUnitOfWork, thread_id: str) -> ChatSchema | None:
        """
        Retrieve a specific chat by its thread ID.

        Args:
            uow (IUnitOfWork): The unit of work for database operations.
            thread_id (str): The thread ID of the chat.

        Returns:
            ChatSchema: The chat schema if found, otherwise None.
        """
        async with uow:
            try:
                chat: ChatsORM = await uow.chats.find_one(thread_id=thread_id)
                return ChatSchema.model_validate(chat, from_attributes=True)
            except Exception as e:
                logging.error(f"Error retrieving chat with thread_id {thread_id}: {e}")
                return None

    async def delete_chat(
        self, uow: IUnitOfWork, thread_id: str, user: UserSchemaAuth
    ) -> bool | None:
        """
        Delete a chat if the user is authorized.

        Args:
            uow (IUnitOfWork): The unit of work for database operations.
            thread_id (str): The thread ID of the chat to be deleted.
            user (UserSchemaAuth): The authenticated user.

        Returns:
            bool: True if the chat was successfully deleted, False otherwise.
        """
        async with uow:
            user = await UsersService()._get_user_by_clerk_id(uow, user.clerk_id)
            if not user:
                return False

            try:
                chat: ChatsORM = await uow.chats.find_one(thread_id=thread_id)
                if chat.user_id != user.id:
                    logging.error(
                        f"User {user.id} is not authorized to delete chat {thread_id}"
                    )
                    return False

                await uow.chats.delete_one(chat.id)
                # Delete all LangGraph related entries
                await uow.checkpoint.delete_one_by(thread_id=thread_id)
                await uow.checkpoint_write.delete_one_by(thread_id=thread_id)
                await uow.checkpoint_blob.delete_one_by(thread_id=thread_id)
                await uow.commit()
                return True
            except Exception as e:
                logging.error(f"Error deleting chat with thread_id {thread_id}: {e}")
                return False
