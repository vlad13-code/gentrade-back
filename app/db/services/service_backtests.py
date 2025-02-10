from fastapi import HTTPException, status
from typing import Optional

from app.db.utils.unitofwork import IUnitOfWork
from app.db.utils.decorators import require_user
from app.db.models.strategies import StrategiesORM
from app.db.models.users import UsersORM
from app.db.models.backtests import BacktestsORM
from app.schemas.schema_backtests import BacktestSchema, BacktestSchemaAdd
from app.tasks.backtests import run_backtest_task
from app.util.logger import (
    setup_logger,
    set_backtest_id,
    set_strategy_id,
    get_correlation_id,
)

logger = setup_logger("services.backtests")


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
        logger.info(
            "Creating new backtest",
            extra={"data": {"strategy_id": strategy_id, "date_range": date_range}},
        )

        async with uow:
            strategy: Optional[StrategiesORM] = await uow.strategies.find_one(
                id=strategy_id
            )
            if not strategy or strategy.user_id != user.id:
                logger.warning(
                    "Strategy access denied",
                    extra={
                        "data": {
                            "strategy_id": strategy_id,
                            "found": strategy is not None,
                            "user_match": (
                                strategy.user_id == user.id if strategy else False
                            ),
                        }
                    },
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not your strategy or strategy not found.",
                )

            # Set strategy ID in logging context
            set_strategy_id(strategy_id)

            new_backtest = BacktestSchemaAdd(
                strategy_id=strategy_id,
                date_range=date_range,
                status="running",
            )
            backtest: BacktestsORM = await uow.backtests.add_one(
                new_backtest.model_dump()
            )
            await uow.commit()

            # Set backtest ID in logging context
            set_backtest_id(backtest.id)

            logger.info(
                "Backtest created in database",
                extra={
                    "data": {
                        "backtest_id": backtest.id,
                        "strategy_id": strategy_id,
                        "date_range": date_range,
                    }
                },
            )

            # Get correlation ID from current context
            correlation_id = get_correlation_id()

            # Enqueue Celery task using async pattern
            logger.info("Enqueueing backtest task")
            await run_backtest_task.apply_async(
                backtest_id=backtest.id,
                strategy_id=strategy_id,
                clerk_id=user.clerk_id,
                date_range=date_range,
                correlation_id=correlation_id,  # Pass correlation ID to task
            )

        logger.info(
            "Backtest creation completed",
            extra={"data": {"backtest_id": backtest.id, "strategy_id": strategy_id}},
        )
        return BacktestSchema.model_validate(backtest, from_attributes=True)

    @require_user
    async def get_backtest(
        self, uow: IUnitOfWork, user: UsersORM, backtest_id: int
    ) -> BacktestSchema:
        """
        Fetch a single backtest by ID, verifying ownership via its strategy
        """
        logger.info(
            f"Fetching backtest {backtest_id}",
            extra={"data": {"backtest_id": backtest_id}},
        )

        async with uow:
            backtest: Optional[BacktestsORM] = await uow.backtests.find_one(
                id=backtest_id
            )
            if not backtest:
                logger.warning(
                    f"Backtest {backtest_id} not found",
                    extra={"data": {"backtest_id": backtest_id}},
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Backtest not found"
                )

            # Check that the user owns the strategy
            strategy: Optional[StrategiesORM] = await uow.strategies.find_one(
                id=backtest.strategy_id
            )
            if not strategy or strategy.user_id != user.id:
                logger.warning(
                    "Backtest access denied",
                    extra={
                        "data": {
                            "backtest_id": backtest_id,
                            "strategy_id": backtest.strategy_id,
                            "found": strategy is not None,
                            "user_match": (
                                strategy.user_id == user.id if strategy else False
                            ),
                        }
                    },
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not your backtest",
                )

            # Set context IDs for logging
            set_backtest_id(backtest.id)
            set_strategy_id(strategy.id)

            logger.info(
                f"Backtest {backtest_id} retrieved successfully",
                extra={
                    "data": {
                        "backtest_id": backtest_id,
                        "strategy_id": strategy.id,
                        "status": backtest.status,
                    }
                },
            )
            return BacktestSchema.model_validate(backtest, from_attributes=True)
