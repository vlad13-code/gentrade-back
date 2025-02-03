import logging
from typing import Optional
from app.celery.celery_async import AsyncTask, celery_app
from app.db.models.strategies import StrategiesORM
from app.db.utils.unitofwork import get_scoped_uow
from app.util.ft.ft_backtesting import FTBacktesting
from app.util.ft.ft_market_data import FTMarketData
from app.util.exceptions import DataDownloadTimeoutError

# Configure basic logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
async def run_backtest_task(
    self: AsyncTask,
    backtest_id: int,
    strategy_id: int,
    clerk_id: str,
    date_range: str,
    **kwargs,
) -> dict:
    """
    Runs in the Celery worker. Uses our async task implementation.
    Returns the backtest result on success.
    Raises exceptions on failure which are handled by the AsyncTask base class.
    """
    self.update_state(state="PROGRESS", meta={"status": "Starting backtest"})

    async with get_scoped_uow() as uow:
        # Get strategy
        strategy: Optional[StrategiesORM] = await uow.strategies.find_one(
            id=strategy_id
        )
        if not strategy:
            raise ValueError(f"Strategy {strategy_id} not found")

        logger.info(
            f"Running backtest {backtest_id} for strategy {strategy_id} with clerk_id {clerk_id}"
        )

        try:
            # Update backtest status to downloading data
            backtest = await uow.backtests.find_one(id=backtest_id)
            if not backtest:
                raise ValueError(f"Backtest {backtest_id} not found")

            await uow.backtests.edit_one(backtest_id, {"status": "downloading_data"})
            await uow.commit()

            # Download market data
            ft_market_data = FTMarketData(clerk_id)
            try:
                # TODO: Extract pairs and timeframes from strategy
                # For now using default values
                ft_market_data.download(
                    pairs=["BTC/USDT"],  # This should come from strategy
                    timeframes=["5m"],  # This should come from strategy
                    date_range=date_range,
                )
            except Exception as e:
                logger.error(f"Failed to download market data: {e}")
                raise DataDownloadTimeoutError("Failed to download market data", e)

            # Update status to running backtest
            await uow.backtests.edit_one(backtest_id, {"status": "running"})
            await uow.commit()

            # Run freqtrade backtest
            ft_backtesting = FTBacktesting(clerk_id)
            result_file_path = ft_backtesting.run_backtest(
                strategy_class_name=strategy.file.replace(".py", ""),
                date_range=date_range,
            )

            # Update backtest with success
            await uow.backtests.edit_one(
                backtest_id, {"file": result_file_path, "status": "finished"}
            )
            await uow.commit()

            return {
                "state": "success",
                "backtest_id": backtest_id,
                "strategy_id": strategy_id,
                "result_file": result_file_path,
            }

        except Exception as e:
            logger.error(f"Error running backtest: {e}")
            # Mark backtest as failed
            backtest = await uow.backtests.find_one(id=backtest_id)
            if backtest:
                await uow.backtests.edit_one(backtest_id, {"status": "failed"})
                await uow.commit()
            # Re-raise the exception to be handled by AsyncTask
            raise
