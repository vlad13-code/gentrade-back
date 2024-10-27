from sqlalchemy import Column, Text
from sqlalchemy.dialects.postgresql import BYTEA
from app.db.db import Base


class CheckpointBlob(Base):
    __tablename__ = "checkpoint_blobs"

    thread_id = Column(Text, primary_key=True)
    checkpoint_ns = Column(Text, primary_key=True, server_default="")
    channel = Column(Text, primary_key=True)
    version = Column(Text, primary_key=True)
    type = Column(Text, nullable=False)
    blob = Column(BYTEA)
