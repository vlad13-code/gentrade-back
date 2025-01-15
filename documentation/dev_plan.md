# Below is a plan for implementing the backtesting feature

---

## 1. Database & Data Model

### 1.1. SQLAlchemy Model

Create the `BacktestsORM` in `app/db/models/backtests.py`:

```python
from sqlalchemy import String, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from datetime import datetime

from app.db.db import Base
from app.db.models._common import intpk, created_at, updated_at

class BacktestsORM(Base):
    __tablename__ = "backtests"

    id: Mapped[intpk]
    strategy_id: Mapped[int] = mapped_column(ForeignKey("strategies.id", ondelete="CASCADE"))
    file: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    date_range: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), default="running")
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())
```

### 1.2. Alembic Migration

After adding the model above, **generate** a migration with:

```bash
alembic revision --autogenerate -m "create_backtests_table"
```

Then apply it:

```bash
alembic upgrade head
```

This creates a `backtests` table with columns `id`, `strategy_id`, `file`, `date_range`, `status`, `created_at`, and `updated_at`.

### 1.3. Repository: `repo_backtests.py`

```python
from app.db.models.backtests import BacktestsORM
from app.db.utils.repository import SQLAlchemyRepository

class BacktestsRepository(SQLAlchemyRepository):
    model = BacktestsORM
```

This provides the basic CRUD (`add_one`, `find_one`, `delete_one`, etc.) inherited from `SQLAlchemyRepository`.

---

## 2. Backtests Service Layer

Create `app/db/services/service_backtests.py`. This is **analogous** to `service_strategies.py`. It will:

1. **Validate** the user’s permission to backtest a given strategy.
2. **Create** a new `backtests` record with status `"running"`.
3. **Enqueue** a Celery task to run the actual Freqtrade backtest.
4. Optionally **fetch** backtests or update their status.

Example structure:

```python
import logging
from fastapi import HTTPException, status
from typing import Optional

from app.db.utils.unitofwork import IUnitOfWork
from app.db.utils.decorators import require_user
from app.db.models.strategies import StrategiesORM
from app.db.models.users import UsersORM
from app.db.models.backtests import BacktestsORM
from app.tasks.backtests import run_backtest_task

class BacktestsService:
    @require_user
    async def create_backtest(
        self,
        uow: IUnitOfWork,
        user: UsersORM,
        strategy_id: int,
        date_range: str
    ) -> int:
        """
        1. Ensure the strategy belongs to the user
        2. Create a backtest record with status='running'
        3. Enqueue the Celery task to actually run the backtest
        4. Return the new backtest ID
        """
        async with uow:
            strategy: Optional[StrategiesORM] = await uow.strategies.find_one(id=strategy_id)
            if not strategy or strategy.user_id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not your strategy or strategy not found.",
                )

            backtest_data = {
                "strategy_id": strategy_id,
                "date_range": date_range,
                "status": "running",
            }
            backtest_id = await uow.backtests.add_one(backtest_data)
            await uow.commit()

        # Enqueue Celery task (non-async call)
        run_backtest_task.delay(backtest_id, strategy_id, user.clerk_id, date_range)
        return backtest_id

    @require_user
    async def get_backtest(
        self, uow: IUnitOfWork, user: UsersORM, backtest_id: int
    ) -> BacktestsORM:
        """
        Fetch a single backtest by ID, verifying ownership via its strategy
        """
        async with uow:
            backtest: Optional[BacktestsORM] = await uow.backtests.find_one(id=backtest_id)
            if not backtest:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Backtest not found"
                )

            # Check that the user owns the strategy
            strategy = await uow.strategies.find_one(id=backtest.strategy_id)
            if not strategy or strategy.user_id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not your backtest",
                )
            return backtest
```

---

## 3. Celery Task & `ft_backtesting.py`

### 3.1. Celery App

Create or update `app/celery_app.py`:

```python
from celery import Celery

celery_app = Celery(
    "gen_trade",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1"
)
```

**Run** worker in another terminal:

```bash
celery -A app.celery_app.celery_app worker --loglevel=info
```

### 3.2. Task Definition

In a new file `app/tasks/backtests.py`:

```python
from app.celery_app import celery_app
from app.db.db import async_session_maker
from app.db.models.backtests import BacktestsORM
from app.db.models.strategies import StrategiesORM
from app.util.ft_backtesting import run_backtest_in_docker
import asyncio

@celery_app.task
def run_backtest_task(backtest_id: int, strategy_id: int, clerk_id: str, date_range: str):
    """
    Runs in the Celery worker. We do a mini async bridging via asyncio.run(...)
    """
    asyncio.run(_run_backtest(backtest_id, strategy_id, clerk_id, date_range))

async def _run_backtest(backtest_id: int, strategy_id: int, clerk_id: str, date_range: str):
    async with async_session_maker() as session:
        strategy = await session.get(StrategiesORM, strategy_id)
        if not strategy:
            # Can't do anything if strategy is gone
            return

        # 1. Run freqtrade backtest
        try:
            result_file_path = run_backtest_in_docker(
                strategy_file_path=strategy.file,  # or full path
                clerk_id=clerk_id,
                date_range=date_range,
            )

            # 2. Update DB with success
            backtest = await session.get(BacktestsORM, backtest_id)
            if backtest:
                backtest.file = result_file_path
                backtest.status = "finished"
            await session.commit()

        except Exception as e:
            # Mark backtest as failed
            backtest = await session.get(BacktestsORM, backtest_id)
            if backtest:
                backtest.status = "failed"
            await session.commit()
```

