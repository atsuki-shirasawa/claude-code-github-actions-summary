<!-- @format -->

# Claude Metrics Extractor

GitHub Actions のログから Claude Code のメトリクスを抽出し、分析レポートを生成する Python ツールです。

## Overview

このツールは、GitHub Actions で実行された Claude Code によるコードレビューワークフローのログを解析し、以下の情報を抽出します：

- PR 番号と PR 名
- PR 作成者
- 使用されたモデル
- 実行コスト（USD）
- 処理時間
- ターン数（対話の回数）
- コミット数
- ファイル変更数
- 実行ステータス
- 開始・終了時刻

抽出したデータは CSV と JSON 形式で出力され、Claude Code の利用状況やコスト分析に活用できます。

## Project Structure

```
claude-code-github-actions-summary/
├── main.py                 # エントリーポイント（CLI コマンド）
├── src/
│   ├── __init__.py
│   ├── github_client.py    # GitHub API とワークフロー実行の取得
│   ├── log_parser.py       # ログの解析
│   ├── metrics_extractor.py # メトリクスの抽出ロジック
│   ├── processor.py        # 実行データの処理
│   ├── formatters.py       # データフォーマット
│   └── report_generator.py # CSV/JSON レポート生成
├── pyproject.toml          # プロジェクト設定と依存関係
└── README.md
```

### Main Modules

- **main.py**: CLI のエントリーポイント。Click を使用してコマンドライン引数を処理し、全体のワークフローを制御します。
- **github_client.py**: GitHub CLI (`gh`) を使用してワークフロー実行データとログを取得します。
- **log_parser.py**: GitHub Actions のログファイルを解析し、Claude Code のメトリクス情報を抽出します。
- **metrics_extractor.py**: ログから特定のメトリクス（コスト、ターン数、処理時間など）を抽出するロジックを実装します。
- **processor.py**: 複数のワークフロー実行を並列処理し、メトリクスデータを収集します。
- **formatters.py**: 抽出したデータを適切な形式にフォーマットします。
- **report_generator.py**: CSV および JSON 形式でレポートを生成します。

## Requirements

- Python 3.12 以上
- GitHub CLI (`gh`)がインストールされ、認証済みであること

## Technology Stack

### Runtime Dependencies

- **Click**: CLI フレームワーク。コマンドライン引数の処理とオプション管理を提供します。
- **Loguru**: シンプルで強力なロギングライブラリ。実行状況の可視化に使用します。

### Development Dependencies

- **Black**: Python コードフォーマッター（行長: 79）
- **Ruff**: 高速な Python リンター。複数のツール（pycodestyle, pyflakes, isort, pydocstyle など）を統合
- **mypy**: 静的型チェッカー。型アノテーションの検証に使用
- **tox**: テスト自動化ツール

## Installation

```bash
uv sync
```

インストール後、`gh` CLI が認証済みであることを確認してください：

```bash
# GitHub CLI の認証状態を確認
gh auth status

# 未認証の場合はログイン
gh auth login
```

## Usage

### Basic Usage

```bash
uv run main.py --repo owner/repo --workflow "Claude Auto Review with Tracking"
```

### Options

- `--repo`: リポジトリ名（`owner/repo`形式）
- `--workflow`: ワークフロー名
  - デフォルト: `Claude Auto Review with Tracking`
- `--days`: 過去何日分のログを取得するか
  - デフォルト: `30`
- `--limit`: 取得する最大実行数
  - デフォルト: `1000`
- `--csv-output`: CSV 出力ファイルのパス
  - デフォルト: `claude_review_report.csv`
- `--json-output`: JSON 出力ファイルのパス
  - デフォルト: `claude_metrics_output.json`
- `--no-csv`: CSV レポートの生成をスキップ
- `--no-json`: JSON 出力をスキップ

### Usage Examples

```bash
# 過去7日間のデータを抽出
uv run main.py --repo owner/repo --days 7

# CSVのみ出力
uv run main.py --repo owner/repo --no-json

# カスタム出力ファイル名を指定
uv run main.py --repo owner/repo --csv-output report.csv --json-output data.json

# 特定のワークフローを指定（デフォルトと異なる名前の場合）
uv run main.py --repo owner/repo --workflow "My Custom Workflow"

# 取得する実行数を制限
uv run main.py --repo owner/repo --limit 100
```

## Output Format

### CSV Format

