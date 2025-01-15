from sqlalchemy import JSON, String, TEXT, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.db import Base
from app.db.models._common import intpk, created_at, updated_at


class StrategiesORM(Base):
    __tablename__ = "strategies"

    id: Mapped[intpk]
    name: Mapped[str] = mapped_column(String(255))
    file: Mapped[str] = mapped_column(String(255))
    code: Mapped[str] = mapped_column(TEXT)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    draft = mapped_column(JSON)
    chat_id: Mapped[int] = mapped_column(
        ForeignKey("chats.id", ondelete="SET NULL"), nullable=True
    )

    createdAt: Mapped[created_at]
    updatedAt: Mapped[updated_at]

    user = relationship("UsersORM", back_populates="strategies")
    chat = relationship("ChatsORM", back_populates="strategies")
    backtests = relationship("BacktestsORM", back_populates="strategy")

    def __repr__(self):
        return f"<StrategiesORM id={self.id}, name={self.name}>"
