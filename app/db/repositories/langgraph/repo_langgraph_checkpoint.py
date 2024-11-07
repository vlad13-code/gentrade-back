from app.db.models.langgraph.checkpoint import Checkpoint
from app.db.utils.repository import SQLAlchemyRepository


class CheckpointRepository(SQLAlchemyRepository):
    model = Checkpoint
