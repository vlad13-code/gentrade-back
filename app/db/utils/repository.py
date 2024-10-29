from abc import ABC, abstractmethod

from sqlalchemy import insert, select, update, asc, desc
from sqlalchemy.ext.asyncio import AsyncSession


class AbstractRepository(ABC):
    @abstractmethod
    async def add_one():
        raise NotImplementedError

    @abstractmethod
    async def find_all():
        raise NotImplementedError


class SQLAlchemyRepository(AbstractRepository):
    model = None

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_one(self, data: dict) -> int:
        stmt = insert(self.model).values(**data).returning(self.model.id)
        res = await self.session.execute(stmt)
        return res.scalar_one()

    async def edit_one(self, id: int, data: dict) -> int:
        stmt = (
            update(self.model).values(**data).filter_by(id=id).returning(self.model.id)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one()

    async def find_all(self):
        stmt = select(self.model)
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def find_all_by(self, **filter_by):
        stmt = select(self.model).filter_by(**filter_by)
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def find_one(self, **filter_by):
        stmt = select(self.model).filter_by(**filter_by)
        res = await self.session.execute(stmt)
        res = res.scalar_one()
        return res

    async def find_all_by_ordered(self, order_by, order_direction="asc", **filter_by):
        if order_direction == "asc":
            order_clause = asc(order_by)
        else:
            order_clause = desc(order_by)

        stmt = select(self.model).filter_by(**filter_by).order_by(order_clause)
        res = await self.session.execute(stmt)
        return res.scalars().all()
