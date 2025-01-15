# pylint: disable=import-error
from fastapi import APIRouter, Response, status

from app.dependencies import UOWDep, UserAuthDep
from app.schemas.schema_strategies import (
    StrategyDraftSchemaAdd,
    StrategySchema,
)
from app.db.services.service_strategies import StrategiesService

router = APIRouter(
    prefix="/strategies",
    tags=["strategies"],
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=StrategySchema,
    summary="Add and deploy a new strategy",
)
async def add_strategy(
    strategy_draft: StrategyDraftSchemaAdd, uow: UOWDep, user: UserAuthDep
) -> StrategySchema:
    return await StrategiesService().add_strategy(uow, strategy_draft, user)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=list[StrategySchema],
    summary="Get all strategies for the current user",
)
async def get_strategies(
    uow: UOWDep,
    user: UserAuthDep,
) -> list[StrategySchema]:
    return await StrategiesService().get_user_strategies(uow, user)


@router.get(
    "/{strategy_id}",
    status_code=status.HTTP_200_OK,
    response_model=StrategySchema,
    summary="Get a strategy by ID",
)
async def get_strategy(
    strategy_id: int,
    uow: UOWDep,
    user: UserAuthDep,
) -> StrategySchema:
    return await StrategiesService().get_strategy(uow, strategy_id, user)


@router.delete(
    "/{strategy_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a strategy",
)
async def delete_strategy(strategy_id: int, uow: UOWDep, user: UserAuthDep):
    await StrategiesService().delete_strategy(uow, strategy_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
