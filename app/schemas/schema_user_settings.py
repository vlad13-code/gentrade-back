from typing import Dict, List, Optional, Union, Literal
from pydantic import BaseModel, Field, model_validator
from app.schemas.schema_freqtrade_config import (
    FreqtradeConfig,
    OrderTypes,
    OrderTimeInForce,
    UnfilledTimeout,
    ExchangeConfig,
    EntryPricing,
    ExitPricing,
    TradingMode,
    MarginMode,
    OrderType,
    TimeInForce,
)


class TradingModeSettings(BaseModel):
    trading_mode: TradingMode = Field(
        default="futures", description="Trading mode: spot, margin, or futures"
    )
    margin_mode: Optional[MarginMode] = Field(
        default="isolated", description="Margin mode for trading: isolated or cross"
    )
    liquidation_buffer: Optional[float] = Field(
        default=0.05, description="Safety buffer for liquidation price"
    )


class PairConfiguration(BaseModel):
    pair_whitelist: List[str] = Field(
        default_factory=list, description="List of pairs to use for trading"
    )
    pair_blacklist: List[str] = Field(
        default_factory=list, description="List of pairs to exclude from trading"
    )
    stake_currency: str = Field(description="Crypto-currency used for trading")


class TradeParameters(BaseModel):
    max_open_trades: int = Field(
        description="Number of open trades your bot is allowed to have"
    )
    stake_amount: Union[float, Literal["unlimited"]] = Field(
        description="Amount of crypto-currency to use for each trade"
    )


class AdvancedTradeParameters(BaseModel):
    available_capital: Optional[float] = Field(
        default=None, description="Available starting capital for the bot"
    )
    tradable_balance_ratio: float = Field(
        default=0.99,
        description="Ratio of the total account balance the bot is allowed to trade",
    )
    position_adjustment_enabled: bool = Field(
        default=False, description="Enable position adjustments"
    )
    minimal_roi: Dict[str, float] = Field(
        default_factory=dict, description="Minimal ROI configuration"
    )


class OrderSettings(BaseModel):
    entry_order_type: OrderType = Field(
        default="limit", description="Order type for entry orders"
    )
    exit_order_type: OrderType = Field(
        default="limit", description="Order type for exit orders"
    )
    stoploss_order_type: OrderType = Field(
        default="market", description="Order type for stoploss orders"
    )
    time_in_force: TimeInForce = Field(
        default="GTC", description="Time in force for orders"
    )
    unfilled_timeout: int = Field(
        default=10, description="How long to wait for orders to fill (in minutes)"
    )


class DisplaySettings(BaseModel):
    fiat_display_currency: str = Field(
        default="USD", description="Fiat currency used to show profits"
    )
    dry_run_enabled: bool = Field(
        default=True,
        description="Define if the bot must be in Dry Run or production mode",
    )


