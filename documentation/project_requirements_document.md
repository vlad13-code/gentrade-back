# Project Requirements Document: GenTrade Backend

## 1. Introduction

**Project Name:** GenTrade Backend

**Version:** 1.0.0

**Date:** 2025-01-29

**Purpose:** This document outlines the requirements for the GenTrade backend application, a platform for creating, managing, and backtesting cryptocurrency trading strategies using Freqtrade and AI-powered strategy generation.

## 2. Stakeholders

- **End Users/Traders:** Individuals (primarily hobbyists and beginners) interested in creating, deploying, and managing crypto trading bots through a user-friendly, chat-based interface.
- **Developers:** Responsible for maintaining, extending, and improving the platform's functionality, performance, and security.
- **System Administrators:** Responsible for deploying, monitoring, and maintaining the infrastructure that supports the GenTrade backend.

## 3. Overall Description

### 3.1. Product Perspective

GenTrade backend is a core component of the GenTrade platform. It provides a RESTful API for the frontend and manages interactions with Freqtrade, databases, and AI services. It does _not_ include a user interface. The backend handles:

- User authentication (via Clerk).
- Chat history persistence.
- AI-driven trading strategy generation.
- Storage and retrieval of trading strategies.
- Initiating and managing Freqtrade backtests (via Celery).
- Handling user data and configurations.
- Webhook handling from Clerk.

### 3.2. Product Functions

- **User Management:**

  - Create user records upon Clerk webhook events (new user signup).
  - Delete user records and associated data upon Clerk webhook events (user deletion).
  - Verify user authentication via Clerk JWTs for API requests.

- **Chat Management:**

  - Create, update, and delete chat histories associated with a user.
  - Store chat messages, including AI responses and strategy details, in a structured format.
  - Retrieve chat histories for a specific user.
  - Manage chat metadata (e.g., titles).

- **Strategy Management:**

  - Generate Freqtrade strategy code based on user input and AI agent interaction.
  - Store generated strategy code, metadata, and associated chat ID in the database.
  - Retrieve a list of strategies for a user.
  - Retrieve a specific strategy by ID.
  - Delete a strategy, including the associated file.
  - Associate Strategy Drafts with Strategies.

- **Backtesting:**

  - Initiate a Freqtrade backtest for a given strategy and date range.
  - Download required market data.
  - Verify downloaded market data before starting a backtest.
  - Store backtest results (output file path, status).
  - Retrieve backtest status and results.
  - Utilize Celery for asynchronous backtest execution.

- **AI Agent Interaction:**

  - Route user requests to appropriate AI agents (e.g., strategy creation vs. general questions).
  - Utilize Langchain and LangGraph for AI agent orchestration and conversation state management.
  - Employ prompt engineering to guide AI strategy generation.
  - Handle structured output from AI agents.

- **Freqtrade Integration:**

  - Manage user-specific Freqtrade directories (creation, deletion).
  - Write generated strategy code to Freqtrade strategy files.
  - Execute Freqtrade commands (backtesting, data download) within Docker containers.
  - Read and update Freqtrade configuration files.

- **Data Download:**
  - Download market data needed for strategy backtesting.

### 3.3. User Classes and Characteristics

- **Authenticated User:** A user who has successfully authenticated via Clerk. They can create, manage, and backtest strategies.
- **Unauthenticated User:** Cannot access any API endpoints requiring authentication (most of the API). The system interacts with unauthenticated users only through Clerk webhooks.

### 3.4. Operating Environment

- **Operating System:** Linux (developed using python:3.12-slim-bullseye Docker image).
- **Database:** PostgreSQL (managed via SQLAlchemy and Alembic).
- **Message Broker:** RabbitMQ (for Celery task queue).
- **Web Server:** FastAPI (with Uvicorn as ASGI server).
- **Containerization:** Docker (for Freqtrade and potentially other services).
- **Cloud Deployment:** Designed for cloud deployment (e.g., AWS, Google Cloud, Azure) but can be run locally.

### 3.5. Design and Implementation Constraints

- **Dependencies:** The project relies heavily on external libraries (FastAPI, SQLAlchemy, Pydantic, Celery, Langchain, Freqtrade, python-on-whales, svix, etc.). Version compatibility must be carefully managed.
- **Asynchronous Operations:** Extensive use of `async/await` requires careful handling of concurrency and potential race conditions.
- **Database Migrations:** Alembic migrations must be carefully managed to ensure database schema integrity.
- **Freqtrade Compatibility:** Generated strategy code must be fully compatible with Freqtrade's requirements and best practices.
- **Docker:** Reliance on Docker for Freqtrade operations introduces dependencies on Docker availability and configuration.
- **External Services**: Reliance on external services, such as Clerk for authentication and OpenAI/Anthropic for language models, introduces potential points of failure and latency.
- **Prompt Length Limit:** The prompts passed to the LLM model have a maximum context window, that depends on the specific model used.

