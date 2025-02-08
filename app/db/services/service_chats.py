# pylint: disable=import-error
from fastapi import HTTPException, status
from app.db.models.chats import ChatsORM
from app.schemas.schema_chats import ChatSchemaAddUpdate, ChatSchema, ChatListItemSchema
from app.db.utils.unitofwork import IUnitOfWork
from app.db.models.users import UsersORM
from app.db.utils.decorators import require_user
from app.util.logger import setup_logger

logger = setup_logger("services.chats")


class ChatsService:
    @require_user
    async def add_chat(
        self, uow: IUnitOfWork, chat: ChatSchemaAddUpdate, user: UsersORM
    ) -> ChatListItemSchema:
        logger.info(
            "Creating new chat",
            extra={"data": {"thread_id": chat.thread_id, "title": chat.title}},
        )
        async with uow:
            chat.user_id = user.id
            chat_dict = chat.model_dump()
            try:
                chat = await uow.chats.add_one(chat_dict)
                await uow.commit()
                chat_list_item = ChatListItemSchema.model_validate(
                    chat, from_attributes=True
                )
                logger.info(
                    "Chat created successfully",
                    extra={"data": {"chat_id": chat.id, "thread_id": chat.thread_id}},
                )
                return chat_list_item
            except Exception as e:
                logger.error(
                    "Error adding chat",
                    extra={
                        "data": {
                            "error": str(e),
                            "error_type": type(e).__name__,
                            "thread_id": chat.thread_id,
                        }
                    },
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to add chat",
                )

    @require_user
    async def update_chat(
        self, uow: IUnitOfWork, chat: ChatSchemaAddUpdate, user: UsersORM
    ) -> ChatSchema:
        logger.info(
            "Updating chat",
            extra={"data": {"thread_id": chat.thread_id, "title": chat.title}},
        )
        async with uow:
            chat.user_id = user.id
            chat_dict = chat.model_dump()
            try:
                existing_chat: ChatsORM = await uow.chats.find_one(
                    thread_id=chat.thread_id
                )
                if not existing_chat:
                    logger.warning(
                        "Chat not found", extra={"data": {"thread_id": chat.thread_id}}
                    )
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found"
                    )
                if existing_chat.user_id != user.id:
                    logger.warning(
                        "Unauthorized chat update attempt",
                        extra={
                            "data": {
                                "thread_id": chat.thread_id,
                                "chat_id": existing_chat.id,
                                "requesting_user_id": user.id,
                                "chat_owner_id": existing_chat.user_id,
                            }
                        },
                    )
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
                logger.info(
                    "Chat updated successfully",
                    extra={
                        "data": {
                            "chat_id": updated_chat.id,
                            "thread_id": updated_chat.thread_id,
                        }
                    },
                )
                return ChatSchema.model_validate(updated_chat, from_attributes=True)
            except Exception as e:
                logger.error(
                    "Error updating chat",
                    extra={
                        "data": {
                            "error": str(e),
                            "error_type": type(e).__name__,
                            "thread_id": chat.thread_id,
                        }
                    },
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update chat",
                )

    @require_user
    async def get_chat_list(
        self, uow: IUnitOfWork, user: UsersORM
    ) -> list[ChatListItemSchema]:
        logger.info("Fetching chat list")
        async with uow:
            try:
                chats = await uow.chats.find_all_by_ordered(
                    order_by="updatedAt", order_direction="desc", user_id=user.id
                )
                logger.info(
                    f"Retrieved {len(chats)} chats",
                    extra={
                        "data": {
                            "count": len(chats),
                            "chat_ids": [chat.id for chat in chats],
                        }
                    },
                )
                return [
                    ChatListItemSchema.model_validate(chat, from_attributes=True)
                    for chat in chats
                ]
            except Exception as e:
                logger.error(
                    "Error retrieving chat list",
                    extra={"data": {"error": str(e), "error_type": type(e).__name__}},
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to retrieve chat list",
                )

    @require_user
    async def get_chat(
        self, uow: IUnitOfWork, thread_id: str, user: UsersORM
    ) -> ChatSchema:
        logger.info("Fetching chat", extra={"data": {"thread_id": thread_id}})
        async with uow:
            try:
                chat: ChatsORM = await uow.chats.find_one(thread_id=thread_id)
                if not chat:
                    logger.warning(
                        "Chat not found", extra={"data": {"thread_id": thread_id}}
                    )
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found"
                    )
                if chat.user_id != user.id:
                    logger.warning(
                        "Unauthorized chat access attempt",
                        extra={
                            "data": {
                                "thread_id": thread_id,
                                "chat_id": chat.id,
                                "requesting_user_id": user.id,
                                "chat_owner_id": chat.user_id,
                            }
                        },
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Not authorized to access this chat",
                    )
                logger.info(
                    "Chat retrieved successfully",
                    extra={
                        "data": {
                            "chat_id": chat.id,
                            "thread_id": chat.thread_id,
                            "message_count": len(chat.messages) if chat.messages else 0,
                        }
                    },
                )
                return ChatSchema.model_validate(chat, from_attributes=True)
            except Exception as e:
                logger.error(
                    "Error retrieving chat",
                    extra={
                        "data": {
                            "error": str(e),
                            "error_type": type(e).__name__,
                            "thread_id": thread_id,
                        }
                    },
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to retrieve chat",
                )

    @require_user
    async def delete_chat(
        self, uow: IUnitOfWork, thread_id: str, user: UsersORM
    ) -> None:
        logger.info("Deleting chat", extra={"data": {"thread_id": thread_id}})
        async with uow:
            try:
                chat: ChatsORM = await uow.chats.find_one(thread_id=thread_id)
                if not chat:
                    logger.warning(
                        "Chat not found", extra={"data": {"thread_id": thread_id}}
                    )
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found"
                    )
                if chat.user_id != user.id:
                    logger.warning(
                        "Unauthorized chat deletion attempt",
                        extra={
                            "data": {
                                "thread_id": thread_id,
                                "chat_id": chat.id,
                                "requesting_user_id": user.id,
                                "chat_owner_id": chat.user_id,
                            }
                        },
                    )
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
                logger.info(
                    "Chat deleted successfully",
                    extra={"data": {"chat_id": chat.id, "thread_id": thread_id}},
                )
            except Exception as e:
                logger.error(
                    "Error deleting chat",
                    extra={
                        "data": {
                            "error": str(e),
                            "error_type": type(e).__name__,
                            "thread_id": thread_id,
                        }
                    },
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to delete chat",
                )
