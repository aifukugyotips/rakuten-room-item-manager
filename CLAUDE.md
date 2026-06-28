# CLAUDE.md

このファイルは、[Claude Code](https://claude.ai/code) でこのリポジトリを扱う際のガイドです。

## プロジェクト概要

楽天ROOMに投稿する商品を管理する個人向けWebツール。

- **バックエンド**: FastAPI + SQLAlchemy + SQLite
- **フロントエンド**: Alpine.js + TailwindCSS（CDN利用、ビルド不要）
- **依存管理**: Poetry
- 詳細は [README.md](./README.md) を参照

## 主要コマンド

```bash
# 依存インストール
poetry install

# DB初期化（初回のみ）
poetry run python scripts/init_db.py

# サーバー起動
./scripts/start.sh
# または
poetry run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# テスト実行
poetry run pytest

# テスト（カバレッジなし、高速）
poetry run pytest --no-cov -q

# フォーマット・Lint
poetry run black backend tests
poetry run ruff check backend tests
```

## ディレクトリ構成

```
backend/        # FastAPI アプリケーション
  api/          # APIルーター（profile, items, export, ai）
  models.py     # SQLAlchemy モデル
  schemas.py    # Pydantic スキーマ
  prompts.py    # AI生成用プロンプト
frontend/       # Alpine.js フロントエンド
scripts/        # 起動・初期化スクリプト
tests/          # pytest テスト
data/           # SQLite DBファイル（gitignore）
images/         # アップロード画像（gitignore）
```

## コーディング方針

- **コメント**: 必要最小限。日本語OK
- **型ヒント**: バックエンドは可能な限り付与
- **エラーハンドリング**: FastAPIの `HTTPException` を使用
- **テスト**: 新機能・バグ修正には対応するテストを追加

## 注意事項

- 個人情報・APIキー・実データをコミットしないこと
- `data/*.db`、`images/`、`.env` は `.gitignore` で除外済み
- AI連携機能を変更する場合は `backend/api/ai.py` と `backend/prompts.py` の両方を確認
