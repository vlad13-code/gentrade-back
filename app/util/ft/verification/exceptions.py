"""
Custom exceptions for data download verification.
"""

from typing import Optional


class DownloadVerificationError(Exception):
    """Base class for download verification errors."""

    def __init__(self, message: str, details: Optional[dict] = None):
        """
        Initialize the error.

        Args:
            message (str): Error message
            details (Optional[dict]): Additional error details
        """
        super().__init__(message)
        self.details = details or {}


class DockerExecutionError(DownloadVerificationError):
    """Raised when Docker command execution fails."""

    pass


class FileVerificationError(DownloadVerificationError):
    """Raised when file verification fails."""

    pass


class DataIntegrityError(DownloadVerificationError):
    """Raised when data integrity check fails."""

    pass
