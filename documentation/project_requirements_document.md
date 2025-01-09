Below are **refined versions** of your **project_requirements_document.md** and **app_flow_document.md**, enhanced with references to the backend architecture and code features you’ve provided. Feel free to copy/paste and adapt these to your existing documentation.

---

# project_requirements_document.md

## 1. Overview

GenTrade is a platform for generating and managing crypto trading bots. The application combines:

- A **FastAPI**-based backend that leverages **LLM-based** Python code generation to produce Freqtrade strategies.
- A **chat-oriented frontend** that enables non-technical users to create and manage trading bots using natural language prompts.
- A secure authentication layer handled by **Clerk** (via `fastapi-clerk-auth`).

The system’s goal is to simplify the process of building, backtesting, and deploying algorithmic strategies without the user needing in-depth programming or DevOps knowledge.

## 2. Stakeholders

1. **End Users / Traders**

   - Typically novices who want to create, deploy, and run trading bots in an accessible, user-friendly environment.

2. **Developers**
   - Extend the platform’s feature set, maintain the codebase, and oversee performance and security updates.

## 3. Functional Requirements

1. **User Authentication and Session Management**

   - Must integrate with **Clerk** to handle sign-ups, logins, and session tokens.
   - The backend enforces authentication via `fastapi_clerk_auth`.
   - Clerk webhooks are processed in `/webhooks/clerk` to create or remove user accounts accordingly.

2. **AI-Powered Strategy Creation**

   - Users see strategy suggestions (e.g., “Create Bitcoin SMA cross strategy”) in the chat interface.
   - A typed or clicked suggestion triggers an **LLM** (see `app/agents/main/graph_main.py`) to generate a trading strategy.

3. **Strategy Editing**

   - Users can click **Edit** to open a popup that allows modifying relevant properties (indicators, timeframe, etc.).
   - The system must store these updates so users can refine strategy details before deployment.

4. **Strategy Deployment**

   - Clicking **Deploy** sends the strategy description to the **backend** (via `/api/v1/strategies` or the chat-based route at `/chat`).
   - The backend calls the LLM to produce a **Freqtrade**-compatible Python script, which is saved to the database (`StrategiesORM.code` column).
   - The new strategy then appears in the user’s side panel with the ability to **Backtest** or **Delete**.

5. **Backtesting**

   - Clicking **Backtest** opens a date-range selection popup.
   - The backend should run a simulation (in future expansions, it may call a separate service or Celery task).
   - The UI shows a spinner and disables the widget until the backtest completes.

6. **Strategy Management and Deletion**

   - The user can list, view, and delete existing strategies.
   - Deleting a strategy removes it from the system database (`app/db/models/strategies.py`).

7. **Database and Migrations**

   - **PostgreSQL** is the main database (configured in `config.py` via `DATABASE_URL_*`).
   - Database schema changes are handled by **Alembic** (see `alembic.ini` and `app/db/migrations/`).
   - The default structure includes tables for `users`, `chats`, `strategies`, as well as `langgraph` store and checkpoints for conversation states.

8. **Notifications and Error Handling**
   - The platform must surface user-friendly error messages if a strategy fails to generate or a backtest fails.
   - The system logs any exceptions for diagnostic purposes (`logging.error(...)` in the services layer).

## 4. Non-Functional Requirements

1. **Scalability**

   - Must handle many concurrent users issuing requests to the LLM for strategy generation.
   - **Celery** and future worker processes can offload heavier tasks like long-running backtests or forward tests.

2. **Performance**

   - LLM-based code generation should complete within a user-friendly timeframe (e.g., < 30 seconds).
   - Database queries should be optimized via the repository pattern (`SQLAlchemyRepository` in `app/db/utils/repository.py`).

3. **Security**

   - Clerk’s JWT tokens must be validated (`check_auth`) prior to performing any user-specific DB operations.
   - Only authorized users can manipulate their own chats or strategies.

4. **Maintainability**

   - Code is separated into logical modules:
     - `agents/`: LLM logic, prompts, strategy building.
     - `db/`: database models, migrations, repositories, services.
     - `routers/`: FastAPI endpoints (e.g., `/api/v1/strategies`, `/api/v1/chats`).
   - Clear directory structure for easy onboarding of new devs.

5. **Reliability & Testing**
   - Should include tests for essential flows: strategy creation, editing, deployment, and backtesting.
   - Database tests and migrations should be validated in staging before production.

## 5. Constraints and Assumptions

- **Freqtrade** is the chosen open-source trading engine; the user data directory is managed by scripts (`init_ft_userdir`, etc.).
- The solution depends on stable connectivity to LLM providers (OpenAI, Anthropic, etc.) and will degrade gracefully otherwise.
- The system stores generated Python code in a `TEXT` field (`StrategiesORM.code`), which must be large enough for typical strategies.
