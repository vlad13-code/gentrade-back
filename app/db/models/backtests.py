from sqlalchemy import String, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, Dict, Any

from app.db.db import Base
from app.db.models._common import intpk, created_at, updated_at


class BacktestsORM(Base):
    __tablename__ = "backtests"

    id: Mapped[intpk]
    strategy_id: Mapped[int] = mapped_column(
        ForeignKey("strategies.id", ondelete="CASCADE")
    )
    date_range: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), default="running")
    results: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    strategy = relationship("StrategiesORM", back_populates="backtests")

    def __repr__(self):
        return f"<BacktestsORM id={self.id}, strategy_id={self.strategy_id}>"
