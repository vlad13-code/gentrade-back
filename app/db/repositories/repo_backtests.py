from app.db.models.backtests import BacktestsORM
from app.db.utils.repository import SQLAlchemyRepository


class BacktestsRepository(SQLAlchemyRepository):
    model = BacktestsORM
