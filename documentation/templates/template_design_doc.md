# [Feature/Component Name] Design Document (GenTrade Backend)

## Current Context

- **Overview:** Briefly describe how this feature fits into the existing GenTrade system. Mention relevant existing components (e.g., "This feature extends the backtesting capabilities currently managed by `app/tasks/backtests.py` and `app/db/services/service_backtests.py`").
- **Key Components:** List _specific_ files and classes that are relevant. (e.g., `BacktestsORM`, `FTBacktesting`, `router_backtests.py`). This helps Claude focus.
- **Pain Points:** Be explicit. Don't just say "enhances user experience." Say _how_ (e.g., "Reduces the latency between backtest request and results display" or "Provides more granular error messages for failed backtests").

## Requirements

### Functional Requirements

- **Be Very Specific:** Instead of "User can create a strategy," use "User can submit a natural language description of a trading strategy via the `/chat` endpoint, which will be processed by the `strategy_draft` agent to generate a `StrategyDraft`."
- **Refer to Existing Code:** Whenever possible, link requirements to existing files/classes. (e.g., "The system must use the `FTBacktesting` class in `app/util/ft/ft_backtesting.py` to execute backtests.")
- **Freqtrade Focus:** Frame requirements in terms of Freqtrade functionality where appropriate (e.g., "The feature must support custom stoploss logic using the `custom_stoploss()` method in Freqtrade strategies.").
- **Data Validation:** Explicitly state data validation requirements, referencing Pydantic models. (e.g., "Input data for backtests must conform to the `BacktestStartSchema` in `app/schemas/schema_backtests.py`").
- **API Endpoints:** If the feature involves new API endpoints, specify them clearly (e.g., `POST /api/v1/strategies/{strategy_id}/optimize`). Include expected request and response formats (using Pydantic model names).
- **AI Agent Interaction**: If the feature requires AI agent interaction, write in detail how it will interact with the agents, which agents it will use, and how.
- **Celery Tasks:** If the feature involves background tasks, define the Celery task's responsibilities and any data it needs.
- **Error Handling:** Define expected error scenarios and how they should be handled (e.g., "If Freqtrade fails to generate a strategy file, the system must return a 500 error with a descriptive message and log the error details.").

### Non-Functional Requirements

- **Performance:** Be specific about performance targets (e.g., "Strategy generation should complete within 15 seconds for 95% of requests").
- **Scalability:** Consider how the feature will scale (e.g., "The backtesting system should be able to handle at least 100 concurrent backtest requests using Celery workers.").
- **Observability:** Explicitly mention logging requirements (e.g., "Log all backtest start and end times, along with the `backtest_id` and `strategy_id`"). Use structured logging (JSON format) as defined in your project.
- **Security:**
  - **Authentication:** Mention Clerk authentication (e.g., "All API endpoints must be protected by Clerk authentication using the `check_auth` dependency.").
  - **Authorization:** Reinforce user ownership (e.g., "Users can only access/modify strategies and backtests associated with their `clerk_id`").
  - **Data Validation:** Refer to Pydantic models for input validation.
  - **Freqtrade Security:** Acknowledge potential risks of user-provided code (e.g., "Generated Freqtrade strategies should be reviewed for potential security vulnerabilities before deployment.").

## Design Decisions

- **Justification:** For _every_ decision, explain the _why_ clearly. Relate it to project goals (e.g., "We will use Celery for backtesting to avoid blocking the main API thread and allow for horizontal scaling.").
- **Alternatives:** Briefly mention alternatives considered and why they were rejected. This is crucial for Claude to understand the trade-offs. (e.g., "We considered using FastAPI's BackgroundTasks, but chose Celery for its robustness and scalability.").
- **Dependencies:** List any _new_ dependencies introduced by this feature.

## Technical Design

### 1. Core Components

```python
# Example:  This is a GOOD example, very specific to your project.
class BacktestService:
    """
    Manages backtest execution and results retrieval.
    Interacts with the BacktestsRepository, Freqtrade, and Celery.
    """
    async def create_backtest(self, uow: IUnitOfWork, user: UsersORM, strategy_id: int, date_range: str) -> BacktestSchema:
        ...

    async def get_backtest(self, uow: IUnitOfWork, user: UsersORM, backtest_id: int) -> BacktestSchema:
        ...

# Example: BAD example (too generic)
# class MainComponent:
#     """Core documentation"""
#     pass
```

- **Use Existing Classes:** If the feature primarily _extends_ existing classes, show the _relevant methods_ of those classes in the code snippet. Don't redefine the whole class.
- **Type Hints:** Use type hints _everywhere_. Use your Pydantic models and ORM models in the type hints.
- **Docstrings:** Use concise, informative docstrings, especially for public-facing methods.

### 2. Data Models

```python
# Example: GOOD example - references existing Pydantic models
from app.schemas.schema_backtests import BacktestSchema, BacktestStartSchema

# Example: If you need a *new* Pydantic model, define it here:
class BacktestOptimizationRequest(BaseModel):
      strategy_id: int
      parameter_ranges: dict[str, tuple[float, float]] # e.g., {"rsi_buy": (20, 40), "rsi_sell": (60, 80)}
      objective_function: str  # e.g., "maximize_profit", "minimize_drawdown"
```

