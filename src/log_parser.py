"""Log parsing utilities for extracting JSON from GitHub Actions logs."""

import json
import re


def _extract_json_part_from_log_line(line: str) -> str:
    """Extract JSON content from a log line.

    Args:
        line: A single log line

    Returns:
        Extracted JSON part as string
    """
    # Extract JSON content after timestamp
    # Format: "review\tUNKNOWN STEP\t2025-12-17T23:51:16.7770671Z   "type": "result","
    timestamp_match = re.search(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z\s+(.*)",
        line,
    )
    if timestamp_match:
        return timestamp_match.group(1)

    # Fallback: get content after last tab
    parts = line.split("\t")
    if len(parts) >= 3:
        return parts[-1]
    return line.strip()


def _prepare_json_string(json_parts: list[str]) -> str:
    """Prepare JSON string from collected parts.

    Args:
        json_parts: List of JSON string parts

    Returns:
        Prepared JSON string starting with '{'
    """
    json_str = "".join(json_parts).strip()
    if not json_str.startswith("{"):
        first_brace = json_str.find("{")
        if first_brace >= 0:
            json_str = json_str[first_brace:]
    return json_str


def _parse_json_with_cleanup(json_str: str) -> dict | None:
    """Parse JSON string with automatic cleanup for common issues.

    Args:
        json_str: JSON string to parse

    Returns:
        Parsed JSON object or None if parsing fails
    """
    try:
        parsed = json.loads(json_str)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        # Try to fix trailing commas
        json_str = re.sub(r",\s*}", "}", json_str)
        json_str = re.sub(r",\s*]", "]", json_str)
        try:
            parsed = json.loads(json_str)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
    return None


def extract_json_from_multiline_log(
    log_lines: list[str],
    start_line_idx: int,
) -> dict | None:
    """Extract a complete JSON object from multiline log format.

    Args:
        log_lines: List of log lines
        start_line_idx: Starting index to begin extraction

    Returns:
        Parsed JSON object or None if extraction fails
    """
    json_parts = []
    brace_count = 0
    found_opening_brace = False

    for i in range(start_line_idx, len(log_lines)):
        line = log_lines[i]
        json_part = _extract_json_part_from_log_line(line)

        # Count braces
        open_braces = json_part.count("{")
        close_braces = json_part.count("}")
        brace_count += open_braces - close_braces

        if open_braces > 0:
            found_opening_brace = True

        json_parts.append(json_part)

        # If we found opening brace and brace count is 0, we have complete JSON
        if found_opening_brace and brace_count == 0:
            json_str = _prepare_json_string(json_parts)
            return _parse_json_with_cleanup(json_str)

    return None
