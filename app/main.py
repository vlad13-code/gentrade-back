import uuid
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager

import jwt
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langserve import add_routes
from pydantic import BaseModel

from app.agents.main.graph_main import graph_main
from app.config import settings

load_dotenv()


class ChatInputType(BaseModel):
    input: list[HumanMessage | AIMessage | SystemMessage]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Construct agent with Sqlite checkpointer
    # async with AsyncSqliteSaver.from_conn_string("checkpoints.db") as saver:
    #     research_assistant.checkpointer = saver
    #     app.state.agent = research_assistant
    #     yield
    # # context manager will clean up the AsyncSqliteSaver on exit
    pass


app = FastAPI(
    title="GenTrade API",
    version="1.0",
    # lifespan=lifespan,
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
    )


@app.middleware("http")
async def check_auth_header(request: Request, call_next: Callable) -> Response:
    if settings.CLERK_JWT_KEY:
        try:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                session = jwt.decode(
                    auth_header.split(" ")[1],
                    key=settings.CLERK_JWT_KEY,
                    algorithms=["RS256"],
                )
                app.state.session = session
        except jwt.exceptions.PyJWTError:
            return Response(status_code=401, content="Missing or invalid token")
        finally:
            return await call_next(request)


async def check_auth_modify_config(config: dict, request: Request) -> dict:
    if app.state.session:
        config["configurable"]["user_id"] = app.state.session["sub"]
        config["configurable"]["thread_id"] = app.state.session["sid"]
        config["configurable"]["run_id"] = str(uuid.uuid4())
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
    per_req_config_modifier=check_auth_modify_config,
)
