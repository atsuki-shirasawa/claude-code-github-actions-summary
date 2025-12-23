"""Formatting utilities for metrics data."""


def format_duration(duration_ms: int | None) -> str:
    """Format duration in milliseconds to seconds.

    Args:
        duration_ms: Duration in milliseconds

    Returns:
        Duration in seconds as string or "N/A"
    """
    if duration_ms:
        seconds = duration_ms / 1000
        return str(seconds)
    return "N/A"


def format_timestamp(timestamp: str | None) -> str:
    """Format ISO timestamp to readable format.

    Args:
        timestamp: ISO format timestamp string

    Returns:
        Formatted timestamp string or "N/A"
    """
    if timestamp:
        return timestamp[:19].replace("T", " ")
    return "N/A"
