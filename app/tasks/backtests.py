import asyncio
from app.celery_app import celery_app
from app.db.db import async_session_maker
from app.db.models.backtests import BacktestsORM
from app.db.models.strategies import StrategiesORM
from app.util.ft_backtesting import run_backtest_in_docker


@celery_app.task
def run_backtest_task(
    backtest_id: int, strategy_id: int, clerk_id: str, date_range: str
):
    """
    Runs in the Celery worker. We do a mini async bridging via asyncio.run(...)
    """
    asyncio.run(_run_backtest(backtest_id, strategy_id, clerk_id, date_range))


async def _run_backtest(
    backtest_id: int, strategy_id: int, clerk_id: str, date_range: str
):
    """
    The actual backtest execution logic:
    1. Get the strategy file path
    2. Run freqtrade backtest in Docker
    3. Update the backtest record with results
    """
    async with async_session_maker() as session:
        strategy = await session.get(StrategiesORM, strategy_id)
        if not strategy:
            # Can't do anything if strategy is gone
            return

        # 1. Run freqtrade backtest
        try:
            result_file_path = run_backtest_in_docker(
                strategy_file_path=strategy.file,
                clerk_id=clerk_id,
                date_range=date_range,
            )

            # 2. Update DB with success
            backtest = await session.get(BacktestsORM, backtest_id)
            if backtest:
                backtest.file = result_file_path
                backtest.status = "finished"
            await session.commit()

        except Exception as e:
            # Mark backtest as failed
            backtest = await session.get(BacktestsORM, backtest_id)
            if backtest:
                backtest.status = "failed"
            await session.commit()
