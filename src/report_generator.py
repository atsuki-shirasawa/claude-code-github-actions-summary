"""CSV report generation utilities."""

import csv
from pathlib import Path

from .formatters import format_duration, format_timestamp


def generate_csv_report(
    results: list[dict],
    output_file: Path,
    repo: str,
) -> None:
    """Generate a CSV report from the results.

    Args:
        results: List of result dictionaries
        output_file: Output file path
        repo: Repository name (owner/repo)
    """
    with output_file.open("w", encoding="utf-8", newline="") as f:
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
