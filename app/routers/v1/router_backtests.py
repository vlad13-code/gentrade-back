from fastapi import APIRouter

from app.dependencies import UOWDep, UserAuthDep
from app.db.services.service_backtests import BacktestsService
from app.schemas.schema_backtests import (
    BacktestStartSchema,
    BacktestCreated,
    BacktestSchema,
)

router = APIRouter(
    prefix="/backtests",
    tags=["backtests"],
)


@router.post("", response_model=BacktestCreated)
async def create_backtest(req: BacktestStartSchema, uow: UOWDep, user: UserAuthDep):
    """Start a new backtest for a strategy"""
    backtest_id = await BacktestsService().create_backtest(
        uow=uow,
        user=user,
        strategy_id=req.strategy_id,
        date_range=req.date_range,
    )
    return {"backtest_id": backtest_id}


@router.get("/{backtest_id}", response_model=BacktestSchema)
async def get_backtest(backtest_id: int, uow: UOWDep, user: UserAuthDep):
    return await BacktestsService().get_backtest(
        uow=uow,
        user=user,
        backtest_id=backtest_id,
    )
