# pylint: disable=import-error
from fastapi import APIRouter, Response, status

from app.dependencies import UOWDep, UserAuthDep
from app.schemas.schema_chats import (
    ChatListItem,
    ChatSchemaAddUpdate,
    ChatSchema,
    ResponseChatAdded,
    ResponseChatNotFound,
)
from app.schemas.schema_users import ResponseUserNotFound
from app.db.services.service_chats import ChatsService

router = APIRouter(
    prefix="/chats",
    tags=["chats"],
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "model": ResponseChatAdded,
            "description": "Chat added successfully",
        },
    },
    summary="Add a new chat history",
)
async def add_chat(
    chat: ChatSchemaAddUpdate, uow: UOWDep, user: UserAuthDep, response: Response
):
    chat_id = await ChatsService().add_chat(uow, chat, user)
    if not chat_id:
        response.status_code = status.HTTP_404_NOT_FOUND
        return ResponseUserNotFound()

    response.status_code = status.HTTP_201_CREATED
    return ResponseChatAdded(chat_id=chat_id)


@router.patch(
    "",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_200_OK: {"model": ChatSchema}},
    summary="Update a chat history by id",
)
async def update_chat(
    chat: ChatSchemaAddUpdate,
    uow: UOWDep,
    user: UserAuthDep,
    response: Response,
):
    updated_chat = await ChatsService().update_chat(uow, chat, user)
    if not updated_chat:
        response.status_code = status.HTTP_404_NOT_FOUND
        return ResponseChatNotFound()
    return updated_chat


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_200_OK: {"model": list[ChatListItem]}},
    summary="Get all chats histories for the current user. No messages, only ids and timestamps",
)
async def get_chat_list(uow: UOWDep, response: Response, user: UserAuthDep):
    chats = await ChatsService().get_chat_list(uow, user.clerk_id)
    return chats


@router.get(
    "/{thread_id}",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_200_OK: {"model": ChatSchema}},
    summary="Get a chat history by id",
)
async def get_chat(uow: UOWDep, thread_id: str, response: Response):
    chat = await ChatsService().get_chat(uow, thread_id)
    if not chat:
        response.status_code = status.HTTP_404_NOT_FOUND
        return ResponseChatNotFound()
    return chat
