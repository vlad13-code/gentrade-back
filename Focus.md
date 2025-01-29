# Project Focus: gentrade-back

**Current Goal:** Project directory structure and information

**Project Context:**
Type: Language: unknown
Target Users: Users of gentrade-back
Main Functionality: Project directory structure and information
Key Requirements:
- Type: Generic Project
- Language: unknown
- Framework: none
- File and directory tracking
- Automatic updates

**Development Guidelines:**
- Keep code modular and reusable
- Follow best practices for the project type
- Maintain clean separation of concerns

# 📁 Project Structure
└─ 📁 app
   ├─ 📄 __init__.py (0 lines) - Python script containing project logic
   ├─ 📄 config.py (52 lines) - Python script containing project logic
   ├─ 📄 dependencies.py (51 lines) - Python script containing project logic
   ├─ 📄 main.py (120 lines) - Python script containing project logic
   ├─ 📁 agents
   │  ├─ 📄 __init__.py (0 lines) - Python script containing project logic
   │  ├─ 📄 model.py (3 lines) - Python script containing project logic
   │  ├─ 📁 main
   │  │  ├─ 📄 __init__.py (0 lines) - Python script containing project logic
   │  │  ├─ 📄 graph_main.py (113 lines) - Python script containing project logic
   │  │  └─ 📄 schemas.py (27 lines) - Python script containing project logic
   │  └─ 📁 strategy
   │     ├─ 📄 __init__.py (0 lines) - Python script containing project logic
   │     ├─ 📄 graph_strategy_code.py (60 lines) - Python script containing project logic
   │     ├─ 📄 graph_strategy_draft.py (100 lines) - Python script containing project logic
   │     └─ 📄 schemas.py (40 lines) - Python script containing project logic
   ├─ 📁 celery
   │  ├─ 📄 celery_async.py (98 lines) - Python script containing project logic
   │  └─ 📄 celery_rmq_connector.py (64 lines) - Python script containing project logic
   ├─ 📁 db
   │  ├─ 📄 db.py (36 lines) - Python script containing project logic
   │  ├─ 📁 migrations
   │  │  └─ 📄 env.py (100 lines) - Python script containing project logic
   │  ├─ 📁 models
   │  │  ├─ 📄 __init__.py (6 lines) - Python script containing project logic
   │  │  ├─ 📄 _common.py (12 lines) - Python script containing project logic
   │  │  ├─ 📄 backtests.py (26 lines) - Python script containing project logic
   │  │  ├─ 📄 chats.py (24 lines) - Python script containing project logic
   │  │  ├─ 📄 strategies.py (29 lines) - Python script containing project logic
   │  │  └─ 📄 users.py (35 lines) - Python script containing project logic
   │  ├─ 📁 repositories
   │  │  ├─ 📄 repo_backtests.py (6 lines) - Python script containing project logic
   │  │  ├─ 📄 repo_chats.py (6 lines) - Python script containing project logic
   │  │  ├─ 📄 repo_strategies.py (6 lines) - Python script containing project logic
   │  │  └─ 📄 repo_users.py (6 lines) - Python script containing project logic
   │  ├─ 📁 services
   │  │  ├─ 📄 service_backtests.py (78 lines) - Python script containing project logic
   │  │  ├─ 📄 service_chats.py (142 lines) - Python script containing project logic
   │  │  ├─ 📄 service_strategies.py (123 lines) - Python script containing project logic
   │  │  └─ 📄 service_users.py (59 lines) - Python script containing project logic
   │  └─ 📁 utils
   │     ├─ 📄 chat_message_utils.py (43 lines) - Python script containing project logic
   │     ├─ 📄 decorators.py (67 lines) - Python script containing project logic
   │     ├─ 📄 repository.py (69 lines) - Python script containing project logic
   │     └─ 📄 unitofwork.py (93 lines) - Python script containing project logic
   ├─ 📁 dependencies
   │  └─ 📄 celery.py (23 lines) - Python script containing project logic
   ├─ 📁 routers
   │  ├─ 📄 __init__.py (0 lines) - Python script containing project logic
   │  └─ 📁 v1
   │     ├─ 📄 __init__.py (0 lines) - Python script containing project logic
   │     ├─ 📄 router_backtests.py (37 lines) - Python script containing project logic
   │     ├─ 📄 router_chats.py (82 lines) - Python script containing project logic
   │     ├─ 📄 router_strategies.py (63 lines) - Python script containing project logic
   │     ├─ 📄 router_users.py (45 lines) - Python script containing project logic
   │     ├─ 📄 router_webhooks.py (71 lines) - Python script containing project logic
   │     └─ 📄 routers.py (13 lines) - Python script containing project logic
   ├─ 📁 schemas
   │  ├─ 📄 schema_backtests.py (23 lines) - Python script containing project logic
   │  ├─ 📄 schema_chats.py (36 lines) - Python script containing project logic
   │  ├─ 📄 schema_clerk_webhook_event.py (60 lines) - Python script containing project logic
   │  ├─ 📄 schema_strategies.py (43 lines) - Python script containing project logic
   │  └─ 📄 schema_users.py (22 lines) - Python script containing project logic
   ├─ 📁 tasks
   │  ├─ 📄 __init__.py (1 lines) - Python script containing project logic
   │  └─ 📄 backtests.py (77 lines) - Python script containing project logic
   └─ 📁 util
      ├─ 📄 exceptions.py (16 lines) - Python script containing project logic
      ├─ 📄 ft_backtesting.py (70 lines) - Python script containing project logic
      ├─ 📄 ft_strategies.py (113 lines) - Python script containing project logic
      └─ 📄 ft_userdir.py (106 lines) - Python script containing project logic

