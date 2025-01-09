from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field
from datetime import datetime


class ChatSchemaAddUpdate(BaseModel):
    title: Optional[str]
    messages: list[dict]
    thread_id: str | UUID
    user_id: Optional[int] = Field(
        None
    )  # Optional because it's added in the router, not in the request. We're getting it from UserAuthDep


class ChatSchema(ChatSchemaAddUpdate):
    id: int
    messages: list[dict]
    createdAt: datetime
    updatedAt: datetime


class ChatListItemSchema(BaseModel):
    id: int
    thread_id: str | UUID
    title: str
    createdAt: datetime
    updatedAt: datetime


class ResponseChatAdded(BaseModel):
    chat_id: int


class ResponseChatNotFound(BaseModel):
    detail: str = "Chat not found"
