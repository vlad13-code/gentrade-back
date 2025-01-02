from pydantic import BaseModel
from datetime import datetime


class StrategySchemaAdd(BaseModel):
    name: str
    file: str
    code: str


class StrategySchema(StrategySchemaAdd):
    id: int
    createdAt: datetime
    updatedAt: datetime
