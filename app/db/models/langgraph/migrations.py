from sqlalchemy import Column, Integer
from app.db.db import Base


class StoreMigration(Base):
    __tablename__ = "store_migrations"

    v = Column(Integer, primary_key=True)


class CheckpointMigration(Base):
    __tablename__ = "checkpoint_migrations"

    v = Column(Integer, primary_key=True)