- **Pydantic Models:** Define any _new_ Pydantic models needed for request/response bodies or internal data structures.
- **ORM Models:** If you need to modify existing ORM models (e.g., `BacktestsORM`), show the _changes_ (additions, modifications). Don't redefine the whole model.

### 3. Integration Points

- **Be Exhaustive:** This is where you tell Claude _exactly_ how the new feature connects to the rest of the system.
- **Example (good):**
  - "This feature adds a new endpoint: `POST /api/v1/strategies/{strategy_id}/backtest` (defined in `app/routers/v1/router_backtests.py`)."
  - "The endpoint will use the `BacktestsService` (in `app/db/services/service_backtests.py`) to create a new `BacktestsORM` record."
  - "The `BacktestsService` will enqueue a `run_backtest_task` (defined in `app/tasks/backtests.py`) to Celery."
  - "The `run_backtest_task` will use the `FTBacktesting` class (in `app/util/ft/ft_backtesting.py`) to execute the Freqtrade backtest command in a Docker container."
  - "The agent graph `graph_main` (in `agents/main/graph_main.py`), will use the `strategy` agent."
  - "The new data will be provided to the `strategy` agent using the tool `strategy_draft_output_tool` in `agents/strategy/tools/strategy_draft_output.py`"
  - "The `BacktestsORM` model (in `app/db/models/backtests.py`) will be updated with the backtest status and results file path."

### 4. Agent Interaction

- **Agent Communication:** Describe how the new feature interacts with the AI agents (if it does). Mention:
  - **Entry Point:** Will the user interact directly with the chat interface, or will the feature be triggered by another part of the system?
  - **Routing:** How will the main agent (`graph_main.py`) route the request to the correct sub-agent (if applicable)? Will you need to modify `router_instructions`?
  - **Prompts:** Will you need to add or modify any prompts in `app/agents/.../prompts`? If so, describe the changes.
  - **Tools:** Will the agent need to use any existing or new tools? If new, describe the tool's purpose and inputs/outputs.
  - **State:** How will the feature affect the agent's state (`AgentState`)? Will you need to add new fields to the state?
  - **Checkpoints**: If this will impact LangGraph checkpoints somehow, mention it.
- **Example (good):**
  - "This feature will be initiated by a new button in strategy widget, that will make a request to a new route /api/v1/strategies/{strategy_id}/improve. This route will send initial message to the `strategy_draft` agent with provided `strategy_id`."
  - "The agent will then be in the loop, where user can provide iterative feedback, using prompts, defined in `app/agents/strategy/prompts/strategy_draft.py`"
  - "The existing tool, `strategy_draft_output_tool`, will be used to provide structured output that will be saved to the database in `StrategiesORM.draft`"

## Implementation Plan

- **Phases:** Break down the implementation into logical phases. This helps with planning and allows for incremental testing.
- **Tasks:** Be _very_ specific about the tasks. (e.g., "Add a `status` field to the `BacktestsORM` model" is better than "Update database").
- **Timeline:** Provide realistic estimates for each phase.

## Observability

### Logging

- **Be Specific:** Don't just say "Key logging points." Say _what_ you're logging at each point. (e.g., "Log the `backtest_id`, `strategy_id`, and `date_range` when a backtest is started.").
- **Structured Logging:** Emphasize the use of structured logging (JSON format) so you can easily query and analyze logs. Mention relevant keys.
- **Correlation ID:** Mention the use of a correlation ID (if you're using one) to track requests across different components.
- **Example:**

```json
{
  "timestamp": "2025-01-29T14:30:00Z",
  "level": "INFO",
  "correlation_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "component": "BacktestsService",
  "event": "backtest_started",
  "user_id": "user_123",
  "strategy_id": 456,
  "backtest_id": 789,
  "date_range": "20240101-20240128"
}
```

## Future Considerations

- **Realistic Enhancements:** Think about how this feature might be extended in the future.
- **Known Limitations:** Be honest about any limitations or trade-offs. This is crucial for maintainability.

## Dependencies

- **List _new_ dependencies:** Only list dependencies that are being _added_ by this feature.

## Security Considerations

- **Reiterate:** Even if it seems obvious, reiterate security points related to authentication, authorization, and data validation.
- **Freqtrade Specific:** Address any security concerns specific to running Freqtrade (e.g., safely handling user-provided strategy code).

## Rollout Strategy

- **Phased Rollout:** Describe how you'll roll out the feature (e.g., to a small group of users first, then to everyone).
- **Monitoring:** Mention how you'll monitor the feature after deployment (e.g., using logs, metrics, error tracking).
- **Rollback:** Briefly describe how you'll roll back the feature if something goes wrong.

## References

- **Link to relevant files:** Link directly to the files in your project. This is especially useful in Cursor. (e.g., "See `app/db/models/backtests.py` for the `BacktestsORM` model.")
- **Link to external documentation:** Link to relevant documentation for Freqtrade, Langchain, FastAPI, etc.
