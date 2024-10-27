from app.db.models.users import UsersORM
from app.db.utils.repository import SQLAlchemyRepository


class UsersRepository(SQLAlchemyRepository):
    model = UsersORM
