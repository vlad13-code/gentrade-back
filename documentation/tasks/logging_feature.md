# Logging System Enhancement Design Document (GenTrade Backend)

## Current Context

- **Overview:** The project currently has a basic logging setup in `app/util/logger.py` that uses `colorlog` for colored console output. However, logging is not standardized across all components, and it lacks structured logging for efficient analysis and correlation. We need a unified logging strategy across FastAPI, Celery, AI agents, and Freqtrade operations.
- **Key Components:**
  - `app/util/logger.py`: Existing logger setup.
  - `app/main.py`: FastAPI application entry point (for middleware integration).
  - `app/dependencies.py`: FastAPI dependency injection (for injecting the logger).
  - `app/tasks/backtests.py`: Celery task definition (for logging within tasks).
  - `app/agents/...`: AI agent code (for logging agent decisions).
  - `app/db/services/...`: Service layer (for logging business logic).
  - `app/util/ft/...`: Freqtrade integration (for logging Freqtrade operations).
- **Pain Points:**
  - Inconsistent logging practices across different parts of the application.
  - Lack of structured logging makes it difficult to parse and analyze logs programmatically.
  - Difficulty in correlating log entries across different components (e.g., a request through FastAPI, a Celery task, and Freqtrade execution).
  - Limited context information in log entries (e.g., user ID, strategy ID).
  - No support for centralized log aggregation or analysis.

## Requirements

### Functional Requirements

- **FR.1:** Implement a centralized logging configuration that can be used across all components (FastAPI, Celery, AI Agents, Freqtrade).
- **FR.2:** Provide component-specific loggers with hierarchical naming (e.g., `app.api.routers.users`, `app.tasks.backtests`).
- **FR.3:** Implement structured logging using JSON format. Each log entry MUST include:
  - `timestamp`: ISO8601 format (UTC).
  - `level`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
  - `correlation_id`: A unique ID to correlate log entries across a single request/operation.
  - `component`: The name of the component generating the log (e.g., `BacktestsService`, `FTBacktesting`).
  - `user_id`: The Clerk user ID, if available.
  - `strategy_id`: The ID of the relevant strategy, if available.
  - `backtest_id`: The ID of the relevant backtest, if available.
  - `message`: A human-readable log message.
  - `data`: An optional dictionary containing additional context-specific data.
- **FR.4:** Implement two log handlers:
  - **Console Handler:** Outputs colored log messages to stdout/stderr for development and debugging. Should use a human-readable format.
  - **JSON Handler:** Outputs structured JSON logs. Should include all context fields. The destination (file, network service) will be determined later.
- **FR.5:** Integrate logging with FastAPI middleware to automatically log all incoming requests and outgoing responses, including:
  - Request method (GET, POST, etc.)
  - Request path
  - Request headers (excluding sensitive information like authorization tokens)
  - Response status code
  - Request duration
  - Correlation ID
- **FR.6:** Integrate logging with Celery tasks to log task execution, including:
  - Task name
  - Task arguments
  - Task status (started, succeeded, failed)
  - Execution time
  - Any exceptions raised
  - Correlation ID (passed from the originating request)
- **FR.7:** Integrate logging with AI agents to log:
  - Agent name
  - Input to the agent
  - Output from the agent
  - Intermediate steps/decisions made by the agent
  - Tool calls and results
  - Correlation ID (passed from the originating request)
- **FR.8:** Integrate logging with Freqtrade operations to log:
  - Freqtrade command being executed
  - Relevant parameters (e.g., strategy name, date range)
  - Success/failure status
  - Output file paths (for backtests)
  - Any errors or warnings from Freqtrade
  - Correlation ID (passed from the originating request)
- **FR.9:** Provide a mechanism to easily add context data to log entries (e.g., `logger.info("Processing trade", data={"trade_id": 123})`).
- **FR.10:** Support configurable log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL) for each handler and component.
- **FR.11:** Propagate the `correlation_id` from FastAPI requests to Celery tasks and AI agents.

### Non-Functional Requirements

- **Performance:** Logging should have minimal impact on application performance. Asynchronous logging should be considered if necessary.
- **Scalability:** The logging system should be able to handle a high volume of log messages.
- **Security:** Sensitive data (e.g., API keys, passwords, user credentials) MUST NOT be logged.
- **Maintainability:** The logging system should be easy to configure, maintain, and extend.
- **Readability:** The console output should be easily readable by humans. The JSON output should be easily parsed by machines.

## Design Decisions

### 1. Logging Structure

We will use Python's built-in `logging` module with a hierarchical logger structure. This allows us to configure different log levels and handlers for different parts of the application. We will use a base logger named `app`.

**Rationale:** Python's `logging` module is standard, well-documented, and flexible. Hierarchical loggers allow for granular control and easy configuration.

### 2. Log Format

We will use a structured JSON format for the JSON handler. The console handler will use a colored, human-readable format using `colorlog`.

**Rationale:** JSON is easily parsed by machines and is suitable for log aggregation and analysis tools. `colorlog` improves readability in the console.

