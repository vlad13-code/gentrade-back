# pylint: disable=import-error
from app.db.models.chats import ChatsORM
from app.db.models.users import UsersORM
from app.schemas.schema_chats import ChatSchemaAddUpdate, ChatSchema, ChatListItem
from app.schemas.schema_users import UserSchemaAuth
from app.db.utils.unitofwork import IUnitOfWork
import logging


class ChatsService:
    async def _get_user_by_clerk_id(self, uow: IUnitOfWork, clerk_id: str) -> UsersORM:
        try:
            user = await uow.users.find_one(clerk_id=clerk_id)
            return user
        except Exception as e:
            logging.error(f"Error finding user with clerk_id {clerk_id}: {e}")

        return None

    async def add_chat(
        self, uow: IUnitOfWork, chat: ChatSchemaAddUpdate, user: UserSchemaAuth
    ) -> int:
        async with uow:
            user = await self._get_user_by_clerk_id(uow, user.clerk_id)
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
    ) -> int:
        async with uow:
            user = await self._get_user_by_clerk_id(uow, user.clerk_id)
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

    async def get_chats(self, uow: IUnitOfWork, clerk_id: str) -> list[ChatSchema]:
        async with uow:
            try:
                chats = await uow.chats.find_all_by(user_id=clerk_id)
                return [
                    ChatSchema.model_validate(chat, from_attributes=True)
                    for chat in chats
                ]
            except Exception as e:
                logging.error(f"Error retrieving chats for clerk_id {clerk_id}: {e}")
                return []

    async def get_chat_list(
        self, uow: IUnitOfWork, clerk_id: str
    ) -> list[ChatListItem]:
        async with uow:
            user = await self._get_user_by_clerk_id(uow, clerk_id)
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

    async def get_chat(self, uow: IUnitOfWork, thread_id: str) -> ChatSchema:
        async with uow:
            try:
                chat: ChatsORM = await uow.chats.find_one(thread_id=thread_id)
                return ChatSchema.model_validate(chat, from_attributes=True)
            except Exception as e:
                logging.error(f"Error retrieving chat with thread_id {thread_id}: {e}")
                return None
