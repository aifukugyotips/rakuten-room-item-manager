"""
SQLAlchemyモデル定義
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship

from backend.database import Base


class Profile(Base):
    """
    プロフィールモデル
    """
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    room_name = Column(String(255), nullable=False)
    owner_name = Column(String(255), nullable=True)
    room_id = Column(String(100), nullable=True)
    target_audience = Column(Text, nullable=True)
    room_direction = Column(Text, nullable=True)
    room_theme = Column(Text, nullable=True)
    tone_manner = Column(String(100), nullable=True)
    posting_style = Column(Text, nullable=True)
    ng_words = Column(Text, nullable=True)  # カンマ区切りまたはJSON

    # AI連携設定
    ai_enabled = Column(Boolean, default=False, nullable=False)
    ai_provider_openai_key = Column(String(500), nullable=True)
    ai_provider_openai_model = Column(String(100), nullable=True)
    ai_provider_gemini_key = Column(String(500), nullable=True)
    ai_provider_gemini_model = Column(String(100), nullable=True)
    ai_provider_perplexity_key = Column(String(500), nullable=True)
    ai_provider_perplexity_model = Column(String(100), nullable=True)
    ai_provider_claude_key = Column(String(500), nullable=True)
    ai_provider_claude_model = Column(String(100), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # リレーション
    items = relationship("Item", back_populates="profile", cascade="all, delete-orphan")


class Item(Base):
    """
    商品モデル
    """
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(Integer, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    unique_id = Column(String(36), unique=True, nullable=True)

    # 基本情報
    status = Column(String(50), default="未投稿", nullable=False)  # 未投稿/下書き/投稿済み/非公開
    name = Column(String(500), nullable=False)
    category = Column(String(100), nullable=True)
    sub_category = Column(String(100), nullable=True)
    brand_model = Column(String(255), nullable=True)

    # 使用状況
    usage_scene = Column(Text, nullable=True)
    frequency = Column(String(50), nullable=True)  # 毎日/週2-3回/月1-2回/年数回
    favorite_points = Column(Text, nullable=True)
    seasonality = Column(String(50), nullable=True)  # 通年/春/夏/秋/冬/春夏/秋冬

    # 画像
    has_photo = Column(Boolean, default=False, nullable=False)
    photo_path = Column(String(500), nullable=True)
    is_original_photo = Column(Boolean, default=False, nullable=False)

    # 所持状況
    has_item = Column(Boolean, default=False, nullable=False)

    # 投稿設定
    priority = Column(Integer, default=3, nullable=False)  # 1(低) ~ 5(高)
    rakuten_url = Column(String(1000), nullable=True)
    room_url = Column(String(1000), nullable=True)
    memo = Column(Text, nullable=True)
    description = Column(Text, nullable=True)  # 商品紹介文

    # タイムスタンプ
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    posted_at_history = Column(JSON, nullable=True)
    deleted_at = Column(DateTime, nullable=True)  # ゴミ箱（ソフトデリート）

    # リレーション
    profile = relationship("Profile", back_populates="items")