# 🔍 Key Files with Methods

`app/tasks/backtests.py` (77 lines)
Functions:
- get_scoped_uow
- run_backtest_task

`app/db/models/backtests.py` (26 lines)
Functions:
- BacktestsORM

`app/dependencies/celery.py` (23 lines)
Functions:
- endpoint
- get_celery_connector

`app/celery/celery_async.py` (98 lines)
Functions:
- AsyncCelery
- AsyncTask
- apply_async
- async_run
- loop
- on_failure
- rmq_connector
- send_task

`app/celery/celery_rmq_connector.py` (64 lines)
Functions:
- CeleryRMQConnector
- _get_connection_channel
- send_task

`app/db/utils/chat_message_utils.py` (43 lines)
Functions:
- ChatMessageUtils
- add_strategy_id_to_message
- remove_strategy_id_from_message

`app/db/models/chats.py` (24 lines)
Functions:
- ChatsORM

`app/config.py` (52 lines)
Functions:
- Config
- DATABASE_URL_asyncpg
- DATABASE_URL_asyncpg_pool
- DATABASE_URL_psycopg
- Settings

`app/db/db.py` (36 lines)
Functions:
- Base
- async_session_maker
- get_async_session

`app/db/utils/decorators.py` (67 lines)
Functions:
- require_user
- wrapper

`app/dependencies.py` (51 lines)
Functions:
- check_auth
- get_celery_connector

`app/db/migrations/env.py` (100 lines)
Functions:
- begin_transaction
- do_run_migrations
- run_async_migrations
- run_migrations_offline
- run_migrations_online

`app/util/exceptions.py` (16 lines)
Functions:
- DockerBacktestError
- PickleableDockerException

`app/util/ft_backtesting.py` (70 lines)
Functions:
- run_backtest_in_docker

`app/util/ft_strategies.py` (113 lines)
Functions:
- delete_strategy_file
- get_user_strategies_dir
- to_camel_case
- user_id
- write_strategy_file

`app/util/ft_userdir.py` (106 lines)
Functions:
- get_user_data_directory
- init_ft_userdir
- remove_ft_userdir
- user_dir_exists
- user_id
- will

`app/agents/main/graph_main.py` (113 lines)
Functions:
- acall_model
- main
- main_router

`app/agents/strategy/graph_strategy_code.py` (60 lines)
Functions:
- generate_strategy_code
- main

