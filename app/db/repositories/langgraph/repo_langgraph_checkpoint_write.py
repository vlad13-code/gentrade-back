from app.db.models.langgraph.checkpoint_write import CheckpointWrite
from app.db.utils.repository import SQLAlchemyRepository


class CheckpointWriteRepository(SQLAlchemyRepository):
    model = CheckpointWrite
