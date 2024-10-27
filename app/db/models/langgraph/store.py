from sqlalchemy import Column, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.db.db import Base


class Store(Base):
    __tablename__ = "store"

    prefix = Column(Text, primary_key=True)
    key = Column(Text, primary_key=True)
    value = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