class UserSettingsSchema(BaseModel):
    trading_mode: Optional[TradingModeSettings] = Field(
        default_factory=TradingModeSettings, description="Trading mode settings"
    )
    pair_config: Optional[PairConfiguration] = Field(
        default_factory=PairConfiguration, description="Pair configuration"
    )
    trade_params: Optional[TradeParameters] = Field(
        default_factory=TradeParameters, description="Trade parameters"
    )
    advanced_params: Optional[AdvancedTradeParameters] = Field(
        default_factory=AdvancedTradeParameters,
        description="Advanced trading parameters",
    )
    order_settings: Optional[OrderSettings] = Field(
        default_factory=OrderSettings,
        description="Order type and time in force settings",
    )
    display_settings: Optional[DisplaySettings] = Field(
        default_factory=DisplaySettings, description="Display and simulation settings"
    )

    @classmethod
    def from_freqtrade_config(cls, config: FreqtradeConfig) -> "UserSettingsSchema":
        """Convert FreqtradeConfig to UserSettings."""
        return cls(
            trading_mode=TradingModeSettings(
                trading_mode=config.trading_mode,
                margin_mode=config.margin_mode,
                liquidation_buffer=config.liquidation_buffer,
            ),
            pair_config=PairConfiguration(
                pair_whitelist=config.exchange.pair_whitelist,
                pair_blacklist=config.exchange.pair_blacklist,
                stake_currency=config.stake_currency,
            ),
            trade_params=TradeParameters(
                max_open_trades=config.max_open_trades,
                stake_amount=config.stake_amount,
            ),
            advanced_params=AdvancedTradeParameters(
                available_capital=config.available_capital,
                tradable_balance_ratio=config.tradable_balance_ratio,
                position_adjustment_enabled=config.position_adjustment_enable,
                minimal_roi={},  # Add ROI mapping if needed
            ),
            order_settings=OrderSettings(
                entry_order_type=(
                    config.order_types.entry if config.order_types else "limit"
                ),
                exit_order_type=(
                    config.order_types.exit if config.order_types else "limit"
                ),
                stoploss_order_type=(
                    config.order_types.stoploss if config.order_types else "market"
                ),
                time_in_force=(
                    config.order_time_in_force.entry
                    if config.order_time_in_force
                    else "GTC"
                ),
                unfilled_timeout=(
                    config.unfilledtimeout.entry if config.unfilledtimeout else 10
                ),
            ),
            display_settings=DisplaySettings(
                fiat_display_currency=config.fiat_display_currency,
                dry_run_enabled=config.dry_run,
            ),
        )

    def to_freqtrade_config(self) -> FreqtradeConfig:
        """Convert UserSettings to FreqtradeConfig."""
        # Create order types configuration
        order_types = OrderTypes(
            entry=(
                self.order_settings.entry_order_type if self.order_settings else "limit"
            ),
            exit=(
                self.order_settings.exit_order_type if self.order_settings else "limit"
            ),
            emergency_exit="market",
            force_entry="market",
            force_exit="market",
            stoploss=(
                self.order_settings.stoploss_order_type
                if self.order_settings
                else "market"
            ),
            stoploss_on_exchange=False,
        )

        # Create order time in force configuration
        order_time_in_force = OrderTimeInForce(
            entry=self.order_settings.time_in_force if self.order_settings else "GTC",
            exit=self.order_settings.time_in_force if self.order_settings else "GTC",
        )

        # Create unfilled timeout configuration
        unfilled_timeout = UnfilledTimeout(
            entry=self.order_settings.unfilled_timeout if self.order_settings else 10,
            exit=self.order_settings.unfilled_timeout if self.order_settings else 10,
            unit="minutes",
            exit_timeout_count=0,
        )

        # Create exchange configuration
        exchange_config = ExchangeConfig(
            name="binance",
            pair_whitelist=self.pair_config.pair_whitelist if self.pair_config else [],
            pair_blacklist=self.pair_config.pair_blacklist if self.pair_config else [],
        )

        return FreqtradeConfig(
            # Trading mode settings
            trading_mode=(
                self.trading_mode.trading_mode if self.trading_mode else "futures"
            ),
            margin_mode=(
                self.trading_mode.margin_mode if self.trading_mode else "isolated"
            ),
            liquidation_buffer=(
                self.trading_mode.liquidation_buffer if self.trading_mode else 0.05
            ),
            # Pair configuration
            stake_currency=(
                self.pair_config.stake_currency if self.pair_config else "USDT"
            ),
            exchange=exchange_config,
            # Trade parameters
            max_open_trades=(
                self.trade_params.max_open_trades if self.trade_params else 1
            ),
            stake_amount=self.trade_params.stake_amount if self.trade_params else 100.0,
            # Advanced parameters
            available_capital=(
                self.advanced_params.available_capital if self.advanced_params else None
            ),
            tradable_balance_ratio=(
                self.advanced_params.tradable_balance_ratio
                if self.advanced_params
                else 0.99
            ),
            position_adjustment_enable=(
                self.advanced_params.position_adjustment_enabled
                if self.advanced_params
                else False
            ),
            # Order settings
            order_types=order_types,
            order_time_in_force=order_time_in_force,
            unfilledtimeout=unfilled_timeout,
            # Display settings
            dry_run=(
                self.display_settings.dry_run_enabled if self.display_settings else True
            ),
            fiat_display_currency=(
                self.display_settings.fiat_display_currency
                if self.display_settings
                else "USD"
            ),
            # Default values for required fields
            entry_pricing=EntryPricing(),
            exit_pricing=ExitPricing(),
        )

    @model_validator(mode="before")
    @classmethod
    def validate_defaults(cls, values: Dict) -> Dict:
        """Ensure all nested models have default values if not provided."""
        if not values.get("trading_mode"):
            values["trading_mode"] = TradingModeSettings()
        if not values.get("pair_config"):
            values["pair_config"] = PairConfiguration(stake_currency="USDT")
        if not values.get("trade_params"):
            values["trade_params"] = TradeParameters(
                max_open_trades=1, stake_amount=100.0
            )
        if not values.get("advanced_params"):
            values["advanced_params"] = AdvancedTradeParameters()
        if not values.get("order_settings"):
            values["order_settings"] = OrderSettings()
        if not values.get("display_settings"):
            values["display_settings"] = DisplaySettings()
        return values

    class Config:
        json_schema_extra = {
            "example": {
                "trading_mode": {
                    "trading_mode": "futures",
                    "margin_mode": "isolated",
                    "liquidation_buffer": 0.05,
                },
                "pair_config": {
                    "pair_whitelist": ["BTC/USDT:USDT"],
                    "pair_blacklist": [],
                    "stake_currency": "USDT",
                },
                "trade_params": {"max_open_trades": 3, "stake_amount": 100},
                "advanced_params": {
                    "available_capital": 1000,
                    "tradable_balance_ratio": 0.99,
                    "position_adjustment_enabled": False,
                    "minimal_roi": {"0": 0.05, "30": 0.025, "60": 0.01},
                },
                "order_settings": {
                    "entry_order_type": "limit",
                    "exit_order_type": "limit",
                    "stoploss_order_type": "market",
                    "time_in_force": "GTC",
                    "unfilled_timeout": 10,
                },
                "display_settings": {
                    "fiat_display_currency": "USD",
                    "dry_run_enabled": True,
                },
            }
        }
