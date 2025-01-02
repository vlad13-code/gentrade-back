from fastapi import HTTPException, status
from app.schemas.schema_strategies import StrategySchemaAdd
from app.db.utils.unitofwork import IUnitOfWork
from app.db.models.strategies import StrategiesORM
from app.db.models.users import UsersORM
from app.db.utils.decorators import require_user


class StrategiesService:
    @require_user
    async def add_strategy(
        self, uow: IUnitOfWork, strategy: StrategySchemaAdd, user: UsersORM
    ) -> int:
        async with uow:
            strategy_dict = strategy.model_dump()
            strategy_dict["user_id"] = user.id
            strategy_id = await uow.strategies.add_one(strategy_dict)
            await uow.commit()
            return strategy_id

    @require_user
    async def delete_strategy(self, uow: IUnitOfWork, id: int, user: UsersORM) -> bool:
        async with uow:
            strategy: StrategiesORM = await uow.strategies.find_one(id=id)
            if not strategy or strategy.user_id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found"
                )
            await uow.strategies.delete_one(id)
            await uow.commit()
            return True

    @require_user
    async def get_user_strategies(
        self, uow: IUnitOfWork, user: UsersORM
    ) -> list[StrategiesORM]:
        async with uow:
            return await uow.strategies.find_all_by(user_id=user.id)

    @require_user
    async def get_strategy(
        self, uow: IUnitOfWork, id: int, user: UsersORM
    ) -> StrategiesORM:
        async with uow:
            strategy: StrategiesORM = await uow.strategies.find_one(id=id)
            if not strategy or strategy.user_id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found"
                )
            return strategy
