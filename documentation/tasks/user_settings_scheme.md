All of the user settings are mapped to corresponding `config.json` params specified in brackets(i.e `trading_mode`).

### Basic View

1. **Trading Mode Settings**

   - **Trading Mode (Spot/Futures)** (`trading_mode`)
     - Specifies if you want to trade regularly (spot) or with leverage (futures)
     - Default: "spot"
   - **Margin Mode** (`margin_mode`, visible when Futures selected)
     - Determines if collateral is shared (cross) or isolated per pair
     - Only applicable for futures trading
   - **Liquidation Buffer** (`liquidation_buffer`, visible when Futures selected)
     - Safety net ratio between liquidation price and stoploss
     - Default: 0.05 (5%)

2. **Pair Configuration**

   - **Pair Whitelist** (`exchange.pair_whitelist`)
     - List of pairs to use for trading
     - Supports regex patterns (e.g., `.*/BTC`)
     - Essential for defining tradeable pairs
   - **Pair Blacklist** (`exchange.pair_blacklist`)
     - List of pairs to absolutely avoid for trading
     - Takes precedence over whitelist
   - **Stake Currency** (`stake_currency`)
     - Base currency used for trading
     - Required setting for bot operation
     - Default is USDT

3. **Basic Trade Parameters**
   - **Max Open Trades** (`max_open_trades`)
     - Number of trades the bot is allowed to have open
     - Use -1 for unlimited (limited by pairlist)
     - Required parameter
   - **Stake Amount** (`stake_amount`)
     - Amount of stake_currency to use per trade
     - Can be set to "unlimited" to use full available balance
     - Required parameter

### Advanced View

1. **Advanced Trade Parameters**

   - **Available Capital** (`available_capital`)
     - Starting capital for the bot
     - Useful when running multiple bots on same exchange account
   - **Tradable Balance Ratio** (`tradable_balance_ratio`)
     - Ratio of total account balance the bot can use
     - Default: 0.99 (99%)
   - **Position Adjustment Settings** (`position_adjustment_enable`)
     - Enable/disable position adjustments
     - Maximum additional orders per trade (`max_entry_position_adjustment`)
     - Default: disabled
   - **Minimal ROI** (`minimal_roi`)
     - Threshold for exiting trades based on profit
     - Time-based profit targets
     - Example:
       ```json
       "minimal_roi": {
           "40": 0.0,    # Exit after 40 min if profit is not negative
           "30": 0.01,   # Exit after 30 min if profit is at least 1%
           "20": 0.02,   # Exit after 20 min if profit is at least 2%
           "0":  0.04    # Exit immediately if profit is at least 4%
       }
       ```

2. **Order Settings**

   - **Order Types** (`order_types`)
     - Define types for entry, exit, stoploss orders
     - Options: "market", "limit"
     - Separate settings for emergency exits (`emergency_exit`)
   - **Time in Force** (`order_time_in_force`)
     - GTC (Good Till Canceled) - default
     - FOK (Fill Or Kill)
     - IOC (Immediate Or Canceled)
     - PO (Post Only)
   - **Unfilled Timeout** (`unfilledtimeout`)
     - How long to wait for entry/exit orders
     - Separate settings for entry (`unfilledtimeout.entry`) and exit (`unfilledtimeout.exit`)
     - Unit can be minutes or seconds (`unfilledtimeout.unit`)

3. **Display & Technical**
   - **Fiat Display Currency** (`fiat_display_currency`)
     - Currency for converting profit/loss displays
     - Uses Coingecko API
     - Supports major fiat (USD, EUR, etc.) and crypto (BTC, ETH)
   - **Dry Run Settings** (`dry_run`)
     - Simulation mode settings
     - Initial simulation wallet balance (`dry_run_wallet`)

### Implementation Recommendations:

1. Show warning when accessing advanced settings
2. Include documentation links next to advanced settings
3. Add validation rules from configuration
4. Show default values clearly
5. Implement proper error handling for invalid combinations
6. Add tooltips with explanations from the documentation