### 3. Context Propagation

We will use a combination of FastAPI dependency injection and Celery task headers to propagate the `correlation_id`.

**Rationale:** FastAPI's dependency injection allows us to easily access request-specific data (like the `correlation_id`) in our route handlers and services. Celery task headers allow us to pass metadata between tasks.

### 4. Libraries

- **`python-json-logger`:** For generating JSON-formatted logs.
- **`colorlog`:** For colored console output (already in use).
- **FastAPI's Request object:** To access request headers, path.
- **Celery's `self.request`**: To access task metadata.

## Technical Design

### 1. Core Components

```python
# app/util/logger.py (modified)

import logging
import colorlog
import json
from pythonjsonlogger import jsonlogger
from typing import Optional
from fastapi import Request
from celery import Task

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record['component'] = record.name
        #The rest of the fields will be added by middleware/decorators

def setup_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Set up a logger instance.

    Args:
        name (str, optional): Logger name.  If None, defaults to the root 'app' logger.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger_name = f"app.{name}" if name else "app"
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG) # Capture all levels, handlers will filter
    logger.propagate = False # Prevent duplicate logs

    if not logger.handlers:  # Only add handlers if they don't exist
        # Console Handler (Colored)
        console_handler = logging.StreamHandler()
        console_formatter = colorlog.ColoredFormatter(
            "%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(name)s%(reset)s - %(message)s",
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            },
        )
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.INFO) # Default console level
        logger.addHandler(console_handler)

        # JSON Handler
        json_handler = logging.StreamHandler() #  For now, also to stdout.  Change later.
        json_formatter = CustomJsonFormatter('%(timestamp)s %(level)s %(correlation_id)s %(message)s %(data)s')
        json_handler.setFormatter(json_formatter)
        json_handler.setLevel(logging.DEBUG) # Capture everything for JSON
        logger.addHandler(json_handler)

    return logger


# Example usage in a service:
# from app.util.logger import setup_logger
# logger = setup_logger(__name__)  # __name__ will be 'app.db.services.service_users'
# logger.info("User created", extra={"user_id": user.id, "data": {"email": user.email}})

```

### 2. Data Models

No new data models required for logging itself, as it relies on provided context.

### 3. Integration Points

- **FastAPI Middleware:** A middleware component will be added to `app/main.py` to:

  - Generate a `correlation_id` for each incoming request (using `uuid.uuid4()`).
  - Add the `correlation_id` to the request state (`request.state.correlation_id`).
  - Log the request details (method, path, headers - excluding sensitive info).
  - Log the response details (status code, duration).
  - Add the `correlation_id` to the logs.

- **Celery Task Decorator:** A custom Celery task class or decorator (similar to `AsyncTask` in `app/celery/celery_async.py`) will be created to:

  - Extract the `correlation_id` from the task headers (if present).
  - Add the `correlation_id` to the logging context.
  - Log task start, success, and failure events, including arguments and execution time.

- **`@require_user` Decorator:** The existing `@require_user` decorator in `app/db/utils/decorators.py` will be modified to add the `user.clerk_id` to the logging context.

- **AI Agents:**

  - The `app/agents/main/graph_main.py`, `app/agents/strategy/graph_strategy_code.py` and `app/agents/strategy/graph_strategy_draft.py` should be modified to add logging around all major steps in the agents.
  - All prompts should be logged.
  - All agent outputs should be logged.
  - All agent decisions should be logged.

- **Services and Repositories:** Service methods (`app/db/services/...`) and repository methods (`app/db/repositories/...`) will use the logger to log significant events (e.g., database operations, errors).

- **Freqtrade integration**: The `app/util/ft/` modules will be modified to log all interaction with docker and file system.

## Implementation Plan

1.  **Phase 1: Core Logging Infrastructure (3 days)**

    - Task 1: Modify `app/util/logger.py` to implement the `setup_logger` function as described above, including the `CustomJsonFormatter`.
    - Task 2: Create a FastAPI middleware in `app/main.py` to generate and propagate `correlation_id` and log request/response details.
    - Task 3: Create a custom Celery task class or decorator in `app/celery/celery_async.py` to handle `correlation_id` and log task events.
    - Task 4: Update the existing `@require_user` decorator to include the `user.clerk_id` in logger context.
    - Task 5: Add basic logging statements (INFO level) to key service methods (e.g., `create_backtest`, `add_strategy`).

2.  **Phase 2: Component Integration (4 days)**

    - Task 1: Integrate logging with AI agents (log inputs, outputs, decisions).
    - Task 2: Integrate logging with Freqtrade operations (log commands, success/failure, output file paths).
    - Task 3: Add more detailed logging to service and repository methods (DEBUG level for detailed operations, ERROR level for exceptions).
    - Task 4: Ensure consistent use of `extra` parameter in log calls to provide context.
    - Task 5: Review all existing log statements to make consistent

