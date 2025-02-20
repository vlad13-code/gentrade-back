# pylint: disable=import-error
from fastapi import APIRouter, Response, status
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel

from app.db.services.service_exchanges import ExchangeService
from app.dependencies import UOWDep, UserAuthDep
from app.schemas.schema_exchanges import (
    MarketType,
    TradingPairInfo,
)
from app.schemas.schema_users import UserSchemaAdd
from app.schemas.schema_user_settings import UserSettingsSchema
from app.db.services.service_users import UsersService
from app.db.services.service_user_settings import UserSettingsService

router = APIRouter(
    prefix="/users",
    tags=["users"],
)


class UserAdded(BaseModel):
    user_id: int


class UserAlreadyExists(BaseModel):
    detail: str = "User already exists"


# TODO: this one is exposed to attacks. need to add api secret key check
# TODO: replace with clerk webhook
@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "model": UserAdded,
            "description": "User added successfully",
        },
    },
    summary="Add a new user if it doesn't exist",
)
async def add_user(user: UserSchemaAdd, uow: UOWDep, response: Response):
    try:
        user_id = await UsersService().add_user(uow, user)
    except IntegrityError as e:
        response.status_code = status.HTTP_200_OK
        return UserAlreadyExists()

    response.status_code = status.HTTP_201_CREATED
    return UserAdded(user_id=user_id)


@router.get("/settings", response_model=UserSettingsSchema)
async def get_user_settings(
    uow: UOWDep,
    user: UserAuthDep,
) -> UserSettingsSchema:
    """Get the current user's Freqtrade settings."""
    settings = await UserSettingsService().get_user_settings(uow, user)
    return settings


@router.patch("/settings", response_model=UserSettingsSchema)
async def update_user_settings(
    settings_update: UserSettingsSchema,
    uow: UOWDep,
    user: UserAuthDep,
) -> UserSettingsSchema:
    """Update the current user's Freqtrade settings."""
    return await UserSettingsService().update_user_settings(uow, user, settings_update)


@router.get("/settings/pairs/{exchange_id}/{market_type}")
async def get_exchange_pairs(
    exchange_id: str,
    market_type: MarketType,
    user: UserAuthDep,
) -> list[TradingPairInfo]:
    """Get the trading pairs for a specific exchange."""
    return await ExchangeService().get_trading_pairs(exchange_id, market_type)
