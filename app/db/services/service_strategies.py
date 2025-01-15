from fastapi import HTTPException, status
from app.db.models.chats import ChatsORM
from app.db.utils.unitofwork import IUnitOfWork
from app.db.models.strategies import StrategiesORM
from app.db.models.users import UsersORM
from app.db.utils.decorators import require_user
from app.agents.strategy.graph_strategy_code import graph_strategy_code
from app.schemas.schema_strategies import (
    StrategySchema,
    StrategyDraftSchemaAdd,
    StrategySchemaAdd,
)
from app.util.ft_userdir import init_ft_userdir
from app.util.ft_strategies import write_strategy_file
from app.db.utils.chat_message_utils import ChatMessageUtils


class StrategiesService:

    @require_user
    async def delete_strategy(self, uow: IUnitOfWork, id: int, user: UsersORM) -> bool:
        async with uow:
            strategy: StrategiesORM = await uow.strategies.find_one(id=id)
            if not strategy or strategy.user_id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found"
                )

            # Remove strategyId from messages in chats so frontend properly displays the strategy draft tool
            try:
                chat: ChatsORM = await uow.chats.find_one(id=strategy.chat_id)
                if chat and chat.messages:
                    chat.messages = [
                        ChatMessageUtils.remove_strategy_id_from_message(message, id)
                        for message in chat.messages
                    ]
                await uow.chats.edit_one(chat.id, {"messages": chat.messages})
            except Exception:
                # Chat already deleted
                return False

            await uow.strategies.delete_one(id)
            await uow.commit()
            return True

    @require_user
    async def get_user_strategies(
        self, uow: IUnitOfWork, user: UsersORM
    ) -> list[StrategySchema]:
        async with uow:
            strategies = await uow.strategies.find_all_by(user_id=user.id)
            return [
                StrategySchema.model_validate(strategy, from_attributes=True)
                for strategy in strategies
            ]

    @require_user
    async def get_strategy(
        self, uow: IUnitOfWork, id: int, user: UsersORM
    ) -> StrategySchema:
        async with uow:
            strategy: StrategiesORM = await uow.strategies.find_one(id=id)
            if not strategy or strategy.user_id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found"
                )
            return StrategySchema.model_validate(strategy, from_attributes=True)

    @require_user
    async def add_strategy(
        self, uow: IUnitOfWork, strategy_draft: StrategyDraftSchemaAdd, user: UsersORM
    ) -> StrategySchema:
        async with uow:
            # Generate strategy code using LLM
            result = await graph_strategy_code.ainvoke(
                {
                    "strategy_draft": strategy_draft,
                }
            )

            strategy_code = (
                result["strategy_code"].code
                if "strategy_code" in result
                and hasattr(result["strategy_code"], "code")
                else None
            )
            if not strategy_code:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Strategy code not found",
                )

            # Initialize user's FreqTrade directory if it doesn't exist
            init_ft_userdir(str(user.clerk_id))

            strategy_file = write_strategy_file(
                strategy_code, str(user.clerk_id), strategy_draft.name
            )

            new_strategy = StrategySchemaAdd(
                name=strategy_draft.name,
                code=strategy_code,
                file=strategy_file,
                user_id=user.id,
                draft=strategy_draft.model_dump(),
                chat_id=strategy_draft.chat_id,
            )
            strategy: StrategiesORM = await uow.strategies.add_one(
                new_strategy.model_dump()
            )

            chat: ChatsORM = await uow.chats.find_one(id=strategy.chat_id)
            if chat and chat.messages:
                chat.messages = [
                    ChatMessageUtils.add_strategy_id_to_message(
                        message, strategy_draft.tool_call_id, strategy.id
                    )
                    for message in chat.messages
                ]
            await uow.chats.edit_one(chat.id, {"messages": chat.messages})

            await uow.commit()
            return StrategySchema.model_validate(strategy, from_attributes=True)
