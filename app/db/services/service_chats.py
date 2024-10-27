# pylint: disable=import-error
from app.db.models.chats import ChatsORM
from app.db.models.users import UsersORM
from app.schemas.schema_chats import ChatSchemaAdd, ChatSchema, ChatListItem
from app.schemas.schema_users import UserSchemaAuth
from app.db.utils.unitofwork import IUnitOfWork


class ChatsService:
    async def add_or_update_chat(
        self, uow: IUnitOfWork, chat: ChatSchemaAdd, user: UserSchemaAuth
    ):
        async with uow:
            try:
                user: UsersORM = await uow.users.find_one(clerk_id=user.clerk_id)
                chat.user_id = user.id
            except Exception:
                return None

            chat_dict = chat.model_dump()
            try:
                existing_chat: ChatsORM = await uow.chats.find_one(
                    thread_id=chat.thread_id
                )
                chat_id = await uow.chats.edit_one(existing_chat.id, chat_dict)
            except Exception as e:
                chat_id = await uow.chats.add_one(chat_dict)

            await uow.commit()
            return chat_id

    async def get_chats(self, uow: IUnitOfWork, clerk_id: str):
        async with uow:
            chats = await uow.chats.find_all_by(user_id=clerk_id)
            chats = [
                ChatSchema.model_validate(chat, from_attributes=True) for chat in chats
            ]
            return chats

    async def get_chat_list(
        self, uow: IUnitOfWork, clerk_id: str
    ) -> list[ChatListItem]:
        async with uow:
            user: UsersORM = await uow.users.find_one(clerk_id=clerk_id)
            chats = await uow.chats.find_all_by(user_id=user.id)
            chats = [
                ChatListItem.model_validate(chat, from_attributes=True)
                for chat in chats
            ]
            return chats

    async def get_chat(self, uow: IUnitOfWork, thread_id: str):
        async with uow:
            try:
                chat: ChatsORM = await uow.chats.find_one(thread_id=thread_id)
                chat = ChatSchema.model_validate(chat, from_attributes=True)
            except Exception:
                return None
            return chat
