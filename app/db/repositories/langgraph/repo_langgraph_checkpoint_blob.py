from app.db.models.langgraph.checkpoint_blob import CheckpointBlob
from app.db.utils.repository import SQLAlchemyRepository


class CheckpointBlobRepository(SQLAlchemyRepository):
    model = CheckpointBlob
