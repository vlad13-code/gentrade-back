# pylint: disable=import-error
from fastapi import HTTPException, status
from app.db.models.chats import ChatsORM
from app.schemas.schema_chats import ChatSchemaAddUpdate, ChatSchema, ChatListItemSchema
from app.db.utils.unitofwork import IUnitOfWork
from app.db.models.users import UsersORM
from app.db.utils.decorators import require_user
import logging


class ChatsService:
    @require_user
    async def add_chat(
        self, uow: IUnitOfWork, chat: ChatSchemaAddUpdate, user: UsersORM
    ) -> ChatListItemSchema:
        async with uow:
            chat.user_id = user.id
            chat_dict = chat.model_dump()
            try:
                chat = await uow.chats.add_one(chat_dict)
                await uow.commit()
                chat_list_item = ChatListItemSchema.model_validate(
                    chat, from_attributes=True
                )
                return chat_list_item
            except Exception as e:
                logging.error(f"Error adding chat: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to add chat",
                )

    @require_user
    async def update_chat(
        self, uow: IUnitOfWork, chat: ChatSchemaAddUpdate, user: UsersORM
    ) -> ChatSchema:
        async with uow:
            chat.user_id = user.id
            chat_dict = chat.model_dump()
            try:
                existing_chat: ChatsORM = await uow.chats.find_one(
                    thread_id=chat.thread_id
                )
                if not existing_chat:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found"
                    )
                if existing_chat.user_id != user.id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Not authorized to update this chat",
                    )

                if not chat.title:
                    chat_dict["title"] = existing_chat.title

                await uow.chats.edit_one(existing_chat.id, chat_dict)
                await uow.commit()

                # Fetch the updated chat to return
                updated_chat = await uow.chats.find_one(id=existing_chat.id)
                return ChatSchema.model_validate(updated_chat, from_attributes=True)
            except Exception as e:
                logging.error(f"Error updating chat: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update chat",
                )

    @require_user
    async def get_chat_list(
        self, uow: IUnitOfWork, user: UsersORM
    ) -> list[ChatListItemSchema]:
        async with uow:
            try:
                chats = await uow.chats.find_all_by_ordered(
                    order_by="updatedAt", order_direction="desc", user_id=user.id
                )
                return [
                    ChatListItemSchema.model_validate(chat, from_attributes=True)
                    for chat in chats
                ]
            except Exception as e:
                logging.error(f"Error retrieving chat list for user {user.id}: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to retrieve chat list",
                )

    @require_user
    async def get_chat(
        self, uow: IUnitOfWork, thread_id: str, user: UsersORM
    ) -> ChatSchema:
        async with uow:
            try:
                chat: ChatsORM = await uow.chats.find_one(thread_id=thread_id)
                if not chat:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found"
                    )
                if chat.user_id != user.id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Not authorized to access this chat",
                    )
                return ChatSchema.model_validate(chat, from_attributes=True)
            except Exception as e:
                logging.error(f"Error retrieving chat with thread_id {thread_id}: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to retrieve chat",
                )

    @require_user
    async def delete_chat(
        self, uow: IUnitOfWork, thread_id: str, user: UsersORM
    ) -> None:
        async with uow:
            try:
                chat: ChatsORM = await uow.chats.find_one(thread_id=thread_id)
                if not chat:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found"
                    )
                if chat.user_id != user.id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Not authorized to delete this chat",
                    )

                await uow.chats.delete_one(chat.id)
                # Delete all LangGraph related entries
                await uow.checkpoint.delete_one_by(thread_id=thread_id)
                await uow.checkpoint_write.delete_one_by(thread_id=thread_id)
                await uow.checkpoint_blob.delete_one_by(thread_id=thread_id)
                await uow.commit()
            except Exception as e:
                logging.error(f"Error deleting chat with thread_id {thread_id}: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to delete chat",
                )
