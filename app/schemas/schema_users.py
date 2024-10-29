from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class UserSchemaAuth(BaseModel):
    clerk_id: str


class UserSchemaAdd(UserSchemaAuth):
    name: Optional[str]
    email: Optional[str]


class UserSchema(UserSchemaAuth):
    id: int
    createdAt: datetime
    updatedAt: datetime


class ResponseUserNotFound(BaseModel):
    description: str = "User not found"
