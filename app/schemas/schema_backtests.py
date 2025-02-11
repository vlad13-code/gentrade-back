from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any


class BacktestStartSchema(BaseModel):
    strategy_id: int
    date_range: str  # Format: "YYYYMMDD-YYYYMMDD"


class BacktestCreated(BaseModel):
    backtest_id: int


class BacktestSchemaAdd(BaseModel):
    strategy_id: int
    date_range: str
    status: str
    results: Optional[Dict[str, Any]] = None


class BacktestSchema(BacktestSchemaAdd):
    id: int
    created_at: datetime
    updated_at: datetime
