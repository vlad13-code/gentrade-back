from sqlalchemy import Column, Text, Integer
from sqlalchemy.dialects.postgresql import BYTEA
from app.db.db import Base


class CheckpointWrite(Base):
    __tablename__ = "checkpoint_writes"

    thread_id = Column(Text, primary_key=True)
    checkpoint_ns = Column(Text, primary_key=True, server_default="")
    checkpoint_id = Column(Text, primary_key=True)
    task_id = Column(Text, primary_key=True)
    idx = Column(Integer, primary_key=True)
    channel = Column(Text, nullable=False)
    type = Column(Text)
    blob = Column(BYTEA, nullable=False)
