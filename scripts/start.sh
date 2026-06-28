#!/bin/bash
set -e

echo "🚀 楽天ROOMアイテムマネージャー起動中..."

# データベース初期化（初回のみ）
if [ ! -f "data/rakuten_room.db" ]; then
    echo "📦 データベース初期化..."
    poetry run python scripts/init_db.py
fi

# サーバー起動
echo "🌐 サーバー起動: http://localhost:8000"
echo "📚 APIドキュメント: http://localhost:8000/docs"
echo ""
poetry run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
