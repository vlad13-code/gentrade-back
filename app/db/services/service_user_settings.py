from fastapi import HTTPException, status
from pydantic import ValidationError

from app.db.models.users import UsersORM
from app.db.utils.decorators import require_user
from app.db.utils.unitofwork import IUnitOfWork
from app.schemas.schema_user_settings import UserSettingsSchema
from app.util.ft.ft_config import FTUserConfig
from app.util.ft.ft_userdir import FTUserDir
from app.util.logger import setup_logger

logger = setup_logger("services.user_settings")


class UserSettingsService:

    @require_user
    async def get_user_settings(
        self, uow: IUnitOfWork, user: UsersORM
    ) -> UserSettingsSchema:
        """
        Retrieves the user's Freqtrade settings.

        Args:
            uow (IUnitOfWork): Unit of work instance
            user (UsersORM): User model instance

        Returns:
            UserSettings: User's settings in frontend format
        """
        ft_user_config = FTUserConfig(user.clerk_id)
        try:
            config = ft_user_config.read_config()
            # Convert FreqtradeConfig to UserSettings using Pydantic
            return UserSettingsSchema.from_freqtrade_config(config)
        except FileNotFoundError:
            # If config doesn't exist, initialize and return defaults
            ft_userdir = FTUserDir(user.clerk_id)
            ft_userdir.initialize()
            config = ft_user_config.read_config()
            return UserSettingsSchema.from_freqtrade_config(config)
        except ValidationError as e:
            # Log the error and return defaults
            logger.error(f"Invalid config for user {user.clerk_id}: {str(e)}")
            return UserSettingsSchema()  # Will use default values from model_validator

    @require_user
    async def update_user_settings(
        self,
        uow: IUnitOfWork,
        user: UsersORM,
        settings_update: UserSettingsSchema,
    ) -> UserSettingsSchema:
        """
        Updates the user's Freqtrade settings.

        Args:
            uow (IUnitOfWork): Unit of work instance
            user (UsersORM): User model instance
            settings_update (UserSettings): New settings in frontend format

        Returns:
            UserSettings: Updated settings in frontend format

        Raises:
            HTTPException: If settings are invalid or update fails
        """
        ft_user_config = FTUserConfig(user.clerk_id)

        try:
            # Ensure user directory exists
            ft_userdir = FTUserDir(user.clerk_id)
            if not ft_userdir.exists():
                ft_userdir.initialize()

            # Convert UserSettings to FreqtradeConfig using Pydantic
            freqtrade_config = settings_update.to_freqtrade_config()

            # Write the updated config
            ft_user_config.write_config(freqtrade_config)

            # Return the updated settings
            return settings_update

        except ValidationError as e:
            logger.error(f"Invalid settings: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid settings: {str(e)}",
            )
        except Exception as e:
            logger.error(f"Error updating settings for user {user.clerk_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update settings",
            )
