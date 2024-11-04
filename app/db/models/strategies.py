from sqlalchemy import String
from app.db.db import Base
from app.db.models._common import intpk, created_at, updated_at
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey


class StrategiesORM(Base):
    __tablename__ = "strategies"

    id: Mapped[intpk]
    name: Mapped[str] = mapped_column(String(255))
    file: Mapped[str] = mapped_column(String(255))
    chat_id: Mapped[int] = mapped_column(
        ForeignKey("chats.id", ondelete="CASCADE"), unique=True
    )

    createdAt: Mapped[created_at]
    updatedAt: Mapped[updated_at]

    chat = relationship("ChatsORM", back_populates="strategy", uselist=False)

    def __repr__(self):
        return f"<StrategiesORM id={self.id}, name={self.name}, chat_id={self.chat_id}>"
