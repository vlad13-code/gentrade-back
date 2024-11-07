# pylint: disable=import-error
from fastapi import APIRouter, Request, Response, status

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
    """
    Add a new chat history.

    Args:
        chat (ChatSchemaAddUpdate): The chat data to add.
        uow (UOWDep): Unit of work dependency.
        user (UserAuthDep): User authentication dependency.
        response (Response): FastAPI response object.

    Returns:
        ResponseChatAdded: If the chat is added successfully.
        ResponseUserNotFound: If the chat could not be added.
    """
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
    """
    Update a chat history by id.

    Args:
        chat (ChatSchemaAddUpdate): The chat data to update.
        uow (UOWDep): Unit of work dependency.
        user (UserAuthDep): User authentication dependency.
        response (Response): FastAPI response object.

    Returns:
        ChatSchema: The updated chat data.
        ResponseChatNotFound: If the chat could not be found.
    """
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
    """
    Get all chat histories for the current user.

    Args:
        uow (UOWDep): Unit of work dependency.
        response (Response): FastAPI response object.
        user (UserAuthDep): User authentication dependency.

    Returns:
        list[ChatListItem]: List of chat items with ids and timestamps.
    """
    chats = await ChatsService().get_chat_list(uow, user.clerk_id)
    return chats


@router.get(
    "/{thread_id}",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_200_OK: {"model": ChatSchema}},
    summary="Get a chat history by id",
)
async def get_chat(
    uow: UOWDep, thread_id: str, response: Response, user: UserAuthDep, request: Request
):
    """
    Get a chat history by id.

    Args:
        uow (UOWDep): Unit of work dependency.
        thread_id (str): The id of the chat thread.
        response (Response): FastAPI response object.

    Returns:
        ChatSchema: The chat data.
        ResponseChatNotFound: If the chat could not be found.
    """
    # graph = request.app.state.agent
    # graph_state = await graph.aget_state({"configurable": {"thread_id": thread_id}})
    chat = await ChatsService().get_chat(uow, thread_id)
    if not chat:
        response.status_code = status.HTTP_404_NOT_FOUND
        return ResponseChatNotFound()
    return chat


@router.delete(
    "/{thread_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {"description": "Chat deleted successfully"},
        status.HTTP_404_NOT_FOUND: {"model": ResponseChatNotFound},
    },
    summary="Delete a chat history by id",
)
async def delete_chat(
    uow: UOWDep, thread_id: str, response: Response, user: UserAuthDep
):
    """
    Delete a chat history by id.

    Args:
        uow (UOWDep): Unit of work dependency.
        thread_id (str): The id of the chat thread.
        response (Response): FastAPI response object.
        user (UserAuthDep): User authentication dependency.

    Returns:
        Response: HTTP 204 if successful, ResponseChatNotFound if not found.
    """
    success = await ChatsService().delete_chat(uow, thread_id, user)
    if not success:
        response.status_code = status.HTTP_404_NOT_FOUND
        return ResponseChatNotFound()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
