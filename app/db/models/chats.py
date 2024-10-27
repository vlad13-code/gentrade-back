from sqlalchemy import JSON, UUID
from app.db.db import Base
from app.db.models._common import intpk, created_at, updated_at
from sqlalchemy.orm import Mapped, mapped_column


from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship


class ChatsORM(Base):
    __tablename__ = "chats"

    id: Mapped[intpk]
    createdAt: Mapped[created_at]
    updatedAt: Mapped[updated_at]
    messages = mapped_column(JSON)
    thread_id = mapped_column(UUID(as_uuid=True))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))

    user = relationship("UsersORM", back_populates="chats")

    def __repr__(self):
        return f"<Chat id={self.id}, createdAt={self.createdAt}, userId={self.userId}>"