### 3.6. Assumptions and Dependencies

- A running PostgreSQL database is available and configured correctly.
- A RabbitMQ message broker is available and configured correctly.
- Clerk authentication service is set up and configured.
- API keys for external services (e.g., OpenAI, Anthropic, Geocoding) are properly configured.
- The Docker environment is correctly set up to run Freqtrade containers.
- The system has sufficient resources (CPU, memory, disk space) to handle backtesting and data download operations.

## 4. System Features

### 4.1. User Authentication and Authorization

- **Description:** Authenticates users via Clerk and authorizes API access based on user ownership of resources.
- **Stimulus/Response Sequences:**
  - User sends a request to a protected API endpoint with a Clerk JWT in the `Authorization` header.
  - The `check_auth` dependency in `dependencies.py` verifies the JWT using `fastapi-clerk-auth`.
  - If the JWT is valid, the user's `clerk_id` is extracted and made available to the endpoint.
  - If the JWT is invalid or missing, a 401 Unauthorized response is returned.
  - The `@require_user` decorator (in `db/utils/decorators.py`) ensures that the authenticated user exists in the database and injects the `UsersORM` instance into the service method.
  - Service methods verify that the requested resource (chat, strategy, backtest) belongs to the authenticated user. If not, a 403 Forbidden response is returned.
- **Functional Requirements:**
  - FR.1: The system MUST use Clerk for user authentication.
  - FR.2: The system MUST verify the Clerk JWT for all protected API endpoints.
  - FR.3: The system MUST authorize access to resources based on user ownership.
  - FR.4: The system MUST return a 401 Unauthorized response for invalid or missing JWTs.
  - FR.5: The system MUST return a 403 Forbidden response if a user attempts to access a resource they do not own.
  - FR.6: The system MUST create a user record in the database upon receiving a `user.created` webhook from Clerk.
  - FR.7: The system MUST delete a user record and associated data upon receiving a `user.deleted` webhook from Clerk.

### 4.2. Chat Management

- **Description:** Allows users to manage their chat histories with the AI.
- **Stimulus/Response Sequences:**
  - User sends a request to create a new chat (`POST /api/v1/chats`).
  - Backend creates a new `ChatsORM` entry, associating it with the authenticated user.
  - Backend returns the newly created chat's ID.
  - User sends a request to update a chat (`PATCH /api/v1/chats`).
  - Backend updates the specified chat record (e.g., title, messages) if it belongs to the user.
  - Backend returns the updated chat data.
  - User sends a request to get a list of their chats (`GET /api/v1/chats`).
  - Backend retrieves all `ChatsORM` entries associated with the user, ordered by update time.
  - Backend returns a list of chat summaries (ID, thread ID, title, timestamps).
  - User sends a request to get a specific chat (`GET /api/v1/chats/{thread_id}`).
  - Backend retrieves the specified `ChatsORM` entry if it belongs to the user.
  - Backend returns the complete chat data (including messages).
  - User sends a request to delete a chat (`DELETE /api/v1/chats/{thread_id}`).
  - Backend deletes the specified `ChatsORM` entry, associated LangGraph entries, and strategy if it is associated with the chat, if it belongs to the user.
- **Functional Requirements:**
  - FR.8: The system MUST allow authenticated users to create new chat histories.
  - FR.9: The system MUST associate each chat history with a unique `thread_id` (UUID).
  - FR.10: The system MUST associate each chat history with the authenticated user.
  - FR.11: The system MUST store chat messages in a structured format (JSON).
  - FR.12: The system MUST allow users to update the title and messages of their chat histories.
  - FR.13: The system MUST allow users to retrieve a list of their chat histories.
  - FR.14: The system MUST allow users to retrieve a specific chat history by `thread_id`.
  - FR.15: The system MUST allow users to delete their chat histories.
  - FR.16: The system MUST delete all associated LangGraph data when deleting a chat.

### 4.3. Strategy Generation and Management

