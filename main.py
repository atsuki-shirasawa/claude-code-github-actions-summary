#!/usr/bin/env python3
"""Extract Claude Code metrics from GitHub Actions logs."""
import csv
import json
import re
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import click
from loguru import logger


def extract_json_from_multiline_log(  # noqa: C901
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

        # Extract JSON content after timestamp
        # Format: "review\tUNKNOWN STEP\t2025-12-17T23:51:16.7770671Z   "type": "result","
        timestamp_match = re.search(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z\s+(.*)",
            line,
        )
        if timestamp_match:
            json_part = timestamp_match.group(1)
        else:
            # Fallback: get content after last tab
            parts = line.split("\t")
            if len(parts) >= 3:
                json_part = parts[-1]
            else:
                json_part = line.strip()

        # Count braces
        open_braces = json_part.count("{")
        close_braces = json_part.count("}")
        brace_count += open_braces - close_braces

        if open_braces > 0:
            found_opening_brace = True

        json_parts.append(json_part)

        # If we found opening brace and brace count is 0, we have complete JSON
        if found_opening_brace and brace_count == 0:
            json_str = "".join(json_parts)
            json_str = json_str.strip()
            if not json_str.startswith("{"):
                first_brace = json_str.find("{")
                if first_brace >= 0:
                    json_str = json_str[first_brace:]

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
                    return None

    return None


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


def generate_csv_report(
    results: list[dict],
    output_file: str,
    repo: str,
) -> None:
    """Generate a CSV report from the results.

    Args:
        results: List of result dictionaries
        output_file: Output file path
        repo: Repository name (owner/repo)
    """
    with Path(output_file).open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)

        # Write header
        writer.writerow(
            [
                "PR番号",
                "PR名",
                "PR Author",
                "ブランチ",
                "モデル",
                "コスト (USD)",
                "処理時間",
                "ターン数",
                "コミット数",
                "ファイル変更数",
                "実行ステータス",
                "開始時刻",
                "終了時刻",
                "PRリンク",
            ],
        )

        # Write data rows
        for r in results:
            pr_number = r.get("pr_number", "N/A") or "N/A"
            pr_name = r.get("pr_name", "N/A") or "N/A"
            pr_author = r.get("pr_author", "N/A") or "N/A"
            branch = r.get("branch", "N/A") or "N/A"

            model = r.get("model", "N/A") or "N/A"
            if model != "N/A":
                model = model.replace(
                    "claude-sonnet-4-5-20250929",
                    "sonnet-4.5",
                )

            cost = r.get("total_cost_usd")
            cost_str = f"{cost:.4f}" if cost is not None else "N/A"

            duration_str = format_duration(r.get("duration_ms"))
            turns = r.get("num_turns", "N/A") or "N/A"
            total_commits = r.get("total_commits", "N/A") or "N/A"
            changed_files = r.get("changed_files", "N/A") or "N/A"
            status = r.get("status", "N/A") or "N/A"
            start_time = format_timestamp(r.get("start_time"))
            end_time = format_timestamp(r.get("end_time"))

            # Create PR link
            if pr_number != "N/A" and pr_number:
                pr_link = f"https://github.com/{repo}/pull/{pr_number}"
            else:
                pr_link = "N/A"

            writer.writerow(
                [
                    pr_number,
                    pr_name,
                    pr_author,
                    branch,
                    model,
                    cost_str,
                    duration_str,
                    turns,
                    total_commits,
                    changed_files,
                    status,
                    start_time,
                    end_time,
                    pr_link,
                ],
            )


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


@click.command()
@click.option(
    "--repo",
    default="retail-ai-inc/toppie",
    help="Repository name in format owner/repo",
)
@click.option(
    "--workflow",
    default="Claude Auto Review with Tracking",
    help="Workflow name",
)
@click.option(
    "--days",
    default=30,
    type=int,
    help="Number of days to look back",
)
@click.option(
    "--limit",
    default=1000,
    type=int,
    help="Maximum number of runs to fetch",
)
@click.option(
    "--csv-output",
    type=Path,
    default=Path("claude_review_report.csv"),
    help="CSV output file path",
)
@click.option(
    "--json-output",
    type=Path,
    default=Path("claude_metrics_output.json"),
    help="JSON output file path",
)
@click.option(
    "--no-csv",
    is_flag=True,
    help="Skip CSV report generation",
)
@click.option(
    "--no-json",
    is_flag=True,
    help="Skip JSON output",
)
def main(
    repo: str,
    workflow: str,
    days: int = 30,
    limit: int = 1000,
    csv_output: Path = Path("claude_review_report.csv"),
    json_output: Path = Path("claude_metrics_output.json"),
    no_csv: bool = False,
    no_json: bool = False,
) -> None:
    """Extract Claude Code metrics from GitHub Actions logs.

    Args:
        repo (str): Repository name in format owner/repo
        workflow (str): _description_
        days (int): Number of days to look back
        limit (int, optional): _description_. Defaults to 1000.
        csv_output (Path, optional): _description_. Defaults to Path("claude_review_report.csv").
        json_output (Path, optional): _description_. Defaults to Path("claude_metrics_output.json").
        no_csv (bool, optional): _description_. Defaults to False.
        no_json (bool, optional): _description_. Defaults to False.
    """
    logger.info(
        f"Fetching workflow runs for '{workflow}' "
        f"in repository '{repo}' (last {days} days)...",
    )

    runs = get_workflow_runs(workflow, limit, days, repo)
    logger.info(f"Found {len(runs)} runs in the last {days} days")

    results = process_runs(runs, repo)

    if not no_csv:
        generate_csv_report(results, csv_output, repo)
        logger.info(f"CSV report generated: {csv_output}")

    if not no_json:
        with Path(json_output).open("w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"JSON output saved: {json_output}")


if __name__ == "__main__":
    main()
