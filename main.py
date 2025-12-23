"""Extract Claude Code metrics from GitHub Actions logs."""

import json
from pathlib import Path

import click
from loguru import logger

from src.github_client import get_workflow_runs
from src.processor import process_runs
from src.report_generator import generate_csv_report


@click.command()
@click.option(
    "--repo",
    type=str,
    required=True,
    help="Repository name in format owner/repo",
)
@click.option(
    "--workflow",
    type=str,
    default="Claude Auto Review with Tracking",
    help="Workflow name",
)
@click.option(
    "--days",
    type=int,
    default=30,
    help="Number of days to look back",
)
@click.option(
    "--limit",
    type=int,
    default=1000,
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
        workflow (str): Workflow name
        days (int): Number of days to look back
        limit (int, optional): \
            Maximum number of runs to fetch. Defaults to 1000.
        csv_output (Path, optional): \
            CSV output file path. Defaults to Path("claude_review_report.csv").
        json_output (Path, optional): \
            JSON output file path. Defaults to Path("claude_metrics_output.json").
        no_csv (bool, optional): \
            Skip CSV report generation. Defaults to False.
        no_json (bool, optional): \
            Skip JSON output. Defaults to False.
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
        logger.info(f"CSV report generated: {csv_output.as_posix()}")

    if not no_json:
        with json_output.open("w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"JSON output saved: {json_output.as_posix()}")


if __name__ == "__main__":
    main()
