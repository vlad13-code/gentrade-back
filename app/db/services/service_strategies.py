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
from app.util.ft.ft_strategies import FTStrategies
from app.util.ft.ft_userdir import FTUserDir
from app.db.utils.chat_message_utils import ChatMessageUtils
from app.util.logger import setup_logger, set_strategy_id

logger = setup_logger("services.strategies")


class StrategiesService:

    @require_user
    async def delete_strategy(self, uow: IUnitOfWork, id: int, user: UsersORM) -> bool:
        logger.info(
            f"Deleting strategy {id}",
            extra={
                "data": {
                    "strategy_id": id,
                }
            },
        )
        async with uow:
            strategy: StrategiesORM = await uow.strategies.find_one(id=id)
            if not strategy or strategy.user_id != user.id:
                logger.warning(
                    f"Strategy {id} not found or access denied",
                    extra={
                        "data": {
                            "strategy_id": id,
                            "found": strategy is not None,
                            "user_match": (
                                strategy.user_id == user.id if strategy else False
                            ),
                        }
                    },
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found"
                )

            # Delete strategy file
            try:
                ft_strategies = FTStrategies(str(user.clerk_id))
                ft_strategies.delete_strategy(strategy.file)
                logger.info(
                    f"Strategy file {strategy.file} deleted",
                    extra={"data": {"strategy_id": id, "file": strategy.file}},
                )
            except FileNotFoundError:
                logger.warning(
                    f"Strategy file {strategy.file} already deleted",
                    extra={"data": {"strategy_id": id, "file": strategy.file}},
                )
            except Exception as e:
                logger.error(
                    "Error deleting strategy file",
                    extra={
                        "data": {
                            "strategy_id": id,
                            "file": strategy.file,
                            "error": str(e),
                            "error_type": type(e).__name__,
                        }
                    },
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to delete strategy file",
                ) from e

            # Remove strategyId from messages in chats
            try:
                chat: ChatsORM = await uow.chats.find_one(id=strategy.chat_id)
                if chat and chat.messages:
                    chat.messages = [
                        ChatMessageUtils.remove_strategy_id_from_message(message, id)
                        for message in chat.messages
                    ]
                await uow.chats.edit_one(chat.id, {"messages": chat.messages})
                logger.info(
                    "Strategy ID removed from chat messages",
                    extra={"data": {"strategy_id": id, "chat_id": chat.id}},
                )
            except Exception as e:
                logger.warning(
                    "Failed to update chat messages, chat may be deleted",
                    extra={
                        "data": {
                            "strategy_id": id,
                            "chat_id": strategy.chat_id,
                            "error": str(e),
                        }
                    },
                )

            await uow.strategies.delete_one(id)
            await uow.commit()
            logger.info(
                f"Strategy {id} deleted successfully",
                extra={"data": {"strategy_id": id}},
            )
            return True

    @require_user
    async def get_user_strategies(
        self, uow: IUnitOfWork, user: UsersORM
    ) -> list[StrategySchema]:
        logger.info("Fetching user strategies", extra={"data": {"user_id": user.id}})
        async with uow:
            strategies = await uow.strategies.find_all_by(user_id=user.id)
            logger.info(
                f"Found {len(strategies)} strategies",
                extra={
                    "data": {
                        "count": len(strategies),
                        "strategy_ids": [s.id for s in strategies],
                    }
                },
            )
            return [
                StrategySchema.model_validate(strategy, from_attributes=True)
                for strategy in strategies
            ]

    @require_user
    async def get_strategy(
        self, uow: IUnitOfWork, id: int, user: UsersORM
    ) -> StrategySchema:
        logger.info(f"Fetching strategy {id}", extra={"data": {"strategy_id": id}})
        async with uow:
            strategy: StrategiesORM = await uow.strategies.find_one(id=id)
            if not strategy or strategy.user_id != user.id:
                logger.warning(
                    f"Strategy {id} not found or access denied",
                    extra={
                        "data": {
                            "strategy_id": id,
                            "found": strategy is not None,
                            "user_match": (
                                strategy.user_id == user.id if strategy else False
                            ),
                        }
                    },
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found"
                )

            # Set strategy ID in logging context
            set_strategy_id(strategy.id)

            logger.info(
                f"Strategy {id} retrieved successfully",
                extra={"data": {"strategy_id": id, "name": strategy.name}},
            )
            return StrategySchema.model_validate(strategy, from_attributes=True)

    @require_user
    async def add_strategy(
        self, uow: IUnitOfWork, strategy_draft: StrategyDraftSchemaAdd, user: UsersORM
    ) -> StrategySchema:
        logger.info(
            "Creating new strategy",
            extra={
                "data": {
                    "strategy_name": strategy_draft.name,
                    "chat_id": strategy_draft.chat_id,
                }
            },
        )
        async with uow:
            # Generate strategy code using LLM
            logger.info("Generating strategy code using LLM")
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
                logger.error(
                    "Strategy code generation failed",
                    extra={"data": {"result": result}},
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Strategy code not found",
                )

            try:
                # Initialize user's FreqTrade directory if it doesn't exist
                ft_userdir = FTUserDir(str(user.clerk_id))
                if not ft_userdir.exists():
                    logger.info("Initializing FreqTrade user directory")
                    ft_userdir.initialize()

                # Write strategy file
                ft_strategies = FTStrategies(str(user.clerk_id))
                strategy_file = ft_strategies.write_strategy(
                    strategy_code, strategy_draft.name
                )
                logger.info(
                    "Strategy file written successfully",
                    extra={"data": {"file": strategy_file}},
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

                # Set strategy ID in logging context
                set_strategy_id(strategy.id)

                logger.info(
                    "Strategy created in database",
                    extra={"data": {"strategy_id": strategy.id, "name": strategy.name}},
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
                logger.info(
                    "Strategy ID added to chat messages",
                    extra={"data": {"strategy_id": strategy.id, "chat_id": chat.id}},
                )

                await uow.commit()
                logger.info(
                    "Strategy creation completed successfully",
                    extra={"data": {"strategy_id": strategy.id, "name": strategy.name}},
                )
                return StrategySchema.model_validate(strategy, from_attributes=True)

            except Exception as e:
                logger.error(
                    "Error creating strategy",
                    extra={
                        "data": {
                            "error": str(e),
                            "error_type": type(e).__name__,
                            "strategy_name": strategy_draft.name,
                        }
                    },
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create strategy",
                ) from e
