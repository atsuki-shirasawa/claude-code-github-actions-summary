"""Metrics extraction from GitHub Actions logs."""

import re
import subprocess

from loguru import logger

from .log_parser import extract_json_from_multiline_log


def extract_metrics_from_log(run_id: str, repo: str) -> dict:  # noqa: C901
    """Extract all metrics from a GitHub Actions run log.

    Args:
        run_id: GitHub Actions run ID
        repo: Repository name (owner/repo)

    Returns:
        Dictionary containing extracted metrics
    """
    result: dict = {
        "run_id": run_id,
        "model": None,
        "total_cost_usd": None,
        "duration_ms": None,
        "num_turns": None,
        "start_time": None,
        "end_time": None,
        "is_error": None,
        "pr_number": None,
        "pr_author": None,
        "total_commits": None,
        "changed_files": None,
    }

    try:
        # Get log
        cmd = ["gh", "run", "view", run_id, "--log", "--repo", repo]
        log_output = subprocess.check_output(  # noqa: S603
            cmd,
            stderr=subprocess.STDOUT,
            text=True,
        )
        log_lines = log_output.split("\n")

        # Extract PR number from log
        pr_number_pattern = r"PR NUMBER:\s*(\d+)"
        pr_match = re.search(pr_number_pattern, log_output)
        if pr_match:
            result["pr_number"] = int(pr_match.group(1))

        # Extract PR Author from log
        pr_author_pattern = r"PR Author:\s*([^\n]+)"
        pr_author_match = re.search(pr_author_pattern, log_output)
        if pr_author_match:
            result["pr_author"] = pr_author_match.group(1).strip()

        # Extract Total Commits from log
        total_commits_pattern = r"Total Commits:\s*(\d+)"
        total_commits_match = re.search(total_commits_pattern, log_output)
        if total_commits_match:
            result["total_commits"] = int(total_commits_match.group(1))

        # Extract Changed Files from log
        changed_files_pattern = r"Changed Files:\s*(\d+)\s*files?"
        changed_files_match = re.search(changed_files_pattern, log_output)
        if changed_files_match:
            result["changed_files"] = int(changed_files_match.group(1))

        # Extract model
        model_pattern = r'"model"\s*:\s*"([^"]+)"'
        model_matches = list(re.finditer(model_pattern, log_output))
        if model_matches:
            result["model"] = model_matches[-1].group(1)

        # Extract result JSON
        for i, line in enumerate(log_lines):
            if '"type"' in line and '"result"' in line:
                start_idx = i
                for j in range(max(0, i - 3), i):
                    if "{" in log_lines[j]:
                        start_idx = j
                        break

                json_obj = extract_json_from_multiline_log(
                    log_lines,
                    start_idx,
                )
                if json_obj and json_obj.get("type") == "result":
                    result["total_cost_usd"] = json_obj.get("total_cost_usd")
                    result["duration_ms"] = json_obj.get("duration_ms")
                    result["num_turns"] = json_obj.get("num_turns")
                    result["is_error"] = json_obj.get("is_error", False)
                    break

        # Extract timestamps
        timestamp_pattern = r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)"
        timestamps = re.findall(timestamp_pattern, log_output)

        if timestamps:
            result["start_time"] = timestamps[0]
            result["end_time"] = timestamps[-1]

    except subprocess.CalledProcessError as e:
        logger.error(f"Error getting log for run {run_id}: {e}")
    except Exception as e:
        logger.error(f"Error processing run {run_id}: {e}")

    return result
