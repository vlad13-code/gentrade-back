FreqTrade is able to check if the data is available for a backtest. If not, it will download the data.

1. **General plan**

- Introduce new `FTMarketData` class in `util/ft/ft_market_data.py` with `download()` method that will run `freqtrade download-data` in Docker. It must take `pair`, `timeframe` and `date_range` as arguments.
- Add new step for data download in Celery task before backtest execution

2. **Data Verification Process**

- Parse strategy and/or user config to identify required:
  - Trading pairs (e.g. BTC/USDT, ETH/USDT)
  - Timeframes (1m, 5m, 1h)

3. **Automated Data Download**

- Run `freqtrade download-data` in Docker with parameters:
  - `--pairs` from strategy/user config
  - `--timeframes` from strategy/user config
  - `--datadir` mounted to `_common_data`
  - `--exchange` from user's configuration
- Add timeout and retry logic for failed downloads
- Validate downloaded data integrity

4. **Error Handling & Reporting**

- Add new exception types:
  - `DataDownloadTimeoutError`
- Implement status update in BacktestsORM:
  - `downloading_data`

This plan follows the existing patterns from:

- `ft_backtesting.py` Docker integration
- Celery task flow in `service_backtests.py`
- User directory management in `ft_userdir.py`
- Error handling patterns from `exceptions.py`

The implementation would require modifications to:

- `FTBacktesting` to include data checks
- Celery tasks in `tasks/backtests.py`
- Backtest status reporting in router endpoints
