"""Workflow run processing utilities."""

import re

from loguru import logger

from .metrics_extractor import extract_metrics_from_log


def process_runs(runs: list[dict], repo: str) -> list[dict]:
    """Process workflow runs and extract metrics.

    Args:
        runs: List of workflow run dictionaries
        repo: Repository name (owner/repo)

    Returns:
        List of processed result dictionaries
    """
    results = []

    for run in runs:
        run_id = str(run["databaseId"])
        pr_name = run.get("displayTitle", "N/A")
        branch = run.get("headBranch", "N/A")
        status = run.get("conclusion", "unknown")

        logger.info(f"Processing run {run_id}...")
        metrics = extract_metrics_from_log(run_id, repo)

        # Use PR number from log if available, otherwise try to extract from displayTitle
        pr_number = metrics.get("pr_number")
        if not pr_number:
            pr_match = re.search(r"#(\d+)", pr_name)
            if pr_match:
                pr_number = int(pr_match.group(1))

        results.append(
            {
                "run_id": run_id,
                "pr_name": pr_name,
                "pr_number": pr_number,
                "branch": branch,
                "status": status,
                **{k: v for k, v in metrics.items() if k != "pr_number"},
            },
        )

    # Sort by start_time descending (most recent first)
    results.sort(key=lambda x: x.get("start_time", "") or "", reverse=True)

    return results
