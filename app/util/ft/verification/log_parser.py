from datetime import datetime
import json
from typing import List, Dict, Optional, Generator
from pydantic import BaseModel, Field

from ...logger import setup_logger


class LogEntry(BaseModel):
    """Represents a single log entry from Freqtrade JSONL logs."""

    timestamp: datetime = Field(description="Timestamp of the log entry")
    created: float = Field(description="Unix timestamp when the log was created")
    name: str = Field(description="Logger name/component")
    levelname: str = Field(description="Log level (INFO, WARNING, ERROR, etc.)")
    message: str = Field(description="Log message content")
    module: str = Field(description="Python module that generated the log")
    lineno: int = Field(description="Line number in the source code")
    details: Optional[Dict] = Field(None, description="Additional log details")


class LogSummary(BaseModel):
    """Summary of log analysis."""

    info: List[LogEntry] = Field(
        default_factory=list, description="List of info log entries"
    )
    warnings: List[LogEntry] = Field(
        default_factory=list, description="List of warning log entries"
    )
    errors: List[LogEntry] = Field(
        default_factory=list, description="List of error log entries"
    )
    total_info: int = Field(
        default=0, description="Total number of info messages found"
    )
    total_warnings: int = Field(default=0, description="Total number of warnings found")
    total_errors: int = Field(default=0, description="Total number of errors found")
    start_time: Optional[datetime] = Field(
        None, description="Timestamp of first log entry"
    )
    end_time: Optional[datetime] = Field(
        None, description="Timestamp of last log entry"
    )


class JsonlLogParser:
    """Parser for Freqtrade JSONL log files."""

    def __init__(self):
        """Initialize the parser."""
        self.summary = LogSummary()
        self.logger = setup_logger(__name__)

    def parse_log_line(self, line: str) -> Optional[LogEntry]:
        """
        Parse a single JSONL log line into a LogEntry object.

        Args:
            line (str): Raw JSON log line to parse

        Returns:
            Optional[LogEntry]: Parsed log entry or None if line couldn't be parsed
        """
        try:
            if not line.strip():
                return None

            # Parse JSON line
            log_data = json.loads(line)

            # Convert timestamp string to datetime
            log_data["timestamp"] = datetime.strptime(
                log_data["timestamp"], "%Y-%m-%d %H:%M:%S"
            )

            # Create log entry from parsed data
            return LogEntry(**log_data)
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            self.logger.warning(f"Failed to parse log line: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error parsing log line: {str(e)}")
            return None

    def process_log_file(self, file_path: str) -> LogSummary:
        """
        Process a JSONL log file and collect log entries by level.

        Args:
            file_path (str): Path to the JSONL log file

        Returns:
            LogSummary: Summary of found log entries
        """
        # Reset summary
        self.summary = LogSummary()

        try:
            with open(file_path, "r") as f:
                for line in f:
                    entry = self.parse_log_line(line)
                    if entry:
                        self._process_entry(entry)

            # Sort all entries by timestamp
            self.summary.info.sort(key=lambda x: x.timestamp)
            self.summary.warnings.sort(key=lambda x: x.timestamp)
            self.summary.errors.sort(key=lambda x: x.timestamp)

            # Set start and end times
            all_entries = (
                self.summary.info + self.summary.warnings + self.summary.errors
            )
            if all_entries:
                self.summary.start_time = min(entry.timestamp for entry in all_entries)
                self.summary.end_time = max(entry.timestamp for entry in all_entries)

        except Exception as e:
            self.logger.error(f"Error processing log file {file_path}: {str(e)}")

        return self.summary

    def _process_entry(self, entry: LogEntry) -> None:
        """
        Process a single log entry and add it to the appropriate collection.

        Args:
            entry (LogEntry): The log entry to process
        """
        if entry.levelname == "INFO":
            self.summary.info.append(entry)
            self.summary.total_info += 1
        elif entry.levelname == "WARNING":
            self.summary.warnings.append(entry)
            self.summary.total_warnings += 1
        elif entry.levelname == "ERROR":
            self.summary.errors.append(entry)
            self.summary.total_errors += 1

    def get_entries_by_component(self, component: str) -> List[LogEntry]:
        """
        Get all log entries for a specific component/logger name.

        Args:
            component (str): Component/logger name to filter by

        Returns:
            List[LogEntry]: List of log entries from the specified component
        """
        all_entries = self.summary.info + self.summary.warnings + self.summary.errors
        return sorted(
            [entry for entry in all_entries if entry.name == component],
            key=lambda x: x.timestamp,
        )

    def get_entries_by_level(self, level: str) -> List[LogEntry]:
        """
        Get all log entries for a specific log level.

        Args:
            level (str): Log level to filter by (INFO, WARNING, ERROR)

        Returns:
            List[LogEntry]: List of log entries with the specified level
        """
        if level == "INFO":
            return self.summary.info
        elif level == "WARNING":
            return self.summary.warnings
        elif level == "ERROR":
            return self.summary.errors
        return []

    def has_critical_errors(self) -> bool:
        """
        Check if there are any error level entries in the logs.

        Returns:
            bool: True if error entries are found
        """
        return self.summary.total_errors > 0
