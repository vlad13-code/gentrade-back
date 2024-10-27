from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from dotenv import load_dotenv

from fastapi import Depends, FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langserve import add_routes
from langgraph.store.postgres.aio import AsyncPostgresStore
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from pydantic import BaseModel
from psycopg_pool import AsyncConnectionPool

from app.agents.main.graph_main import graph_main
from app.config import settings
from app.dependencies import check_auth
from app.routers.v1.routers import all_routers

load_dotenv()


class ChatInputType(BaseModel):
    input: list[HumanMessage | AIMessage | SystemMessage]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    connection_kwargs = {
        "autocommit": True,
        "prepare_threshold": 0,
    }
    async with AsyncPostgresStore.from_conn_string(
        settings.DATABASE_URL_asyncpg_pool
    ) as store:
        graph_main.store = store

        async with AsyncConnectionPool(
            conninfo=settings.DATABASE_URL_asyncpg_pool,
            max_size=20,
            kwargs=connection_kwargs,
        ) as pool:
            checkpointer = AsyncPostgresSaver(pool)
            # Uncomment if setup is necessary
            await checkpointer.setup()
            graph_main.checkpointer = checkpointer
            app.state.agent = graph_main
            yield  # Yield control back to the application


app = FastAPI(
    title="GenTrade API",
    version="1.0",
    lifespan=lifespan,
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
    )


# async def check_auth_modify_config(config: dict, request: Request) -> dict:
#     if app.state.session:
#         config["configurable"]["user_id"] = app.state.session["sub"]
#         config["configurable"]["thread_id"] = app.state.session["sid"]
#         config["configurable"]["run_id"] = str(uuid.uuid4())
#         print(config["configurable"]["thread_id"])
#     return config


async def check_thread_id(config: dict, request: Request):
    if "threadid" in request.headers:
        config["configurable"]["thread_id"] = request.headers["threadid"]
    return config


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

runnable = graph_main.with_types(input_type=ChatInputType, output_type=dict)
add_routes(
    app,
    runnable,
    path="/chat",
    playground_type="chat",
    per_req_config_modifier=check_thread_id,
    enabled_endpoints=["stream_events", "feedback"],
    enable_feedback_endpoint=True,
    dependencies=[Depends(check_auth)],
)

# Example of adding a path prefix to a group of routers
for router in all_routers:
    app.include_router(router, prefix="/api/v1")

if not hasattr(app, "openapi_tags") or app.openapi_tags is None:
    app.openapi_tags = []

app.openapi_tags.append(
    {
        "name": "chats",
        "description": "Chat history endpoints. Designed for using on frontend.",
    }
)
