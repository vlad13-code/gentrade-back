from sqlalchemy import String, TEXT, ForeignKey
from app.db.db import Base
from app.db.models._common import intpk, created_at, updated_at
from sqlalchemy.orm import Mapped, mapped_column, relationship


class StrategiesORM(Base):
    __tablename__ = "strategies"

    id: Mapped[intpk]
    name: Mapped[str] = mapped_column(String(255))
    file: Mapped[str] = mapped_column(String(255))
    code: Mapped[str] = mapped_column(TEXT)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    createdAt: Mapped[created_at]
    updatedAt: Mapped[updated_at]

    user = relationship("UsersORM", back_populates="strategies")

    def __repr__(self):
        return f"<StrategiesORM id={self.id}, name={self.name}>"
