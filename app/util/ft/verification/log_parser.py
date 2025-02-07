from datetime import datetime
import re
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

from ...logger import setup_logger


class LogEntry(BaseModel):
    """Represents a single log entry."""

    timestamp: datetime = Field(description="Timestamp of the log entry")
    level: str = Field(description="Log level (WARNING, ERROR, etc.)")
    component: str = Field(description="Component that generated the log")
    message: str = Field(description="Log message content")
    details: Optional[Dict] = Field(None, description="Additional log details")


class DockerLogSummary(BaseModel):
    """Summary of Docker log analysis."""

    warnings: List[LogEntry] = Field(
        default_factory=list, description="List of warning log entries"
    )
    errors: List[LogEntry] = Field(
        default_factory=list, description="List of error log entries"
    )
    total_warnings: int = Field(default=0, description="Total number of warnings found")
    total_errors: int = Field(default=0, description="Total number of errors found")


class DockerLogParser:
    """Parser for Docker log output with focus on WARNING and ERROR messages."""

    # Regex to match timestamp at the start of a log line
    TIMESTAMP_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}")

    # Regex to match a complete log line
    LOG_LINE_PATTERN = re.compile(
        r"(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\s*-\s*(?P<component>[^-]+)-\s*(?P<level>[^-]+)-\s*(?P<message>.*)"
    )

    def __init__(self):
        """Initialize the parser."""
        self.summary = DockerLogSummary()
        self.logger = setup_logger(__name__)

    def parse_log_line(self, line: str) -> Optional[LogEntry]:
        """
        Parse a single log line into a LogEntry object.

        Args:
            line (str): Raw log line to parse

        Returns:
            Optional[LogEntry]: Parsed log entry or None if line couldn't be parsed
        """
        try:
            # Skip empty lines
            if not line.strip():
                return None

            # Try to match the complete log line pattern
            match = self.LOG_LINE_PATTERN.match(line)
            if not match:
                return None

            # Extract components
            timestamp_str = match.group("timestamp")
            component = match.group("component")
            level = match.group("level")
            message = match.group("message")

            # Parse timestamp
            try:
                timestamp = datetime.strptime(
                    timestamp_str.strip(), "%Y-%m-%d %H:%M:%S,%f"
                )
            except ValueError:
                return None

            # Create log entry
            return LogEntry(
                timestamp=timestamp,
                component=component.strip(),
                level=level.strip(),
                message=message.strip(),
            )
        except Exception:
            return None

    def process_docker_output(self, docker_result: dict) -> DockerLogSummary:
        """
        Process Docker command output and collect WARNING and ERROR logs.

        Args:
            docker_result (dict): Docker command output containing stdout and stderr

        Returns:
            DockerLogSummary: Summary of found warnings and errors
        """
        # Reset summary
        self.summary = DockerLogSummary()

        def process_lines(lines: str) -> None:
            if not lines:
                return

            # Split into lines and reconstruct complete log entries
            current_lines = []

            for line in lines.splitlines():
                line = line.strip()
                if not line:
                    continue

                # If this is a new log entry
                if self.TIMESTAMP_PATTERN.match(line):
                    # Process previous lines if any
                    if current_lines:
                        complete_line = " ".join(current_lines)
                        entry = self.parse_log_line(complete_line)
                        if entry:
                            self._process_entry(entry)
                    # Start new entry
                    current_lines = [line]
                else:
                    # Continue current entry
                    current_lines.append(line)

            # Process the last entry if any
            if current_lines:
                complete_line = " ".join(current_lines)
                entry = self.parse_log_line(complete_line)
                if entry:
                    self._process_entry(entry)

        # Process stderr first as it's more likely to contain errors
        process_lines(docker_result.get("stderr", ""))

        # Process stdout
        process_lines(docker_result.get("stdout", ""))

        return self.summary

    def _process_entry(self, entry: LogEntry) -> None:
        """
        Process a single log entry and add it to the appropriate collection.
        Checks for duplicates before adding.

        Args:
            entry (LogEntry): The log entry to process
        """

        def is_duplicate(entry: LogEntry, entries: List[LogEntry]) -> bool:
            """Check if entry is already in the list."""
            for existing in entries:
                # Compare timestamps and messages
                if (
                    existing.timestamp == entry.timestamp
                    and existing.component == entry.component
                    and existing.message == entry.message
                ):
                    return True
            return False

        if "WARNING" in entry.level:
            if not is_duplicate(entry, self.summary.warnings):
                self.summary.warnings.append(entry)
                self.summary.total_warnings += 1
        elif "ERROR" in entry.level:
            if not is_duplicate(entry, self.summary.errors):
                self.summary.errors.append(entry)
                self.summary.total_errors += 1

    def get_warnings_by_component(self) -> Dict[str, List[LogEntry]]:
        """
        Group warnings by component.

        Returns:
            Dict[str, List[LogEntry]]: Warnings grouped by component
        """
        warnings_by_component = {}
        for warning in self.summary.warnings:
            if warning.component not in warnings_by_component:
                warnings_by_component[warning.component] = []
            warnings_by_component[warning.component].append(warning)
        return warnings_by_component

    def get_errors_by_component(self) -> Dict[str, List[LogEntry]]:
        """
        Group errors by component.

        Returns:
            Dict[str, List[LogEntry]]: Errors grouped by component
        """
        errors_by_component = {}
        for error in self.summary.errors:
            if error.component not in errors_by_component:
                errors_by_component[error.component] = []
            errors_by_component[error.component].append(error)
        return errors_by_component

    def has_critical_errors(self) -> bool:
        """
        Check if there are any critical errors in the logs.

        Returns:
            bool: True if critical errors are found
        """
        return self.summary.total_errors > 0
