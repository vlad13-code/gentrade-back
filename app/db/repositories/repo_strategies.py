from app.db.models.strategies import StrategiesORM
from app.db.utils.repository import SQLAlchemyRepository


class StrategiesRepository(SQLAlchemyRepository):
    model = StrategiesORM
