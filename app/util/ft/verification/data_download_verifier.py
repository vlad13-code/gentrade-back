import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd

from app.util.ft.verification.log_parser import LogSummary
from app.util.logger import setup_logger

from .exceptions import (
    DataIntegrityError,
    DockerExecutionError,
    FileVerificationError,
)
from .schemas import DataGap, DateRangeInfo, VerificationResult
from .utils import TimeframeUtils


class DataDownloadVerifier:
    """Verifies market data download success."""

    def __init__(self, base_dir: str):
        """
        Initialize the verifier.

        Args:
            base_dir (str): Base directory where data files are stored
        """
        self.base_dir = Path(base_dir)
        self.logger = setup_logger(__name__)

    def verify_docker_execution(self, docker_result: LogSummary) -> None:
        """
        Verify Docker command execution success.

        Args:
            docker_result (LogSummary): Docker command execution result

        Raises:
            DockerExecutionError: If verification fails
        """
        if docker_result.errors:
            error_details = {
                "total_errors": docker_result.total_errors,
            }
            self.logger.debug(
                "Docker execution verification failed",
                extra={"error_details": error_details},
            )
            raise DockerExecutionError(
                "Docker command failed with error", details=error_details
            )

        # Log any warnings
        if docker_result.warnings:
            for warning in docker_result.warnings:
                self.logger.warning(
                    f"{warning.component}: {warning.message}",
                    extra={"timestamp": warning.timestamp},
                )

        self.logger.debug("Docker execution verification passed")

    def verify_files_existence(self, expected_files: List[str]) -> List[str]:
        """
        Verify downloaded files exist.

        Args:
            expected_files (List[str]): List of expected file paths

        Returns:
            List[str]: List of verified file paths

        Raises:
            FileVerificationError: If any file is missing
        """

        missing_files = []
        verified_files = []

        for file_path in expected_files:
            full_path = self.base_dir / file_path

            if not full_path.exists():
                self.logger.debug(f"File not found: {full_path}")
                missing_files.append(file_path)
            else:
                verified_files.append(str(full_path))

        if missing_files:
            self.logger.debug(
                "File existence verification failed",
                extra={"missing_files": missing_files},
            )
            raise FileVerificationError(
                "Some expected files are missing",
                details={"missing_files": missing_files},
            )

        self.logger.debug(
            "File existence verification passed",
            extra={"verified_files": verified_files},
        )
        return verified_files

    def verify_date_range(
        self,
        df: pd.DataFrame,
        date_range: str,
        timeframe: str,
        file_path: str,
    ) -> DateRangeInfo:
        """
        Verify date range coverage and find gaps in the data.

        Args:
            df (pd.DataFrame): DataFrame with market data
            date_range (str): Requested date range in format "YYYYMMDD-YYYYMMDD"
            timeframe (str): Timeframe string (e.g., "1h", "4h")
            file_path (str): Path to the data file for logging

        Returns:
            DateRangeInfo: Information about date range coverage and gaps
        """
        self.logger.debug(
            f"Verifying date range for {file_path}",
            extra={"date_range": date_range, "timeframe": timeframe},
        )

        # Parse requested date range
        requested_start, requested_end = TimeframeUtils.parse_date_range(date_range)

        # Get actual date range from data
        actual_start = df["date"].min().replace(tzinfo=None)
        actual_end = df["date"].max().replace(tzinfo=None)

        # Calculate expected number of candles
        candles_expected = TimeframeUtils.calculate_expected_candles(
            requested_start, requested_end, timeframe
        )
        candles_found = len(df)

        if candles_found < candles_expected:
            raise DataIntegrityError(
                f"Insufficient candles in {file_path}: expected {candles_expected} candles, found {candles_found}",
            )

        # Find gaps in the data
        gaps = TimeframeUtils.find_gaps(df, timeframe)
        data_gaps = [
            DataGap(
                start_date=start,
                end_date=end,
                missing_candles=missing,
                timeframe=timeframe,
            )
            for start, end, missing in gaps
        ]

        # Calculate coverage percentage
        total_missing_candles = sum(gap.missing_candles for gap in data_gaps)
        coverage_percentage = (
            (candles_expected - total_missing_candles) / candles_expected
        ) * 100

        # Check for data outside requested range
        has_extra_data = actual_start < requested_start or actual_end > requested_end

        return DateRangeInfo(
            requested_start=requested_start,
            requested_end=requested_end,
            actual_start=actual_start,
            actual_end=actual_end,
            coverage_percentage=coverage_percentage,
            has_extra_data=has_extra_data,
            gaps=data_gaps,
            candles_expected=candles_expected,
            candles_found=candles_found,
        )

    def verify_data_integrity(
        self,
        file_path: str,
        date_range: Optional[str] = None,
        timeframe: Optional[str] = None,
    ) -> Tuple[bool, Optional[DateRangeInfo]]:
        """
        Verify data file integrity and optionally check date range coverage.

        Args:
            file_path (str): Path to the data file
            date_range (Optional[str], optional): Date range to verify. Defaults to None.
            timeframe (Optional[str], optional): Timeframe string. Defaults to None.

        Returns:
            Tuple[bool, Optional[DateRangeInfo]]: Success status and date range info if applicable

        Raises:
            DataIntegrityError: If file integrity check fails
        """
        try:
            # Try to read the feather file
            # self.logger.debug(f"Reading file: {file_path}")
            df = pd.read_feather(file_path)

            # Check if dataframe is empty
            if df.empty:
                raise DataIntegrityError(
                    f"File {file_path} contains no data",
                    details={"file_path": file_path},
                )

            # Check for required columns (OHLCV data)
            required_columns = ["date", "open", "high", "low", "close", "volume"]
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise DataIntegrityError(
                    f"File {file_path} is missing required columns",
                    details={
                        "file_path": file_path,
                        "missing_columns": missing_columns,
                    },
                )

            # Verify date range if provided
            date_range_info = None
            if date_range and timeframe:
                date_range_info = self.verify_date_range(
                    df, date_range, timeframe, file_path
                )

            return True, date_range_info

        except Exception as e:
            if isinstance(e, DataIntegrityError):
                raise
            raise DataIntegrityError(
                f"Failed to verify data integrity for {file_path}",
                details={"file_path": file_path, "error": str(e)},
            )

    def verify_download(
        self,
        docker_result: Optional[LogSummary] = None,
        expected_files: List[str] = [],
        date_range: Optional[str] = None,
        timeframes: Optional[List[str]] = None,
    ) -> VerificationResult:
        """
        Perform complete verification of data download.

        Args:
            docker_result (LogSummary): Docker command execution result
            expected_files (List[str]): List of expected file paths
            date_range (Optional[str], optional): Date range to verify. Defaults to None.
            timeframes (Optional[List[str]], optional): List of timeframes to verify.
                Defaults to None.

        Returns:
            VerificationResult: Verification result
        """
        try:
            # Step 1: Verify Docker execution
            if docker_result:
                self.verify_docker_execution(docker_result)

            # Step 2: Verify files existence
            verified_files = self.verify_files_existence(expected_files)

            # Step 3: Verify data integrity and date ranges
            warnings = []
            date_range_info = {}

            for file_path in verified_files:
                # Extract timeframe from file name
                timeframe = None
                if timeframes:
                    for tf in timeframes:
                        if f"-{tf}-" in file_path:
                            timeframe = tf
                            break

                success, range_info = self.verify_data_integrity(
                    file_path, date_range, timeframe
                )

                if range_info:
                    date_range_info[file_path] = range_info

                    # Add warnings for gaps and extra data
                    if range_info.gaps:
                        warnings.append(
                            f"Found {len(range_info.gaps)} gaps in {file_path}"
                        )
                    if range_info.has_extra_data:
                        warnings.append(
                            f"Data extends beyond requested range in {file_path}"
                        )
                    if range_info.coverage_percentage < 100:
                        warnings.append(
                            f"Data coverage is {range_info.coverage_percentage:.1f}% "
                            f"in {file_path}"
                        )

            # All verifications passed
            return VerificationResult(
                success=True,
                verified_files=verified_files,
                verification_time=datetime.utcnow(),
                date_range_info=date_range_info or None,
                warnings=warnings,
            )

        except (DockerExecutionError, FileVerificationError, DataIntegrityError) as e:
            # Create verification result with error details
            return VerificationResult(
                success=False,
                error_type=e.__class__.__name__,
                error_message=str(e),
                verified_files=[],
                verification_time=datetime.utcnow(),
                date_range_info=None,
                warnings=[],
            )
