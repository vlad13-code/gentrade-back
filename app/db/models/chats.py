from sqlalchemy import JSON, UUID
from app.db.db import Base
from app.db.models._common import intpk, created_at, updated_at
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey

# Import the module where StrategiesORM is defined
from app.db.models.strategies import StrategiesORM


class ChatsORM(Base):
    __tablename__ = "chats"

    id: Mapped[intpk]
    title: Mapped[str]
    thread_id = mapped_column(UUID(as_uuid=True), unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    messages = mapped_column(JSON)

    createdAt: Mapped[created_at]
    updatedAt: Mapped[updated_at]

    user = relationship("UsersORM", back_populates="chats")

    strategy = relationship(
        "StrategiesORM",
        back_populates="chat",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<ChatsORM id={self.id}, thread_id={self.thread_id}, user_id={self.user_id} createdAt={self.createdAt},>"