3.  **Phase 3: Testing and Refinement (3 days)**

    - Task 1: Write unit tests for the logging utility functions.
    - Task 2: Write integration tests to verify logging in various scenarios (successful requests, failed requests, Celery task execution, etc.).
    - Task 3: Review log output during development and testing, and adjust log levels and messages as needed.
    - Task 4: Configure log rotation/archiving (to be defined later - out of scope for initial implementation).

## Observability

### Logging

- **Key Logging Points:** (This list is not exhaustive, but provides examples)

  - **API Requests:** Start and end of each request, method, path, status code, duration, correlation ID, user ID.
  - **Authentication:** Successful and failed authentication attempts, user ID.
  - **Strategy Generation:** Input prompt, generated strategy code, strategy ID, user ID.
  - **Backtesting:** Backtest start, end, status, strategy ID, date range, correlation ID, output file path.
  - **Database Operations:** Successful and failed database queries (with parameters at DEBUG level), transaction start/commit/rollback.
  - **Celery Tasks:** Task start, success, failure, arguments, execution time, correlation ID.
  - **AI Agent Decisions:** Agent name, input, output, intermediate steps, tool calls, tool results.
  - **Freqtrade Operations:** Command executed, success/failure, output.
  - **Exceptions:** All exceptions should be logged with traceback information, level, and correlation ID.

- **Log Levels:**

  - `DEBUG`: Detailed debugging information (e.g., raw request/response data, database query parameters).
  - `INFO`: General operational events (e.g., backtest started, strategy created).
  - `WARNING`: Unexpected but handled situations (e.g., data download retry).
  - `ERROR`: Error events that don't necessarily stop the application (e.g., backtest failure).
  - `CRITICAL`: Critical errors that require immediate attention (e.g., database connection failure).

- **Structured Logging Format (JSON Handler):**

```json
{
  "timestamp": "2025-01-29T15:00:00.000Z",
  "level": "INFO",
  "correlation_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "component": "BacktestsService",
  "user_id": "user_123",
  "strategy_id": 456,
  "backtest_id": 789,
  "message": "Backtest started",
  "data": {
    "date_range": "20240101-20240128"
  }
}
```

- **Console Logging Format (Colorlog):**
  `%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(name)s%(reset)s - %(message)s`

## Future Considerations

### Potential Enhancements

- **Log Aggregation:** Integrate with a log aggregation system (e.g., ELK stack, Splunk, Datadog) for centralized log management and analysis.
- **Real-time Log Analysis:** Implement real-time log analysis to detect anomalies and trigger alerts.
- **Custom Log Viewers:** Create custom dashboards or tools for viewing and filtering logs.
- **Automated Log Analysis:** Use machine learning to automatically analyze logs and identify potential issues.
- **Log Rotation**: Implement log rotation to prevent log files from growing indefinitely.
- **Log Masking**: Add a mechanism for automatically masking sensitive data in log entries (e.g. replacing API keys with "**\*\*\*\***").
- **Asynchronous Logging**: Consider using asynchronous logging to reduce the performance impact of logging, especially for high-volume operations.

### Known Limitations

- **Initial Implementation:** The initial implementation will focus on console and JSON logging to stdout. Centralized log aggregation will be addressed in a future phase.
- **Performance Overhead:** Logging, especially at DEBUG level, can introduce some performance overhead. This should be monitored and optimized as needed.

## Dependencies

### Runtime Dependencies

- `python-json-logger`: For generating JSON-formatted logs.
- `colorlog`: For colored console output (already a dependency).
- No new dependencies on existing project libraries. Will utilize existing FastAPI, Celery, and logging functionalities.

### Development Dependencies

- `pytest`: For writing unit and integration tests.

## Security Considerations

- **Sensitive Data:** The logging system MUST NOT log any sensitive data, such as API keys, passwords, or user credentials. Careful review of log messages is required. Consider implementing data masking.
- **Log Access Control:** Access to logs should be restricted to authorized personnel.
- **Log Storage:** Logs should be stored securely and protected from unauthorized access.

## Rollout Strategy

1.  **Development Phase:**
    - Implement the core logging infrastructure (logger setup, middleware, Celery integration).
    - Add logging statements to key components (services, repositories, agents).
    - Write unit and integration tests.
2.  **Staging Deployment:**
    - Deploy the changes to a staging environment.
    - Validate the log format and content.
    - Assess the performance impact of logging.
3.  **Production Deployment:**
    - Gradually roll out the changes to production, monitoring logs and performance closely.
4.  **Monitoring Period:**
    - Collect feedback from developers and users.
    - Adjust log levels and messages as needed.
    - Fine-tune performance.

## References

- Current logger implementation: `app/util/logger.py`
- Celery logging documentation: [https://docs.celeryq.dev/en/stable/userguide/tasks.html#logging](https://docs.celeryq.dev/en/stable/userguide/tasks.html#logging)
- python-json-logger documentation: [https://github.com/madzak/python-json-logger](https://github.com/madzak/python-json-logger)
- colorlog documentation: [https://github.com/borntyping/python-colorlog](https://github.com/borntyping/python-colorlog)
