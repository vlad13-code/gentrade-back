from app.db.models.chats import ChatsORM
from app.db.utils.repository import SQLAlchemyRepository


class ChatsRepository(SQLAlchemyRepository):
    model = ChatsORM
