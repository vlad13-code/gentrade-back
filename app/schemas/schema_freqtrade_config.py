from typing import Dict, List, Optional, Union, Literal
from pydantic import BaseModel, Field

TradingMode = Literal["spot", "margin", "futures"]
MarginMode = Literal["isolated", "cross"]
OrderType = Literal["limit", "market"]
TimeInForce = Literal["GTC", "FOK", "IOC"]
PriceSide = Literal["ask", "bid", "same", "other"]


class CoingeckoConfig(BaseModel):
    api_key: Optional[str] = Field(
        default=None, description="Coingecko API key for rate limit handling"
    )
    is_demo: bool = Field(
        default=True, description="Whether to use demo or pro API key"
    )


class UnfilledTimeout(BaseModel):
    entry: int = Field(description="How long to wait for entry orders to fill")
    exit: int = Field(description="How long to wait for exit orders to fill")
    exit_timeout_count: int = Field(
        default=0, description="Max number of exit timeouts"
    )
    unit: str = Field(default="minutes", description="Time unit for timeout")


class EntryPricingDepthOfMarket(BaseModel):
    enabled: bool = Field(default=False, description="Enable checking depth of market")
    bids_to_ask_delta: float = Field(
        default=1,
        description="The difference ratio of buy orders and sell orders found in Order Book",
    )


class EntryPricing(BaseModel):
    price_side: PriceSide = Field(
        default="same", description="Select the side of the spread to use for entry"
    )
    use_order_book: bool = Field(
        default=True, description="Enable entering using the rates in Order Book"
    )
    order_book_top: int = Field(
        default=1,
        description="Bot will use the top N rate in Order Book to enter a trade",
    )
    price_last_balance: float = Field(
        default=0.0, description="Interpolate the bidding price"
    )
    check_depth_of_market: EntryPricingDepthOfMarket = Field(
        default_factory=EntryPricingDepthOfMarket,
        description="Settings for checking depth of market",
    )


class ExitPricing(BaseModel):
    price_side: PriceSide = Field(
        default="same", description="Select the side of the spread to use for exit"
    )
    use_order_book: bool = Field(
        default=True, description="Enable exiting using the rates in Order Book"
    )
    order_book_top: int = Field(
        default=1, description="Bot will use the top N rate in Order Book to exit"
    )


class OrderTypes(BaseModel):
    entry: OrderType = Field(default="limit", description="Order type for entry orders")
    exit: OrderType = Field(default="limit", description="Order type for exit orders")
    emergency_exit: OrderType = Field(
        default="market", description="Order type for emergency exit orders"
    )
    force_entry: OrderType = Field(
        default="market", description="Order type for force entry orders"
    )
    force_exit: OrderType = Field(
        default="market", description="Order type for force exit orders"
    )
    stoploss: OrderType = Field(
        default="market", description="Order type for stoploss orders"
    )
    stoploss_on_exchange: bool = Field(
        default=False, description="Enable stoploss on exchange"
    )
    stoploss_on_exchange_interval: int = Field(
        default=60, description="Interval in seconds for stoploss on exchange"
    )
    stoploss_on_exchange_limit_ratio: float = Field(
        default=0.99, description="Limit ratio for stoploss on exchange"
    )


class OrderTimeInForce(BaseModel):
    entry: TimeInForce = Field(
        default="GTC", description="Time in force for entry orders"
    )
    exit: TimeInForce = Field(
        default="GTC", description="Time in force for exit orders"
    )


class ExchangeConfig(BaseModel):
    name: str = Field(description="Name of the exchange class to use")
    key: str = Field(default="", description="API key to use for the exchange")
    secret: str = Field(default="", description="API secret to use for the exchange")
    password: Optional[str] = Field(
        default=None, description="API password for exchanges that use password"
    )
    uid: Optional[str] = Field(
        default=None, description="API uid for exchanges that use uid"
    )
    ccxt_config: Dict = Field(
        default_factory=dict,
        description="Additional CCXT parameters passed to both ccxt instances",
    )
    ccxt_async_config: Dict = Field(
        default_factory=dict,
        description="Additional CCXT parameters passed to async ccxt instance",
    )
    ccxt_sync_config: Dict = Field(
        default_factory=dict,
        description="Additional CCXT parameters passed to sync ccxt instance",
    )
    pair_whitelist: List[str] = Field(
        default_factory=list, description="List of pairs to use for trading"
    )
    pair_blacklist: List[str] = Field(
        default_factory=list, description="List of pairs to exclude from trading"
    )
    enable_ws: bool = Field(default=False, description="Enable the usage of Websockets")
    markets_refresh_interval: int = Field(
        default=60, description="The interval in minutes in which markets are reloaded"
    )
    skip_open_order_update: bool = Field(
        default=False, description="Skip open order updates on startup"
    )
    unknown_fee_rate: Optional[float] = Field(
        default=None, description="Fallback value for calculating trading fees"
    )
    log_responses: bool = Field(
        default=False, description="Log relevant exchange responses"
    )
    only_from_ccxt: bool = Field(
        default=False, description="Prevent data-download from data.binance.vision"
    )


