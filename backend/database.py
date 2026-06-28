"""
データベース接続設定
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from backend.config import DATABASE_URL

# SQLAlchemyエンジン
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite用
    echo=True,  # SQLログを出力（開発時）
)

# セッションローカル
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ベースクラス
Base = declarative_base()


# 依存性注入用のDB取得関数
def get_db():
    """
    FastAPIの依存性注入でDBセッションを取得
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
