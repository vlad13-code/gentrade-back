from sqlalchemy import Column, Text
from sqlalchemy.dialects.postgresql import JSONB
from app.db.db import Base


class Checkpoint(Base):
    __tablename__ = "checkpoints"

    thread_id = Column(Text, primary_key=True)
    checkpoint_ns = Column(Text, primary_key=True, server_default="")
    checkpoint_id = Column(Text, primary_key=True)
    parent_checkpoint_id = Column(Text)
    type = Column(Text)
    checkpoint = Column(JSONB, nullable=False)
    metadata_ = Column("metadata", JSONB, nullable=False, server_default="{}")
