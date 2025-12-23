"""GitHub API client for workflow runs."""

import json
import subprocess
import sys
from datetime import UTC, datetime, timedelta

from loguru import logger


def get_workflow_runs(
    workflow_name: str,
    limit: int,
    days: int,
    repo: str,
) -> list[dict]:
    """Get workflow runs from GitHub Actions.

    Args:
        workflow_name: Name of the workflow
        limit: Maximum number of runs to fetch
        days: Number of days to look back
        repo: Repository name (owner/repo)

    Returns:
        List of workflow run dictionaries

    Raises:
        SystemExit: If command execution fails
    """
    cmd = [
        "gh",
        "run",
        "list",
        "--workflow",
        workflow_name,
        "--limit",
        str(limit),
        "--repo",
        repo,
        "--json",
        "databaseId,displayTitle,headBranch,conclusion,createdAt,number",
    ]
    try:
        runs_json = subprocess.check_output(cmd, text=True)  # noqa: S603
        runs = json.loads(runs_json)
    except Exception as e:
        logger.error(f"Error getting run list: {e}")
        sys.exit(1)

    # Filter runs by date
    cutoff_date = datetime.now(UTC) - timedelta(days=days)
    filtered_runs = []
    for run in runs:
        created_at = run.get("createdAt", "")
        if created_at:
            try:
                run_date = datetime.fromisoformat(
                    created_at.replace("Z", "+00:00"),
                )
                if run_date >= cutoff_date:
                    filtered_runs.append(run)
            except (ValueError, AttributeError):
                # If date parsing fails, include it anyway
                filtered_runs.append(run)
        else:
            filtered_runs.append(run)

    return filtered_runs