### 3.3. `ft_backtesting.py` Utility

```python
# app/util/ft_backtesting.py
from python_on_whales import DockerClient
import os
import uuid
from app.util.ft_userdir import get_user_data_directory

def run_backtest_in_docker(strategy_file_path: str, clerk_id: str, date_range: str) -> str:
    user_dir = get_user_data_directory(clerk_id)
    docker_compose_path = os.path.join(user_dir, "docker-compose.yml")

    docker = DockerClient(
        compose_files=[docker_compose_path],
        client_type="docker",
    )

    output_filename = f"backtest_{uuid.uuid4()}.json"
    docker.compose.run(
        "freqtrade",
        [
            "backtesting",
            "--userdir", "user_data",
            "--strategy", strategy_file_path,
            "--timerange", date_range,
            "--export", "json",
            "--exportfilename", output_filename,
        ],
        remove=True,
    )

    # Construct the full path to the result inside user_data
    return os.path.join(user_dir, "user_data", output_filename)
```

---

## 4. Backtests Router

Finally, create a new router file: `app/routers/v1/router_backtests.py`. Note how we call the **Service** instead of doing DB logic here directly.

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.dependencies import UOWDep, UserAuthDep
from app.db.services.service_backtests import BacktestsService
from app.db.models.backtests import BacktestsORM

router = APIRouter(
    prefix="/backtests",
    tags=["backtests"],
)

class BacktestStartSchema(BaseModel):
    strategy_id: int
    date_range: str

class BacktestCreated(BaseModel):
    backtest_id: int

class BacktestStatusSchema(BaseModel):
    id: int
    strategy_id: int
    date_range: str
    status: str
    file: Optional[str] = None
    created_at: datetime
    updated_at: datetime

@router.post("", response_model=BacktestCreated)
async def create_backtest(
    req: BacktestStartSchema,
    uow: UOWDep,
    user: UserAuthDep
):
    # Offload logic to service
    backtest_id = await BacktestsService().create_backtest(
        uow=uow,
        user=user,  # user is a UsersORM from the @require_user decorator
        strategy_id=req.strategy_id,
        date_range=req.date_range,
    )
    return {"backtest_id": backtest_id}


@router.get("/{backtest_id}", response_model=BacktestStatusSchema)
async def get_backtest(
    backtest_id: int,
    uow: UOWDep,
    user: UserAuthDep
):
    # Use service to retrieve the record
    backtest_orm: BacktestsORM = await BacktestsService().get_backtest(
        uow=uow,
        user=user,
        backtest_id=backtest_id,
    )

    return {
        "id": backtest_orm.id,
        "strategy_id": backtest_orm.strategy_id,
        "date_range": backtest_orm.date_range,
        "status": backtest_orm.status,
        "file": backtest_orm.file,
        "created_at": backtest_orm.created_at,
        "updated_at": backtest_orm.updated_at,
    }
```

---

## 5. Frontend Flow (Polling)

On the **frontend**:

1. **POST** `/backtests` with `{"strategy_id": X, "date_range": "YYYYMMDD-YYYYMMDD"}`
   - Response: `{"backtest_id": 123}`
2. Poll **`GET /backtests/123`** every few seconds:
   - If `status == "running"`, keep polling.
   - If `status == "finished"`, show success.
   - If `status == "failed"`, show error.

---

## 6. Summary of the MVP Flow

1. **User** clicks “Backtest” → picks date range → calls `create_backtest()`.
2. **`BacktestsService.create_backtest()`**
   - Validates user, inserts a row into `backtests`, enqueues Celery task.
3. **Celery** calls `run_backtest_in_docker(...)` → runs Freqtrade in Docker:
   - On success: updates `file` and `status="finished"`.
   - On error: `status="failed"`.
4. **Frontend** polls `GET /backtests/{id}` → reads `status` and `file`.
5. If finished, user can open or parse the JSON results.

**All** logic that touches the DB or Celery is in the **Service** layer or in the **Celery task**. The router is now minimal, consistent with your existing `service_strategies.py` pattern.

---

### Questions / Next Steps

- **Result Parsing**: Do you eventually want to parse the JSON for metrics? If so, you could add a method in the **service** that reads the file and extracts stats into DB columns.
- **Celery Setup**: Make sure your worker container (or host) can talk to Docker.
- **Performance**: If you expect many backtests simultaneously, keep an eye on concurrency.
- **Cleanup**: Decide whether to periodically delete old JSON results.

This approach **mirrors** the style of `service_strategies.py`, ensuring your backtesting logic is easy to maintain and test. If you need more details, just let me know!
