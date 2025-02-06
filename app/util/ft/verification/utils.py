"""
Utility functions for data verification.
"""

from datetime import datetime, timedelta
from typing import List, Tuple

import pandas as pd


class TimeframeUtils:
    """Utilities for handling timeframe calculations."""

    # Map timeframe strings to timedelta
    TIMEFRAME_MAP = {
        "1m": timedelta(minutes=1),
        "3m": timedelta(minutes=3),
        "5m": timedelta(minutes=5),
        "15m": timedelta(minutes=15),
        "30m": timedelta(minutes=30),
        "1h": timedelta(hours=1),
        "2h": timedelta(hours=2),
        "4h": timedelta(hours=4),
        "6h": timedelta(hours=6),
        "8h": timedelta(hours=8),
        "12h": timedelta(hours=12),
        "1d": timedelta(days=1),
        "3d": timedelta(days=3),
        "1w": timedelta(weeks=1),
        "1M": timedelta(days=30),  # Approximate
    }

    @classmethod
    def parse_timeframe(cls, timeframe: str) -> timedelta:
        """
        Convert timeframe string to timedelta.

        Args:
            timeframe (str): Timeframe string (e.g., "1h", "4h", "1d")

        Returns:
            timedelta: Corresponding timedelta object

        Raises:
            ValueError: If timeframe format is invalid
        """
        if timeframe not in cls.TIMEFRAME_MAP:
            raise ValueError(
                f"Invalid timeframe format: {timeframe}. "
                f"Supported formats: {list(cls.TIMEFRAME_MAP.keys())}"
            )
        return cls.TIMEFRAME_MAP[timeframe]

    @classmethod
    def parse_date_range(cls, date_range: str) -> Tuple[datetime, datetime]:
        """
        Parse freqtrade date range string.

        Args:
            date_range (str): Date range in format "YYYYMMDD-YYYYMMDD"

        Returns:
            Tuple[datetime, datetime]: Start and end datetime objects

        Raises:
            ValueError: If date range format is invalid
        """
        try:
            start_str, end_str = date_range.split("-")
            start_date = datetime.strptime(start_str, "%Y%m%d")
            end_date = datetime.strptime(end_str, "%Y%m%d")
            # End date should be at the end of the day
            end_date = end_date.replace(hour=23, minute=59, second=59)
            return start_date, end_date
        except ValueError as e:
            raise ValueError(
                f"Invalid date range format: {date_range}. "
                "Expected format: YYYYMMDD-YYYYMMDD"
            ) from e

    @classmethod
    def calculate_expected_candles(
        cls, start_date: datetime, end_date: datetime, timeframe: str
    ) -> int:
        """
        Calculate expected number of candles for a date range.

        Args:
            start_date (datetime): Start date
            end_date (datetime): End date
            timeframe (str): Timeframe string

        Returns:
            int: Expected number of candles
        """
        interval = cls.parse_timeframe(timeframe)
        total_time = end_date - start_date
        return int(total_time / interval) + 1  # +1 to include both start and end

    @classmethod
    def find_gaps(
        cls,
        df: pd.DataFrame,
        timeframe: str,
        min_gap_size: int = 2,
    ) -> List[Tuple[datetime, datetime, int]]:
        """
        Find gaps in time series data.

        Args:
            df (pd.DataFrame): DataFrame with 'date' column
            timeframe (str): Timeframe string
            min_gap_size (int, optional): Minimum gap size to report. Defaults to 2.

        Returns:
            List[Tuple[datetime, datetime, int]]: List of (gap_start, gap_end, missing_candles)
        """
        # Sort by date to ensure correct gap detection
        df = df.sort_values("date")
        interval = cls.parse_timeframe(timeframe)

        # Calculate time differences between consecutive rows
        time_diffs = df["date"].diff()

        # Find gaps larger than the timeframe
        gaps = []
        for i in range(1, len(df)):
            diff = time_diffs.iloc[i]
            if diff > interval:
                missing_candles = int(diff / interval) - 1
                if missing_candles >= min_gap_size:
                    gap_start = df["date"].iloc[i - 1]
                    gap_end = df["date"].iloc[i]
                    gaps.append((gap_start, gap_end, missing_candles))

        return gaps