- **Description:** Enables users to create, view, and delete trading strategies using natural language.
- **Stimulus/Response Sequences:**
  - User interacts with the chat interface, sending a message requesting a new strategy.
  - The backend (via LangServe and `graph_main.py`) routes the request to the `strategy_draft` agent.
  - The `strategy_draft` agent uses the LLM (with prompts defined in `agents/strategy/prompts/strategy_draft.py`) to create a `StrategyDraft` (Pydantic model).
  - The `StrategyDraftOutputTool` is called (triggering a `on_tool_start` event for the frontend).
  - The backend returns the `StrategyDraft` to the frontend.
  - User (optionally) provides feedback on the draft, which is sent back to the backend. The agent uses this feedback to improve the strategy.
  - When the user is satisfied, they request to deploy the strategy (`POST /api/v1/strategies`).
  - The backend sends the `StrategyDraft` to `graph_strategy_code.py`, which uses the LLM (with prompts defined in `agents/strategy/prompts/strategy_code.py`) to generate Freqtrade-compatible Python code.
  - The backend (via `service_strategies.py`) creates a new `StrategiesORM` entry, storing the strategy name, code, file path, user ID, draft, and chat ID.
  - The backend (via `FTStrategies`) writes the generated code to a `.py` file in the user's Freqtrade strategies directory.
  - The backend updates the chat messages to link the strategy creation output to the strategy id.
  - The backend returns the new strategy's details to the frontend.
  - User requests a list of their strategies (`GET /api/v1/strategies`).
  - Backend retrieves all `StrategiesORM` entries associated with the user.
  - Backend returns a list of strategy summaries.
  - User requests a specific strategy (`GET /api/v1/strategies/{strategy_id}`).
  - Backend retrieves the specified `StrategiesORM` entry if it belongs to the user.
  - Backend returns the complete strategy details.
  - User requests to delete a strategy (`DELETE /api/v1/strategies/{strategy_id}`).
  - Backend deletes the `StrategiesORM` entry, the associated strategy file, and removes the strategy ID from any related chat messages.
- **Functional Requirements:**
  - FR.17: The system MUST use an AI agent (LLM) to generate trading strategies based on user input.
  - FR.18: The system MUST generate Freqtrade-compatible Python code for strategies.
  - FR.19: The system MUST store generated strategy code in the database.
  - FR.20: The system MUST store the generated strategy code in a `.py` file in the user's Freqtrade directory.
  - FR.21: The system MUST associate each strategy with a unique name.
  - FR.22: The system MUST associate each strategy with the authenticated user.
  - FR.23: The system MUST allow users to retrieve a list of their strategies.
  - FR.24: The system MUST allow users to retrieve a specific strategy by ID.
  - FR.25: The system MUST allow users to delete their strategies.
  - FR.26: The system MUST delete the strategy file when a strategy is deleted.
  - FR.27: The system MUST allow users to create strategies based on a textual description (Strategy Draft).
  - FR.28: The system MUST store a JSON representation of the Strategy Draft.

### 4.4. Backtesting

- **Description:** Allows users to run historical backtests of their strategies using Freqtrade.
- **Stimulus/Response Sequences:**
  - User sends a request to start a backtest (`POST /api/v1/backtests`) with the strategy ID and date range.
  - Backend validates that the strategy exists and belongs to the user.
  - Backend creates a new `BacktestsORM` entry with status "downloading_data".
  - Backend enqueues a Celery task (`run_backtest_task` in `tasks/backtests.py`).
  - Backend returns the new backtest's ID to the frontend.
  - The Celery task:
    - Downloads required market data using `FTMarketData`.
    - Verifies market data. If verification fails set status to 'failed' and return.
    - Updates the `BacktestsORM` entry status to "running".
    - Executes the Freqtrade backtest command via Docker (`FTBacktesting`).
    - If the backtest is successful, updates the `BacktestsORM` entry with the results file path and status "finished".
    - If the backtest fails, updates the `BacktestsORM` entry with status "failed" and error information.
  - User requests the status/results of a backtest (`GET /api/v1/backtests/{backtest_id}`).
  - Backend retrieves the `BacktestsORM` entry if it belongs to the user (via the associated strategy).
  - Backend returns the backtest status and, if finished, the results file path.
- **Functional Requirements:**
  - FR.29: The system MUST allow users to initiate backtests for their strategies.
  - FR.30: The system MUST require a strategy ID and date range for backtests.
  - FR.31: The system MUST use Celery to run backtests asynchronously.
  - FR.32: The system MUST update the backtest status in the database during the backtest process.
  - FR.33: The system MUST store the path to the Freqtrade backtest results file.
  - FR.34: The system MUST handle backtest failures and record error information.
  - FR.35: The system MUST allow users to retrieve the status and results of a backtest.
  - FR.36: The system MUST download necessary market data before running the backtest.
  - FR.37: The system MUST verify downloaded market data before running the backtest.

