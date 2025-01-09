strategy_code_instructions = """You are an expert FreqTrade strategy developer. Generate a complete, production-ready FreqTrade strategy based on the following specifications:

Strategy Name: {name}
Description: {description}
Indicators: {indicators}
Entry Signals: {entry_signals}
Exit Signals: {exit_signals}
Minimal ROI: {minimal_roi}
Stoploss: {stoploss}
Timeframe: {timeframe}
Can Short: {can_short}

Follow these guidelines:
1. Use proper FreqTrade strategy class structure with all required methods
2. Implement all indicators and logic exactly as specified
3. Include detailed docstrings and comments
4. Use proper type hints
5. Follow PEP 8 style guidelines
6. Include hyperopt parameters where appropriate
7. Implement proper buy/sell signal logic
8. Add proper minimal_roi and stoploss settings
9. Include all necessary imports
10. Make the strategy production-ready and optimized

Generate the complete strategy code now."""
