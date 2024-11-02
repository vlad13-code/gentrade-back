from fastapi import APIRouter, Request, Response, status
from svix.webhooks import Webhook, WebhookVerificationError
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.config import Settings
from app.db.services.service_users import UsersService
from app.dependencies import UOWDep
from app.schemas.schema_clerk_webhook_event import ClerkWebhookEvent
from app.schemas.schema_users import UserSchemaAdd
from app.util.ft_userdir import init_ft_userdir, remove_ft_userdir

settings = Settings()

router = APIRouter(
    prefix="/webhooks",
    tags=["webhooks"],
)


@router.post("/clerk", status_code=status.HTTP_204_NO_CONTENT)
async def clerk_webhook_handler(request: Request, response: Response, uow: UOWDep):
    """
    Handle incoming webhook events from Clerk.

    This endpoint processes webhook events sent by Clerk. It verifies the event
    using a secret, validates the event data, and performs actions based on the
    event type. Supported event types include 'user.created' and 'user.deleted'.

    Args:
        request (Request): The incoming HTTP request containing headers and body.
        response (Response): The HTTP response object to modify status codes.
        uow (UOWDep): Unit of Work dependency for database operations.

    Raises:
        WebhookVerificationError: If the webhook signature verification fails.
        ValidationError: If the event data validation fails.
        IntegrityError: If this user already exists.
    """
    headers = request.headers
    payload = await request.body()

    try:
        wh = Webhook(settings.WH_SECRET)
        event = wh.verify(payload, headers)
        clerk_event = ClerkWebhookEvent.model_validate(event)

        if clerk_event.type == "user.created":
            user = UserSchemaAdd(
                clerk_id=clerk_event.data.id,
                name=f"{clerk_event.data.first_name} {clerk_event.data.last_name}".strip(),
                email=(
                    clerk_event.data.email_addresses[0].email_address
                    if clerk_event.data.email_addresses
                    else None
                ),
            )
            # user_id = await UsersService().add_user(uow, user)
            init_ft_userdir(user.clerk_id)
            return
        elif clerk_event.type == "user.deleted":
            remove_ft_userdir(clerk_event.data.id)
            await UsersService().delete_user(uow, clerk_event.data.id)

    except WebhookVerificationError as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return
    except ValidationError as e:
        response.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        return
    except IntegrityError as e:
        response.status_code = status.HTTP_409_CONFLICT
        return
