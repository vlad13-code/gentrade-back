strategy_code_instructions = """You are an **expert Freqtrade strategy developer** and **Python engineer**. Create a **complete, production-ready** Freqtrade strategy that meets the following **specifications** and **best practices**:

1. **Strategy Metadata**  
   - **Strategy Name**: {name}  
   - **Description**: {description}  
   - **Timeframe**: {timeframe}  
   - **Can Short**: {can_short}  
   - **Startup Candle Count**: Automatically set based on the largest indicator period (use a reasonable buffer to ensure indicator stability).

2. **Indicators**  
   - Implement the following primary indicators exactly as specified (vectorized calculations, no loops over each row):
     ```
     {indicators}
     ```
   - Apply them in the `populate_indicators()` method.  
   - Add comments and docstrings explaining how each indicator is calculated.  
   - Ensure you do **not** introduce lookahead bias (no negative `.shift(-1)` or references to future data in `populate_*` methods).

3. **Entry Signals**  
   - In `populate_entry_trend()`:
     ```
     {entry_signals}
     ```
   - Generate **long** signals by setting `enter_long = 1`; if `can_short` is true, you may also generate **short** signals with `enter_short = 1`.  
   - Use an `enter_tag` column to label specific entry conditions.  
   - Follow Colliding Signals rules to avoid immediate buy-then-sell collisions.

4. **Exit Signals**  
   - In `populate_exit_trend()`:
     ```
     {exit_signals}
     ```
   - Generate **long** exits by setting `exit_long = 1`; if short trades are used, also define `exit_short = 1`.  
   - Use an `exit_tag` column to label specific exit conditions.  
   - If signals rely on advanced conditions, consider adding `custom_exit()` callbacks as needed.

5. **Minimal ROI and Stoploss**  
   - **Minimal ROI**:  
     ```
     {minimal_roi}
     ```  
   - **Stoploss**:  
     ```
     {stoploss}
     ```
   - Ensure they comply with Freqtrade best practices (e.g., do not rely on future data).  
   - Optionally demonstrate trailing stoploss or `custom_stoploss()` if relevant.

6. **Optional / Advanced Callbacks**  
   - If the strategy specifies advanced logic, incorporate strategy callbacks such as:
     - `custom_stoploss()`  
     - `custom_exit()`  
     - `adjust_trade_position()`  
     - `confirm_trade_entry()`  
     - `leverage()` (if using futures/`can_short`)  
   - Include docstrings clarifying the callback’s purpose and logic.

7. **Hyperopt Parameters**  
   - Where appropriate, use hyperoptable parameters (e.g., `self.buy_rsi = IntParameter(...)`) for critical indicator or exit thresholds.  
   - Show how each parameter is integrated into the strategy’s logic.

8. **Code Quality and Documentation**  
   - Use **type hints** for all methods.  
   - Adhere to **PEP 8** style guidelines.  
   - Provide **clear docstrings** explaining each indicator, signal, and callback.  
   - Include all necessary imports (e.g. `import talib.abstract as ta`, `from freqtrade.strategy import IStrategy`, etc.).
   - Strategy class name must be {name} in camel case.

9. **Final Output**  
   - Return the complete Python code for the strategy class.  
   - The resulting file must be **directly usable** in Freqtrade by placing it in `user_data/strategies/`.  
   - Focus on clarity, maintainability, and avoid any non-deterministic or data-leaking patterns (e.g., no referencing of external real-time data in backtesting).

**Generate the complete Freqtrade strategy code now**, ensuring that it **fully** follows the above requirements and guidelines."""
