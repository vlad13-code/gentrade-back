from abc import ABC, abstractmethod
from typing import Type

# pylint: disable=import-error

from app.db.db import async_session_maker
from app.db.repositories.langgraph.repo_langgraph_checkpoint_write import (
    CheckpointWriteRepository,
)
from app.db.repositories.langgraph.repo_langgraph_checkpoint_blob import (
    CheckpointBlobRepository,
)
from app.db.repositories.langgraph.repo_langgraph_checkpoint import CheckpointRepository
from app.db.repositories.repo_chats import ChatsRepository
from app.db.repositories.repo_strategies import StrategiesRepository
from app.db.repositories.repo_users import UsersRepository
from app.db.repositories.repo_backtests import BacktestsRepository


# https://github1s.com/cosmicpython/code/tree/chapter_06_uow
class IUnitOfWork(ABC):
    chats: Type[ChatsRepository]
    users: Type[UsersRepository]
    strategies: Type[StrategiesRepository]
    backtests: Type[BacktestsRepository]
    checkpoint_write: Type[CheckpointWriteRepository]
    checkpoint_blob: Type[CheckpointBlobRepository]
    checkpoint: Type[CheckpointRepository]

    @abstractmethod
    def __init__(self): ...

    @abstractmethod
    async def __aenter__(self): ...

    @abstractmethod
    async def __aexit__(self, *args): ...

    @abstractmethod
    async def commit(self): ...

    @abstractmethod
    async def rollback(self): ...


class UnitOfWork:
    def __init__(self):
        self.session_factory = async_session_maker
        self.session = None

    async def __aenter__(self):
        if not self.session:
            self.session = self.session_factory()

        self.users = UsersRepository(self.session)
        self.strategies = StrategiesRepository(self.session)
        self.chats = ChatsRepository(self.session)
        self.checkpoint_write = CheckpointWriteRepository(self.session)
        self.checkpoint_blob = CheckpointBlobRepository(self.session)
        self.checkpoint = CheckpointRepository(self.session)

    async def __aexit__(self, *args):
        await self.rollback()
        await self.session.close()

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()