### 4.5. Freqtrade User Directory Management

- **Description**: Automatically manages Freqtrade user data directories.
- **Stimulus/Response Sequences:**
  - Backend receives a 'user.created' webhook event
  - `FTUserDir` class is instantiated with user's clerk_id.
  - `initialize()` method is called. This does the following:
    - Creates user directory `ft_userdata/user_<clerk_id>`
    - Copies `docker-compose.template` to user directory.
    - Creates a `config.json` in `ft_userdata/user_<clerk_id>/user_data`.
  - Backend receives a 'user.deleted' webhook event.
  - `FTUserDir` class is instantiated with user's clerk_id.
  - `remove()` method is called to remove the user directory, including strategies, data, and configuration.
- **Functional Requirements:**
  - FR.38: The system MUST automatically initialize a Freqtrade user data directory when a user is created.
  - FR.39: The system MUST create the user directory in a consistent, predictable location, based on the user's Clerk ID.
  - FR.40: The system MUST create a `docker-compose.yml` file in the user's Freqtrade directory.
  - FR.41: The system MUST create a default `config.json` file in the user's `user_data` directory.
  - FR.42: The system MUST automatically remove a user's Freqtrade user data directory, including all subdirectories and files, when the user is deleted.
  - FR.43 The user's freqtrade directory MUST have subdirectories: `user_data`, `data`, `strategies`, `backtest_results`.
  - FR.44 The `user_data` directory MUST contain a `config.json` file.

## 5. External Interface Requirements

### 5.1. User Interfaces

- The backend does not provide a user interface. It provides a RESTful API for use by a frontend application.
- All API responses should be in JSON format.

### 5.2. Hardware Interfaces

- None.

### 5.3. Software Interfaces

- **Clerk:** Authentication and user management.
- **PostgreSQL:** Database for storing user data, chat histories, strategies, and backtest results.
- **RabbitMQ:** Message broker for Celery task queue.
- **Celery:** Asynchronous task queue for running backtests.
- **Freqtrade:** Cryptocurrency trading bot framework.
- **Docker:** Containerization platform for running Freqtrade.
- **OpenAI API / Anthropic API:** For AI-powered strategy generation.
- **Langchain/LangGraph:** AI agent orchestration.
- **FastAPI:** Web framework.
- **SQLAlchemy:** Database ORM.
- **Pydantic:** Data validation and settings management.

### 5.4. Communications Interfaces

- **HTTP/HTTPS:** For API requests and responses.
- **AMQP:** For communication with the RabbitMQ message broker.
- **Webhooks:** For receiving events from Clerk.

## 6. Nonfunctional Requirements

### 6.1. Performance Requirements

- API response times should be minimized (target < 500ms for most endpoints).
- Strategy generation should be completed within a reasonable timeframe (target < 30 seconds).
- The system should be able to handle a large number of concurrent users and backtests.

### 6.2. Scalability Requirements

- The system should be designed to scale horizontally (e.g., by adding more Celery workers or API server instances).
- The database should be able to handle a large number of users, strategies, and backtests.

### 6.3. Security Requirements

- User authentication MUST be handled by Clerk.
- API access MUST be restricted to authenticated users.
- User data MUST be protected from unauthorized access.
- Sensitive data (e.g., API keys) MUST be stored securely.
- Generated strategy code should be reviewed for potential security vulnerabilities.

### 6.4. Maintainability Requirements

- The codebase should be modular and well-documented.
- Consistent coding style and conventions should be followed.
- Dependencies should be managed using a dependency management tool (Poetry).
- Database migrations should be managed using Alembic.

### 6.5. Reliability Requirements

- The system should be designed to handle failures gracefully.
- Error handling and logging should be implemented throughout the codebase.
- Backtests should be able to recover from failures (e.g., by retrying or resuming).
- Market data download should be verified.

## 7. Other Requirements

- **Documentation:** The codebase should be well-documented, including API documentation, developer documentation, and user documentation.
- **Testing:** Unit tests and integration tests should be written to ensure code quality and functionality.

This document provides a comprehensive overview of the requirements for the GenTrade backend. It should be used as a guide for development and testing. This document will evolve as the project progresses and new requirements are identified.
