# User Settings Endpoint Design Document (GenTrade Backend)

## Current Context

- **Overview:** This feature implements a new endpoint for managing user-specific settings related to Freqtrade configuration. It extends the existing user management capabilities provided by Clerk webhooks and the `UsersService`. This feature will allow users to customize their Freqtrade experience, affecting backtesting and (eventually) live trading.
- **Key Components:**
  - `app/db/services/service_users.py` (UsersService - will be extended)
  - `app/db/models/users.py` (UsersORM - might need modification)
  - `app/schemas/schema_users.py` (User schemas - new schema needed)
  - `app/routers/v1/router_users.py` (User router - new endpoint needed)
  - `app/util/ft/ft_config.py` (FTUserConfig - for reading/writing Freqtrade config)
  - `app/schemas/schema_freqtrade_config.py` (FreqtradeConfig - Pydantic model)
  - `app/db/utils/unitofwork.py` (IUnitOfWork, UnitOfWork)
  - `app/dependencies.py` (check_auth)
- **Pain Points:**
  - Currently, all users operate with a default Freqtrade configuration. This limits the ability to tailor the trading experience.
  - Users have no way to customize parameters like stake currency, max open trades, or pair whitelists/blacklists.
  - Adding this feature will improve user satisfaction by allowing customization.

## Requirements

### Functional Requirements

- **Create/Update Settings:**

  - Users should be able to create or update their Freqtrade settings via a `PATCH /api/v1/users/settings` endpoint.
  - The request body should conform to a new Pydantic model (`UserSettingsUpdateSchema`), which will be a subset of `FreqtradeConfig`. This model should only include fields that users are allowed to modify.
  - The backend should validate the input against `UserSettingsUpdateSchema`.
  - The backend should update the user's `config.json` file using `FTUserConfig.update_config`.
  - The backend should return the updated settings (using a new `UserSettingsSchema`) to the user.

- **Get Settings:**

  - Users should be able to retrieve their current Freqtrade settings via a `GET /api/v1/users/settings` endpoint.
  - The backend should retrieve the user's `config.json` file using `FTUserConfig.read_config`.
  - The backend should return the user's settings, filtered to only include fields defined in `UserSettingsSchema`.

- **Authentication and Authorization:**

  - The `/api/v1/users/settings` endpoint (both GET and PATCH) MUST be protected by Clerk authentication using the `check_auth` dependency.
  - Only the authenticated user can modify their own settings. The `UsersService` will be responsible for ensuring this.

- **Error Handling:**
  - If the user's `config.json` file does not exist, the `GET` request should return the default Freqtrade configuration (perhaps by calling `FTUserDir.initialize()` to ensure the default config exists).
  - If the provided settings are invalid (e.g., invalid `stake_currency`), the backend should return a 422 Unprocessable Entity error with a descriptive message.
  - If the user attempts to update settings they are not authorized to change, the backend should return a 403 Forbidden error.

### Non-Functional Requirements

- **Performance:**
  - Retrieving settings (`GET`) should ideally complete within 500ms.
  - Updating settings (`PATCH`) should ideally complete within 1 second (writing to the file system is the primary operation).
- **Scalability:** The settings endpoint should not be a bottleneck. It is expected to scale similarly to other user-related endpoints.
- **Observability:**
  - Log all setting update attempts, including the user ID, timestamp, and the fields that were updated.
  - Log any errors encountered during settings updates (e.g., file I/O errors, validation errors).
- **Security:**
  - Only authenticated users can access their own settings.
  - Input validation MUST be performed to prevent users from injecting malicious configuration values.

## Design Decisions

- **Separate Endpoint:** Using `/api/v1/users/settings` provides a clear and dedicated endpoint for managing user settings, separate from general user profile information. This improves API organization.
- **PATCH Method:** Using PATCH allows partial updates to the settings, which is more efficient than requiring the user to submit the entire configuration every time.
- **Pydantic Models for Request/Response:** Using Pydantic models (`UserSettingsUpdateSchema`, `UserSettingsSchema`) provides strong input validation and clear API documentation.
- **`FTUserConfig` Integration:** Reusing the existing `FTUserConfig` class ensures consistency in how Freqtrade configuration is handled.
- **Default Configuration:** Returning default values if a user hasn't customized their settings yet provides a user-friendly experience.

**Alternatives Considered:**

- **Storing settings in the database:** We could store the settings as a JSON blob in the `UsersORM` model. However, using Freqtrade's `config.json` file simplifies integration with Freqtrade and allows for potential future use cases (e.g., users manually editing their config file).
- **Combined User Profile Endpoint:** We could have included settings in a general `/api/v1/users/me` endpoint. However, separating it keeps the user profile endpoint focused and improves API organization.

## Technical Design

### 1. Core Components

```python
# app/db/services/service_users.py

class UsersService:
    @require_user
    async def get_user_settings(self, uow: IUnitOfWork, user: UsersORM) -> UserSettingsSchema:
        """Retrieves the user's Freqtrade settings."""
        ft_user_config = FTUserConfig(user.clerk_id)
        try:
            config = ft_user_config.read_config()
        except FileNotFoundError:
            # If config doesn't exist, initialize and return defaults
            ft_userdir = FTUserDir(user.clerk_id)
            ft_userdir.initialize()
            config = ft_user_config.read_config()
        return UserSettingsSchema(**config.model_dump(include=UserSettingsSchema.model_fields.keys()))

    @require_user
    async def update_user_settings(self, uow: IUnitOfWork, user: UsersORM, settings_update: UserSettingsUpdateSchema) -> UserSettingsSchema:
        """Updates the user's Freqtrade settings."""
        ft_user_config = FTUserConfig(user.clerk_id)
        try:
           updated_config = ft_user_config.update_config(settings_update.model_dump(exclude_unset=True))
        except ValidationError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
        return UserSettingsSchema(**updated_config.model_dump(include=UserSettingsSchema.model_fields.keys()))


# app/routers/v1/router_users.py

@router.get("/settings", response_model=UserSettingsSchema)
async def get_user_settings(uow: UOWDep, user: UserAuthDep):
    """Get the current user's Freqtrade settings."""
    return await UsersService().get_user_settings(uow, user)

@router.patch("/settings", response_model=UserSettingsSchema)
async def update_user_settings(settings_update: UserSettingsUpdateSchema, uow: UOWDep, user: UserAuthDep):
    """Update the current user's Freqtrade settings."""
    return await UsersService().update_user_settings(uow, user, settings_update)

```

