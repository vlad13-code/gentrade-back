# pylint: disable=import-error
from fastapi import APIRouter, Response, status
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel

from app.dependencies import UOWDep
from app.schemas.schema_users import UserSchemaAdd
from app.db.services.service_users import UsersService

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
    except IntegrityError:
        response.status_code = status.HTTP_200_OK
        return UserAlreadyExists()

    response.status_code = status.HTTP_201_CREATED
    return UserAdded(user_id=user_id)