class PairlistConfig(BaseModel):
    method: str = Field(
        default="StaticPairList", description="Name of the pairlist method to use"
    )
    number_assets: Optional[int] = Field(
        default=None, description="Number of pairs to keep in whitelist"
    )
    sort_key: Optional[str] = Field(
        default=None, description="Key to use for sorting pairs"
    )
    min_value: Optional[float] = Field(
        default=None, description="Minimum value for filtering pairs"
    )
    refresh_period: Optional[int] = Field(
        default=None, description="Refresh period in seconds"
    )


class TelegramNotificationSettings(BaseModel):
    status: bool = Field(default=True, description="Send status notifications")
    warning: bool = Field(default=True, description="Send warning notifications")
    startup: bool = Field(default=True, description="Send startup notifications")
    entry: bool = Field(default=True, description="Send entry notifications")
    entry_fill: bool = Field(default=True, description="Send entry fill notifications")
    entry_cancel: bool = Field(
        default=True, description="Send entry cancellation notifications"
    )
    exit: bool = Field(default=True, description="Send exit notifications")
    exit_fill: bool = Field(default=True, description="Send exit fill notifications")
    exit_cancel: bool = Field(
        default=True, description="Send exit cancellation notifications"
    )


class TelegramConfig(BaseModel):
    enabled: bool = Field(default=False, description="Enable the usage of Telegram")
    token: str = Field(default="", description="Your Telegram bot token")
    chat_id: str = Field(default="", description="Your personal Telegram account id")
    balance_dust_level: float = Field(
        default=0.0, description="Dust-level for balance command"
    )
    reload: bool = Field(
        default=True, description="Allow reload buttons on telegram messages"
    )
    notification_settings: TelegramNotificationSettings = Field(
        default_factory=TelegramNotificationSettings,
        description="Detailed notification settings",
    )
    allow_custom_messages: bool = Field(
        default=False, description="Enable sending custom messages from strategies"
    )


class WebhookConfig(BaseModel):
    enabled: bool = Field(
        default=False, description="Enable usage of Webhook notifications"
    )
    url: Optional[str] = Field(default=None, description="URL for the webhook")
    entry: Optional[str] = Field(default=None, description="Payload to send on entry")
    entry_cancel: Optional[str] = Field(
        default=None, description="Payload to send on entry order cancel"
    )
    entry_fill: Optional[str] = Field(
        default=None, description="Payload to send on entry order filled"
    )
    exit: Optional[str] = Field(default=None, description="Payload to send on exit")
    exit_cancel: Optional[str] = Field(
        default=None, description="Payload to send on exit order cancel"
    )
    exit_fill: Optional[str] = Field(
        default=None, description="Payload to send on exit order filled"
    )
    status: Optional[str] = Field(
        default=None, description="Payload to send on status calls"
    )
    allow_custom_messages: bool = Field(
        default=False, description="Enable sending custom messages from strategies"
    )


class ApiServerConfig(BaseModel):
    enabled: bool = Field(default=False, description="Enable usage of API Server")
    listen_ip_address: str = Field(default="0.0.0.0", description="Bind IP address")
    listen_port: int = Field(default=8080, description="Bind Port")
    verbosity: Literal["info", "error"] = Field(
        default="error", description="Logging verbosity"
    )
    enable_openapi: bool = Field(
        default=False, description="Enable OpenAPI documentation"
    )
    jwt_secret_key: Optional[str] = Field(
        default="", description="Secret key for JWT tokens"
    )
    ws_token: Optional[str] = Field(
        default="", description="API token for the Message WebSocket"
    )
    CORS_origins: Optional[List[str]] = Field(
        default_factory=list, description="List of allowed CORS origins"
    )
    username: Optional[str] = Field(default="", description="Username for API server")
    password: Optional[str] = Field(default="", description="Password for API server")


class ExternalMessageConsumer(BaseModel):
    enabled: bool = Field(default=False, description="Enable Producer/Consumer mode")
    producer_url: Optional[str] = Field(default=None, description="URL of the producer")
    producer_ws_token: Optional[str] = Field(
        default=None, description="WebSocket token for producer"
    )


class InternalsConfig(BaseModel):
    process_throttle_secs: int = Field(
        default=5, description="Set the process throttle in seconds"
    )
    heartbeat_interval: int = Field(
        default=60, description="Print heartbeat message every N seconds"
    )
    sd_notify: bool = Field(default=False, description="Enable sd_notify protocol")


