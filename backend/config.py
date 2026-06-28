"""
設定ファイル
"""
import os
from pathlib import Path

# プロジェクトルート
BASE_DIR = Path(__file__).resolve().parent.parent

# データディレクトリ
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# データベースパス
DATABASE_PATH = DATA_DIR / "rakuten_room.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# CORS設定
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
    "file://",  # ローカルHTMLファイルからのアクセス
    "null",     # ローカルHTMLファイルからのアクセス（Origin: null）
]

# API設定
API_PREFIX = "/api"
API_TITLE = "楽天ROOMアイテムマネージャー API"
API_VERSION = "0.1.0"
API_DESCRIPTION = """
楽天ROOMに投稿する商品を効率的に管理するためのAPI

## 主要機能

* **Profile API**: プロフィール管理（CRUD）
* **Items API**: 商品管理（CRUD、検索、フィルタ）
* **Export API**: データエクスポート（JSON、CSV）
"""
