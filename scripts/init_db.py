"""
データベース初期化スクリプト
"""
import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.database import engine, Base
from backend.models import Profile, Item
from backend.config import DATABASE_PATH


def init_database():
    """
    データベースを初期化する
    """
    print(f"📦 データベース初期化開始: {DATABASE_PATH}")

    # データベースファイルが既に存在する場合は警告
    if DATABASE_PATH.exists():
        print(f"⚠️  データベースファイルが既に存在します: {DATABASE_PATH}")
        response = input("既存のデータベースを削除して初期化しますか？ (y/N): ")
        if response.lower() != 'y':
            print("❌ 初期化をキャンセルしました")
            return

        # 既存のデータベースを削除
        DATABASE_PATH.unlink()
        print(f"🗑️  既存のデータベースを削除しました")

    # テーブル作成
    Base.metadata.create_all(bind=engine)

    print(f"✅ データベースを初期化しました")
    print(f"📍 データベースパス: {DATABASE_PATH}")
    print(f"📋 作成されたテーブル:")
    for table in Base.metadata.sorted_tables:
        print(f"  - {table.name}")


if __name__ == "__main__":
    init_database()
