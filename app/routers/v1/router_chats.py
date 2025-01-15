# pylint: disable=import-error
from fastapi import APIRouter, status

from app.dependencies import UOWDep, UserAuthDep
from app.schemas.schema_chats import (
    ChatListItemSchema,
    ChatSchemaAddUpdate,
    ChatSchema,
)
from app.db.services.service_chats import ChatsService

router = APIRouter(
    prefix="/chats",
    tags=["chats"],
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=ChatListItemSchema,
    summary="Add a new chat history",
)
async def add_chat(
    chat: ChatSchemaAddUpdate, uow: UOWDep, user: UserAuthDep
) -> ChatListItemSchema:
    chat = await ChatsService().add_chat(uow, chat, user)
    return chat


@router.patch(
    "",
    status_code=status.HTTP_200_OK,
    response_model=ChatSchema,
    summary="Update a chat history by id",
)
async def update_chat(
    chat: ChatSchemaAddUpdate,
    uow: UOWDep,
    user: UserAuthDep,
) -> ChatSchema:
    return await ChatsService().update_chat(uow, chat, user)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=list[ChatListItemSchema],
    summary="Get all chats histories for the current user. No messages, only ids and timestamps",
)
async def get_chat_list(
    uow: UOWDep,
    user: UserAuthDep,
) -> list[ChatListItemSchema]:
    return await ChatsService().get_chat_list(uow, user)


@router.get(
    "/{thread_id}",
    status_code=status.HTTP_200_OK,
    response_model=ChatSchema,
    summary="Get a chat history by id",
)
async def get_chat(
    uow: UOWDep,
    thread_id: str,
    user: UserAuthDep,
) -> ChatSchema:
    return await ChatsService().get_chat(uow, thread_id, user)


@router.delete(
    "/{thread_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a chat history by id",
)
async def delete_chat(
    uow: UOWDep,
    thread_id: str,
    user: UserAuthDep,
):
    await ChatsService().delete_chat(uow, thread_id, user)
