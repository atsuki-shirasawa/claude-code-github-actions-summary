<!-- @format -->

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Claude Metrics Extractor is a CLI tool that analyzes GitHub Actions logs from Claude Code automated code review workflows. It extracts metrics (cost, duration, turns, commits, etc.) and generates CSV/JSON reports for usage analysis.

## Development Commands

### Setup

```bash
uv sync              # Install runtime dependencies
uv sync --group dev  # Install with dev dependencies
```

### Running the Tool

```bash
uv run main.py --repo owner/repo --workflow "Claude Auto Review with Tracking"
uv run main.py --repo owner/repo --days 7 --limit 100
```

### Code Quality

```bash
# Run all quality checks
uv run tox

# Individual checks
uv run ruff check .         # Lint
uv run ruff check --fix .   # Lint with auto-fix
uv run black .              # Format
uv run black --check .      # Check formatting
uv run mypy .               # Type check
```

## Architecture

### Data Flow Pipeline

The tool follows a sequential pipeline architecture:

1. **github_client.py**: Fetches workflow runs via `gh` CLI

   - Calls `gh run list` to get workflow execution metadata
   - Filters runs by date range (last N days)
   - Returns list of run dictionaries with basic metadata

2. **processor.py**: Orchestrates metric extraction

   - Iterates through workflow runs sequentially
   - Calls metrics_extractor for each run
   - Merges extracted metrics with run metadata
   - Extracts PR numbers from display titles if not found in logs
   - Sorts results by start_time (most recent first)

3. **metrics_extractor.py**: Core extraction logic

   - Calls `gh run view --log` to fetch raw logs
   - Uses regex patterns to extract:
     - PR metadata: number, author, commits, changed files
     - Model information from JSON fragments
     - Result JSON containing cost/duration/turns
     - Start/end timestamps
   - Delegates multiline JSON parsing to log_parser

4. **log_parser.py**: Multiline JSON extraction

   - Handles GitHub Actions log format: `job\tstep\ttimestamp\tcontent`
   - Tracks opening/closing braces to reconstruct split JSON
   - Strips timestamp prefixes from each line
   - Handles malformed JSON (trailing commas, etc.)
   - Critical for extracting Claude Code's result JSON which spans multiple log lines

5. **report_generator.py**: CSV output
   - Formats metrics using formatters.py helpers
   - Generates human-readable CSV with Japanese headers
   - Creates GitHub PR links

### Key Design Patterns

**Regex-based Log Parsing**: The tool relies heavily on regex patterns to extract structured data from unstructured GitHub Actions logs. Key patterns:

- `PR NUMBER:\s*(\d+)` - Extracts PR number from log text
- `"model"\s*:\s*"([^"]+)"` - Extracts model name from JSON fragments
- `"type".*"result"` - Identifies result JSON blocks

**Multiline JSON Reconstruction**: GitHub Actions logs split JSON across lines with prefixes on each line. The `log_parser.extract_json_from_multiline_log()` function:

- Strips prefixes (job name, step name, timestamp) from each line
- Uses brace counting to determine when complete JSON is assembled
- Handles the "review\tUNKNOWN STEP\t2025-12-17T23:51:16.7770671Z" prefix format

**Subprocess-based GitHub CLI Integration**: All GitHub API interactions use `gh` CLI via subprocess rather than direct API calls. This simplifies authentication (uses `gh auth`) but requires `gh` to be installed and authenticated.

## Code Standards

### Type Annotations

- All functions must have type hints for parameters and return values
- Use modern Python 3.12+ syntax: `list[dict]` not `List[Dict]`
- mypy strict mode enforced: `disallow_untyped_defs = true`

### Code Style

- Line length: 79 characters (PEP 8 compliant)
- Formatted with Black
- Linted with Ruff (includes pycodestyle, pyflakes, isort, pydocstyle, bandit, etc.)
- Docstrings required (Google style)

### Error Handling

- Use loguru for all logging
- Subprocess calls use `subprocess.check_output()` with proper error handling
- Failed log parsing returns default values (None/"N/A") rather than crashing

## Important Implementation Notes

### Log Format Parsing

When working with log extraction, understand GitHub Actions log format:

```
job_name\tstep_name\ttimestamp\tactual_content
```

Always strip these prefixes before parsing JSON. See `_extract_json_part_from_log_line()` in log_parser.py.

### Model Name Normalization

The CSV report normalizes model names (e.g., `claude-sonnet-4-5-20250929` → `sonnet-4.5`). This happens only in report_generator.py, not in raw JSON output.

### PR Number Extraction Fallback

PR numbers are extracted with a two-tier approach:

1. Primary: Regex search for `PR NUMBER:` in logs
2. Fallback: Extract `#(\d+)` from displayTitle if log parsing fails

This dual approach handles cases where log format varies.

### Timestamp Handling

All timestamps are ISO 8601 format from GitHub. The formatters.py converts them to readable format (`YYYY-MM-DD HH:MM:SS`) for CSV output, but preserves original format in JSON.
