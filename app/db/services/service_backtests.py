from fastapi import HTTPException, status
from typing import Optional

from app.db.utils.unitofwork import IUnitOfWork
from app.db.utils.decorators import require_user
from app.db.models.strategies import StrategiesORM
from app.db.models.users import UsersORM
from app.db.models.backtests import BacktestsORM
from app.schemas.schema_backtests import BacktestSchema, BacktestSchemaAdd
from app.tasks.backtests import run_backtest_task


class BacktestsService:
    @require_user
    async def create_backtest(
        self, uow: IUnitOfWork, user: UsersORM, strategy_id: int, date_range: str
    ) -> BacktestSchema:
        """
        1. Ensure the strategy belongs to the user
        2. Create a backtest record with status='running'
        3. Enqueue the Celery task to actually run the backtest
        4. Return the new backtest ID
        """
        async with uow:
            strategy: Optional[StrategiesORM] = await uow.strategies.find_one(
                id=strategy_id
            )
            if not strategy or strategy.user_id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not your strategy or strategy not found.",
                )

            new_backtest = BacktestSchemaAdd(
                strategy_id=strategy_id,
                date_range=date_range,
                status="running",
            )
            backtest: BacktestsORM = await uow.backtests.add_one(
                new_backtest.model_dump()
            )
            await uow.commit()

        # Enqueue Celery task using async pattern
        await run_backtest_task.apply_async(
            backtest_id=backtest.id,
            strategy_id=strategy_id,
            clerk_id=user.clerk_id,
            date_range=date_range,
        )
        return BacktestSchema.model_validate(backtest, from_attributes=True)

    @require_user
    async def get_backtest(
        self, uow: IUnitOfWork, user: UsersORM, backtest_id: int
    ) -> BacktestSchema:
        """
        Fetch a single backtest by ID, verifying ownership via its strategy
        """
        async with uow:
            backtest: Optional[BacktestsORM] = await uow.backtests.find_one(
                id=backtest_id
            )
            if not backtest:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Backtest not found"
                )

            # Check that the user owns the strategy
            strategy: Optional[StrategiesORM] = await uow.strategies.find_one(
                id=backtest.strategy_id
            )
            if not strategy or strategy.user_id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not your backtest",
                )
            return BacktestSchema.model_validate(backtest, from_attributes=True)
