from typing import Dict, List, Optional, Union, Literal
from pydantic import BaseModel, Field, HttpUrl


class UnfilledTimeout(BaseModel):
    entry: int = Field(description="How long to wait for entry orders to fill")
    exit: int = Field(description="How long to wait for exit orders to fill")
    exit_timeout_count: int = Field(
        default=0, description="Max number of exit timeouts"
    )
    unit: str = Field(default="minutes", description="Time unit for timeout")


class EntryPricingDepthOfMarket(BaseModel):
    enabled: bool = Field(default=False)
    bids_to_ask_delta: float = Field(default=1)


class EntryPricing(BaseModel):
    price_side: str = Field(default="same")
    use_order_book: bool = Field(default=True)
    order_book_top: int = Field(default=1)
    price_last_balance: float = Field(default=0.0)
    check_depth_of_market: EntryPricingDepthOfMarket = Field(
        default_factory=EntryPricingDepthOfMarket
    )


class ExitPricing(BaseModel):
    price_side: str = Field(default="same")
    use_order_book: bool = Field(default=True)
    order_book_top: int = Field(default=1)


class ExchangeConfig(BaseModel):
    name: str
    key: str = Field(default="")
    secret: str = Field(default="")
    ccxt_config: Dict = Field(default_factory=dict)
    ccxt_async_config: Dict = Field(default_factory=dict)
    pair_whitelist: List[str] = Field(default_factory=list)
    pair_blacklist: List[str] = Field(default_factory=list)


class PairlistConfig(BaseModel):
    method: str
    number_assets: Optional[int] = None
    sort_key: Optional[str] = None
    min_value: Optional[float] = None
    refresh_period: Optional[int] = None


class TelegramConfig(BaseModel):
    enabled: bool = Field(default=False)
    token: str = Field(default="")
    chat_id: str = Field(default="")


class ApiServerConfig(BaseModel):
    enabled: bool = Field(default=True)
    listen_ip_address: str = Field(default="0.0.0.0")
    listen_port: int = Field(default=8080)
    verbosity: str = Field(default="error")
    enable_openapi: bool = Field(default=False)
    jwt_secret_key: str
    ws_token: str
    CORS_origins: List[str] = Field(default_factory=list)
    username: str
    password: str = Field(default="")


class InternalsConfig(BaseModel):
    process_throttle_secs: int = Field(default=5)


class FreqtradeConfig(BaseModel):
    max_open_trades: int = Field(default=3)
    stake_currency: str = Field(default="USDT")
    stake_amount: Union[float, str] = Field(default=1000)
    tradable_balance_ratio: float = Field(default=0.99)
    fiat_display_currency: str = Field(default="USD")
    dry_run: bool = Field(default=True)
    dry_run_wallet: Union[float, Dict[str, float]] = Field(default=1000)
    cancel_open_orders_on_exit: bool = Field(default=False)
    trading_mode: Literal["spot", "margin", "futures"] = Field(default="futures")
    margin_mode: Optional[Literal["isolated", "cross"]] = Field(default="isolated")
    unfilledtimeout: UnfilledTimeout = Field(default_factory=UnfilledTimeout)
    entry_pricing: EntryPricing = Field(default_factory=EntryPricing)
    exit_pricing: ExitPricing = Field(default_factory=ExitPricing)
    exchange: ExchangeConfig
    pairlists: List[PairlistConfig] = Field(default_factory=list)
    telegram: TelegramConfig = Field(default_factory=TelegramConfig)
    api_server: ApiServerConfig
    bot_name: str = Field(default="freqtrade")
    initial_state: Literal["running", "stopped"] = Field(default="running")
    force_entry_enable: bool = Field(default=False)
    internals: InternalsConfig = Field(default_factory=InternalsConfig)