`app/agents/strategy/graph_strategy_draft.py` (100 lines)
Functions:
- create_strategy_draft
- human_feedback
- main
- should_continue

`app/main.py` (120 lines)
Functions:
- AsyncConnectionPool
- ChatInputType
- check_thread_id
- exception_handler
- lifespan
- validation_exception_handler

`app/db/repositories/repo_backtests.py` (6 lines)
Functions:
- BacktestsRepository

`app/db/repositories/repo_chats.py` (6 lines)
Functions:
- ChatsRepository

`app/db/repositories/repo_strategies.py` (6 lines)
Functions:
- StrategiesRepository

`app/db/repositories/repo_users.py` (6 lines)
Functions:
- UsersRepository

`app/db/utils/repository.py` (69 lines)
Functions:
- AbstractRepository
- SQLAlchemyRepository
- add_one
- delete_one
- delete_one_by
- edit_one
- find_all
- find_all_by
- find_all_by_ordered
- find_one

`app/routers/v1/router_backtests.py` (37 lines)
Functions:
- create_backtest
- get_backtest

`app/routers/v1/router_chats.py` (82 lines)
Functions:
- add_chat
- delete_chat
- get_chat
- get_chat_list
- update_chat

`app/routers/v1/router_strategies.py` (63 lines)
Functions:
- add_strategy
- delete_strategy
- get_strategies
- get_strategy

`app/routers/v1/router_users.py` (45 lines)
Functions:
- UserAdded
- UserAlreadyExists
- add_user

`app/routers/v1/router_webhooks.py` (71 lines)
Functions:
- clerk_webhook_handler

`app/schemas/schema_backtests.py` (23 lines)
Functions:
- BacktestCreated
- BacktestSchema
- BacktestSchemaAdd
- BacktestStartSchema

`app/schemas/schema_chats.py` (36 lines)
Functions:
- ChatListItemSchema
- ChatSchema
- ChatSchemaAddUpdate
- ResponseChatAdded
- ResponseChatNotFound

`app/schemas/schema_clerk_webhook_event.py` (60 lines)
Functions:
- ClerkWebhookEvent
- EmailAddress
- EventAttributes
- HttpRequest
- UserData
- Verification

`app/schemas/schema_strategies.py` (43 lines)
Functions:
- StrategyDraftSchemaAdd
- StrategySchema
- StrategySchemaAdd

`app/schemas/schema_users.py` (22 lines)
Functions:
- ResponseUserNotFound
- UserSchema
- UserSchemaAdd
- UserSchemaAuth

`app/agents/main/schemas.py` (27 lines)
Functions:
- AgentState
- RouterResponse
- get_agent_descriptions

`app/agents/strategy/schemas.py` (40 lines)
Functions:
- CreateStrategyDraftState
- GenerateStrategyCodeState
- StrategyCode
- StrategyDraft

`app/db/services/service_backtests.py` (78 lines)
Functions:
- BacktestsService
- create_backtest
- get_backtest

`app/db/services/service_chats.py` (142 lines)
Functions:
- ChatsService
- add_chat
- delete_chat
- get_chat
- get_chat_list
- update_chat

`app/db/services/service_strategies.py` (123 lines)
Functions:
- StrategiesService
- add_strategy
- delete_strategy
- get_strategy
- get_user_strategies

`app/db/services/service_users.py` (59 lines)
Functions:
- UsersService
- _get_user_by_clerk_id
- add_user
- delete_user
- uow

`app/db/models/strategies.py` (29 lines)
Functions:
- StrategiesORM

`app/db/utils/unitofwork.py` (93 lines)
Functions:
- IUnitOfWork
- ScopedUnitOfWork
- UnitOfWork
- commit
- get_scoped_uow
- remove
- rollback

`app/db/models/users.py` (35 lines)
Functions:
- UsersORM

# 📊 Project Overview
**Files:** 55  |  **Lines:** 2,595

## 📁 File Distribution
- .py: 55 files (2,595 lines)

*Updated: January 29, 2025 at 01:46 PM*