"""
Pydantic schemas for data download verification.
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class DataGap(BaseModel):
    """Represents a gap in the downloaded data."""

    start_date: datetime = Field(description="Start of the gap")
    end_date: datetime = Field(description="End of the gap")
    missing_candles: int = Field(description="Number of missing candles")
    timeframe: str = Field(description="Timeframe of the data")


class DateRangeInfo(BaseModel):
    """Information about the date range of downloaded data."""

    requested_start: datetime = Field(description="Requested start date")
    requested_end: datetime = Field(description="Requested end date")
    actual_start: datetime = Field(description="Actual start date in the data")
    actual_end: datetime = Field(description="Actual end date in the data")
    coverage_percentage: float = Field(
        description="Percentage of requested timeframe covered by data"
    )
    has_extra_data: bool = Field(
        description="Whether the data contains points outside requested range"
    )
    gaps: List[DataGap] = Field(
        default_factory=list, description="List of gaps in the data"
    )
    candles_expected: int = Field(description="Expected number of candles")
    candles_found: int = Field(description="Actual number of candles found")


class VerificationResult(BaseModel):
    """Result of verification process."""

    success: bool = Field(description="Whether the verification was successful")
    error_type: Optional[str] = Field(
        None, description="Type of error if verification failed"
    )
    error_message: Optional[str] = Field(
        None, description="Detailed error message if verification failed"
    )
    verified_files: List[str] = Field(
        default_factory=list, description="List of verified file paths"
    )
    verification_time: datetime = Field(
        default_factory=datetime.utcnow,
        description="Time when verification was performed",
    )
    date_range_info: Optional[Dict[str, DateRangeInfo]] = Field(
        None,
        description="Date range verification results per file",
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="List of non-critical issues found during verification",
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "success": True,
                "error_type": None,
                "error_message": None,
                "verified_files": [
                    "ft_userdata/_common_data/BTC_USDT-1h-futures.feather",
                    "ft_userdata/_common_data/ETH_USDT-1h-futures.feather",
                ],
                "verification_time": "2025-02-06T12:00:00Z",
                "date_range_info": {
                    "ft_userdata/_common_data/BTC_USDT-1h-futures.feather": {
                        "requested_start": "2025-01-28T00:00:00Z",
                        "requested_end": "2025-02-04T00:00:00Z",
                        "actual_start": "2025-01-28T00:00:00Z",
                        "actual_end": "2025-02-04T23:00:00Z",
                        "coverage_percentage": 100.0,
                        "has_extra_data": True,
                        "gaps": [
                            {
                                "start_date": "2025-01-30T12:00:00Z",
                                "end_date": "2025-01-30T14:00:00Z",
                                "missing_candles": 2,
                                "timeframe": "1h",
                            }
                        ],
                        "candles_expected": 168,
                        "candles_found": 166,
                    }
                },
                "warnings": [
                    "Found 2 missing candles in BTC_USDT-1h-futures.feather",
                    "Data extends beyond requested range in ETH_USDT-1h-futures.feather",
                ],
            }
        }
