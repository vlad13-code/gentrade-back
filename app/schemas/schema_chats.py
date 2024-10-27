from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field
from datetime import datetime


class ChatSchemaAdd(BaseModel):
    messages: list[dict]
    thread_id: str | UUID
    user_id: Optional[int] = Field(
        None
    )  # Optional because it's added in the router, not in the request. We're getting it from UserAuthDep


class ChatSchema(ChatSchemaAdd):
    id: int
    messages: list[dict]
    createdAt: datetime
    updatedAt: datetime


class ChatListItem(BaseModel):
    id: int
    thread_id: str | UUID
    createdAt: datetime
    updatedAt: datetime


class ResponseChatAdded(BaseModel):
    chat_id: int


class ResponseChatNotFound(BaseModel):
    detail: str = "Chat not found"