class FreqtradeConfig(BaseModel):
    # Required fields
    max_open_trades: int = Field(
        description="Number of open trades your bot is allowed to have"
    )
    stake_currency: str = Field(description="Crypto-currency used for trading")
    stake_amount: Union[float, str] = Field(
        description="Amount of crypto-currency to use for each trade"
    )
    dry_run: bool = Field(
        description="Define if the bot must be in Dry Run or production mode"
    )
    exchange: ExchangeConfig = Field(description="Exchange configuration")
    strategy: Optional[str] = Field(
        default="", description="Defines Strategy class to use"
    )

    # Optional fields with defaults from config.json
    tradable_balance_ratio: float = Field(
        default=0.99,
        description="Ratio of the total account balance the bot is allowed to trade",
    )
    available_capital: Optional[float] = Field(
        default=None, description="Available starting capital for the bot"
    )
    amend_last_stake_amount: Optional[bool] = Field(
        default=False, description="Use reduced last stake amount if necessary"
    )
    last_stake_amount_min_ratio: Optional[float] = Field(
        default=0.5, description="Minimum ratio for last stake amount"
    )
    amount_reserve_percent: Optional[float] = Field(
        default=0.05, description="Reserve some amount in min pair stake amount"
    )
    fiat_display_currency: str = Field(
        default="USD", description="Fiat currency used to show profits"
    )
    dry_run_wallet: Union[float, Dict[str, float]] = Field(
        default=1000.0, description="Starting balance for dry run"
    )
    cancel_open_orders_on_exit: bool = Field(
        default=False, description="Cancel open orders on bot stop"
    )
    trading_mode: TradingMode = Field(default="futures", description="Trading mode")
    margin_mode: Optional[MarginMode] = Field(
        default="isolated", description="Margin mode for trading"
    )
    liquidation_buffer: Optional[float] = Field(
        default=0.05, description="Safety buffer for liquidation price"
    )
    unfilledtimeout: UnfilledTimeout = Field(
        default_factory=UnfilledTimeout, description="Unfilled order timeout settings"
    )
    entry_pricing: EntryPricing = Field(
        default_factory=EntryPricing, description="Entry pricing settings"
    )
    exit_pricing: ExitPricing = Field(
        default_factory=ExitPricing, description="Exit pricing settings"
    )
    custom_price_max_distance_ratio: Optional[float] = Field(
        default=0.02,
        description="Maximum distance ratio between current and custom price",
    )
    use_exit_signal: Optional[bool] = Field(
        default=True, description="Use exit signals from strategy"
    )
    exit_profit_only: Optional[bool] = Field(
        default=False, description="Only exit on profit"
    )
    exit_profit_offset: Optional[float] = Field(
        default=0.0, description="Profit offset for exit signal"
    )
    ignore_roi_if_entry_signal: Optional[bool] = Field(
        default=False, description="Ignore ROI if entry signal is still active"
    )
    ignore_buying_expired_candle_after: Optional[int] = Field(
        default=None, description="Ignore buying on expired candles"
    )
    order_types: Optional[OrderTypes] = Field(
        default_factory=OrderTypes, description="Order type configurations"
    )
    order_time_in_force: Optional[OrderTimeInForce] = Field(
        default_factory=OrderTimeInForce, description="Order time in force settings"
    )
    position_adjustment_enable: Optional[bool] = Field(
        default=False, description="Enable position adjustments"
    )
    max_entry_position_adjustment: Optional[int] = Field(
        default=-1, description="Maximum position adjustments"
    )
    pairlists: List[PairlistConfig] = Field(
        default_factory=list, description="Pairlist configurations"
    )
    webhook: Optional[WebhookConfig] = Field(
        default_factory=WebhookConfig, description="Webhook configuration"
    )
    api_server: Optional[ApiServerConfig] = Field(
        default_factory=ApiServerConfig, description="API server configuration"
    )
    bot_name: str = Field(default="freqtrade", description="Name of the bot")
    initial_state: Literal["running", "stopped"] = Field(
        default="running", description="Initial bot state"
    )
    force_entry_enable: bool = Field(
        default=False, description="Enable force entry commands"
    )
    internals: InternalsConfig = Field(
        default_factory=InternalsConfig, description="Internal configurations"
    )
    db_url: Optional[str] = Field(default=None, description="Database URL to use")
    logfile: Optional[str] = Field(default=None, description="Logfile name")
    strategy_path: Optional[str] = Field(
        default=None, description="Additional strategy lookup path"
    )
    recursive_strategy_search: Optional[bool] = Field(
        default=False, description="Recursively search for strategies"
    )
    user_data_dir: Optional[str] = Field(
        default="./user_data/", description="Directory containing user data"
    )
    dataformat_ohlcv: Optional[str] = Field(
        default="feather", description="Data format for OHLCV data"
    )
    dataformat_trades: Optional[str] = Field(
        default="feather", description="Data format for trades data"
    )
    reduce_df_footprint: Optional[bool] = Field(
        default=False, description="Reduce dataframe memory usage"
    )
    add_config_files: Optional[List[str]] = Field(
        default_factory=list, description="Additional config files to load"
    )
