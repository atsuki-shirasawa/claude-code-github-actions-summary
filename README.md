<!-- @format -->

# Claude Metrics Extractor

GitHub Actions のログから Claude Code のメトリクスを抽出し、分析レポートを生成する Python ツールです。

## 概要

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

## 必要要件

- Python 3.12 以上
- GitHub CLI (`gh`)がインストールされ、認証済みであること

## インストール

```bash
# uvを使用する場合（推奨）
uv sync

# pipを使用する場合
pip install -e .
```

## 使い方

### 基本的な使用方法

```bash
python main.py --repo owner/repo --workflow "Claude Auto Review with Tracking"
```

### オプション

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

### 使用例

```bash
# 過去7日間のデータを抽出
python main.py --repo myorg/myrepo --days 7

# CSVのみ出力
python main.py --repo myorg/myrepo --no-json

# カスタム出力ファイル名を指定
python main.py --repo myorg/myrepo --csv-output report.csv --json-output data.json
```

## 出力形式

### CSV 形式

CSV ファイルには以下のカラムが含まれます：

| カラム名       | 説明                          |
| -------------- | ----------------------------- |
| PR 番号        | プルリクエスト番号            |
| PR 名          | プルリクエストのタイトル      |
| PR Author      | プルリクエストの作成者        |
| ブランチ       | ブランチ名                    |
| モデル         | 使用された Claude Code モデル |
| コスト (USD)   | 実行コスト                    |
| 処理時間       | 処理時間（秒）                |
| ターン数       | 対話のターン数                |
| コミット数     | PR に含まれるコミット数       |
| ファイル変更数 | 変更されたファイル数          |
| 実行ステータス | ワークフローの実行結果        |
| 開始時刻       | 実行開始時刻                  |
| 終了時刻       | 実行終了時刻                  |
| PR リンク      | GitHub の PR へのリンク       |

### JSON 形式

JSON ファイルには各実行の詳細なメトリクスが配列形式で保存されます。

## 開発

### 開発環境のセットアップ

```bash
# 開発用依存関係を含めてインストール
uv sync --all-extras

# コード品質チェック
ruff check .
mypy .
black --check .

# フォーマット
black .
ruff check --fix .
```

### テスト

```bash
# tox でテスト実行
tox
```

## ライセンス

このプロジェクトは特定のライセンスが設定されていません。

## 貢献

バグ報告や機能リクエストは、GitHub の Issue でお願いします。