CSV ファイルには以下のカラムが含まれます：

| #   | カラム名       | 説明                          |
| --- | -------------- | ----------------------------- |
| 1   | PR 番号        | プルリクエスト番号            |
| 2   | PR 名          | プルリクエストのタイトル      |
| 3   | PR Author      | プルリクエストの作成者        |
| 4   | ブランチ       | ブランチ名                    |
| 5   | モデル         | 使用された Claude Code モデル |
| 6   | コスト (USD)   | 実行コスト                    |
| 7   | 処理時間       | 処理時間（秒）                |
| 8   | ターン数       | 対話のターン数                |
| 9   | コミット数     | PR に含まれるコミット数       |
| 10  | ファイル変更数 | 変更されたファイル数          |
| 11  | 実行ステータス | ワークフローの実行結果        |
| 12  | 開始時刻       | 実行開始時刻                  |
| 13  | 終了時刻       | 実行終了時刻                  |
| 14  | PR リンク      | GitHub の PR へのリンク       |

```csv
PR番号,PR名,PR Author,ブランチ,モデル,コスト (USD),処理時間,ターン数,コミット数,ファイル変更数,実行ステータス,開始時刻,終了時刻,PRリンク
121,Release: Merge feature branch to main,sample-user,develop,sonnet-4.5,0.6942,207.302,32,57,70,success,2025-12-22 09:04:27,2025-12-22 09:08:27,https://github.com/sample-org/sample-repo/pull/121
120,feat: add error handling for API requests,sample-user,feature/add-error-handling,sonnet-4.5,0.4966,155.488,22,5,8,success,2025-12-22 08:50:26,2025-12-22 08:53:37,https://github.com/sample-org/sample-repo/pull/120
120,feat: add error handling for API requests,sample-user,feature/add-error-handling,sonnet-4.5,0.4577,146.525,25,4,8,success,2025-12-22 08:36:05,2025-12-22 08:39:04,https://github.com/sample-org/sample-repo/pull/120
119,feat(ui): enhance data display with table/code mode toggle,sample-user,feature/enhance-data-display,sonnet-4.5,0.3319,118.523,11,9,11,success,2025-12-22 00:27:23,2025-12-22 00:29:53,https://github.com/sample-org/sample-repo/pull/119
119,feat(ui): enhance data display with table/code mode toggle,sample-user,feature/enhance-data-display,sonnet-4.5,0.6898,208.952,30,8,11,success,2025-12-22 00:21:14,2025-12-22 00:25:14,https://github.com/sample-org/sample-repo/pull/119
...
```

### JSON Format

JSON ファイルには各実行の詳細なメトリクスが配列形式で保存されます。

```json
[
  {
    "run_id": "20426748554",
    "pr_name": "feat: add error handling for API requests",
    "pr_number": 120,
    "branch": "feature/add-error-handling",
    "status": "success",
    "model": "claude-sonnet-4-5-20250929",
    "total_cost_usd": 0.4965642999999999,
    "duration_ms": 155488,
    "num_turns": 22,
    "start_time": "2025-12-22T08:50:26.8545466Z",
    "end_time": "2025-12-22T08:53:37.7604735Z",
    "is_error": false,
    "pr_author": "sample-user",
    "total_commits": 5,
    "changed_files": 8
  },
  {
    "run_id": "20426440936",
    "pr_name": "feat: add error handling for API requests",
    "pr_number": 120,
    "branch": "feature/add-error-handling",
    "status": "success",
    "model": "claude-sonnet-4-5-20250929",
    "total_cost_usd": 0.4577244499999999,
    "duration_ms": 146525,
    "num_turns": 25,
    "start_time": "2025-12-22T08:36:05.7873997Z",
    "end_time": "2025-12-22T08:39:04.7201467Z",
    "is_error": false,
    "pr_author": "sample-user",
    "total_commits": 4,
    "changed_files": 8
  },
  ...
]
```

## Development

### Setup Development Environment

```bash
# 開発用依存関係を含めてインストール
uv sync --group dev

# コード品質チェック
uv run ruff check .
uv run mypy .
uv run black --check .

# フォーマット
uv run black .
uv run ruff check --fix .
```

### Test

```bash
# tox でテスト実行
uv run tox
```

## License

このプロジェクトは特定のライセンスが設定されていません。

## Contributing

バグ報告や機能リクエストは、GitHub の Issue でお願いします。