### 2. Data Models

```python
# app/schemas/schema_users.py
from typing import Optional
from pydantic import BaseModel, Field
from app.schemas.schema_freqtrade_config import (
    TelegramConfig,
    ExchangeConfig,
)  # Import relevant parts


class UserSettingsUpdateSchema(BaseModel):
    max_open_trades: Optional[int] = Field(None, description="Maximum number of open trades")
    stake_currency: Optional[str] = Field(None, description="Stake currency")
    stake_amount: Optional[float | Literal["unlimited"]] = Field(None, description="Stake amount")
    trading_mode: Optional[Literal["spot", "margin", "futures"]] = Field(
        None, description="Trading mode"
    )
    telegram: Optional[TelegramConfig] = Field(None, description="Telegram configuration") # Example of nested model
    exchange: Optional[ExchangeConfig] = Field(None, description="Exchange configuration settings") # Example nested config


class UserSettingsSchema(UserSettingsUpdateSchema):
    dry_run: bool = Field(description="Whether dry run is enabled")
    # Add other read-only fields here, but *only* those you want to expose.


```

### 3. Integration Points

- **New Endpoints:**
  - `GET /api/v1/users/settings`: Retrieves the current user's Freqtrade settings.
  - `PATCH /api/v1/users/settings`: Updates the current user's Freqtrade settings.
- **Existing Components:**
  - `UsersService` (in `app/db/services/service_users.py`): Extended with `get_user_settings` and `update_user_settings` methods.
  - `FTUserConfig` (in `app/util/ft/ft_config.py`): Used for reading and writing the Freqtrade configuration file.
  - `check_auth` (in `app/dependencies.py`): Used for authentication.
  - `UsersORM` (in `app/db/models/users.py`): No changes required to the model itself, as settings are stored in a file.

### 4. Agent Interaction

- This feature does not directly interact with any AI agents.

## Implementation Plan

1. **Create Pydantic Models:** Define `UserSettingsUpdateSchema` and `UserSettingsSchema` in `app/schemas/schema_users.py`.
2. **Implement Service Methods:** Add `get_user_settings` and `update_user_settings` to `UsersService`.
3. **Create API Endpoints:** Add `GET` and `PATCH` endpoints to `router_users.py`.
4. **Add Unit Tests:** Write unit tests for the new service methods and API endpoints.
5. **Update Documentation:** Update the API documentation (OpenAPI/Swagger).

**Timeline:**

- **Phase 1:** (1 day) Pydantic models and service methods.
- **Phase 2:** (1 day) API endpoints and integration tests.
- **Phase 3:** (0.5 day) Documentation and final testing.

## Observability

### Logging

- **`UsersService.get_user_settings`:**
  - Log when settings are retrieved, including the `user_id`.
  - Log if the `config.json` file is not found and defaults are used.
- **`UsersService.update_user_settings`:**
  - Log when settings are updated, including the `user_id` and the fields that were modified.
  - Log any validation errors (with details).
  - Log any file I/O errors.

```json
{
  "timestamp": "2025-01-29T15:00:00Z",
  "level": "INFO",
  "component": "UsersService",
  "event": "user_settings_updated",
  "user_id": "user_123",
  "updated_fields": ["max_open_trades", "stake_currency"]
}

{
  "timestamp": "2025-01-29T15:05:00Z",
  "level": "ERROR",
  "component": "UsersService",
  "event": "user_settings_update_failed",
  "user_id": "user_123",
  "error_type": "ValidationError",
  "error_message": "Invalid value for stake_currency"
}
```

## Future Considerations

- **User Interface:** This design document focuses on the backend. A corresponding frontend UI will need to be developed to allow users to easily manage their settings.
- **Default Settings:** Consider providing a way to set global default settings for new users.
- **More Granular Settings:** Allow users to control more Freqtrade configuration options.
- **Settings Presets**: Allow user to create, save and switch between several settings presets.

## Dependencies

- No _new_ dependencies are introduced by this feature.

## Security Considerations

- **Authentication:** All endpoints are protected by Clerk authentication.
- **Authorization:** Only the authenticated user can modify their own settings.
- **Data Validation:** Pydantic models are used to validate input, preventing users from injecting invalid configuration values. The `UserSettingsUpdateSchema` limits the fields that users can modify.

## Rollout Strategy

- **Backend Deployment:** Deploy the updated backend code.
- **Frontend Integration:** Develop the frontend UI to interact with the new endpoints.
- **Testing:** Thoroughly test the feature in a staging environment.
- **Monitoring:** Monitor logs and performance after deployment.

## References

- `app/db/services/service_users.py`
- `app/db/models/users.py`
- `app/schemas/schema_users.py`
- `app/routers/v1/router_users.py`
- `app/util/ft/ft_config.py`
- `app/schemas/schema_freqtrade_config.py`
- [Freqtrade Configuration Documentation](https://www.freqtrade.io/en/stable/configuration/)
