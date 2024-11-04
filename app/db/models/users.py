from app.db.db import Base
from app.db.models._common import intpk, created_at, updated_at
from sqlalchemy.orm import Mapped
from typing import Optional
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String


class UsersORM(Base):
    __tablename__ = "users"

    id: Mapped[intpk]
    name: Mapped[Optional[str]]
    email: Mapped[Optional[str]]
    clerk_id: Mapped[str] = Column(String, unique=True)

    createdAt: Mapped[created_at]
    updatedAt: Mapped[updated_at]

    chats = relationship(
        "ChatsORM",
        back_populates="user",
        cascade="all, delete",
        passive_deletes=True,
    )

    def __repr__(self):
        return f"<UsersORM id={self.id}, name={self.name}, clerk_id={self.clerk_id}, email={self.email}, createdAt={self.createdAt},>"
