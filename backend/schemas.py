"""
Pydanticスキーマ定義
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ========================================
# Profile スキーマ
# ========================================

class ProfileBase(BaseModel):
    """プロフィール基底スキーマ"""
    room_name: str = Field(..., min_length=1, max_length=255)
    owner_name: Optional[str] = None
    room_id: Optional[str] = None
    target_audience: Optional[str] = None
    room_direction: Optional[str] = None
    room_theme: Optional[str] = None
    tone_manner: Optional[str] = None
    posting_style: Optional[str] = None
    ng_words: Optional[str] = None

    # AI連携設定
    ai_enabled: bool = False
    ai_provider_openai_key: Optional[str] = None
    ai_provider_openai_model: Optional[str] = None
    ai_provider_gemini_key: Optional[str] = None
    ai_provider_gemini_model: Optional[str] = None
    ai_provider_perplexity_key: Optional[str] = None
    ai_provider_perplexity_model: Optional[str] = None
    ai_provider_claude_key: Optional[str] = None
    ai_provider_claude_model: Optional[str] = None


class ProfileCreate(ProfileBase):
    """プロフィール作成スキーマ"""
    pass


class ProfileUpdate(BaseModel):
    """プロフィール更新スキーマ（全フィールド任意）"""
    room_name: Optional[str] = Field(None, min_length=1, max_length=255)
    owner_name: Optional[str] = None
    room_id: Optional[str] = None
    target_audience: Optional[str] = None
    room_direction: Optional[str] = None
    room_theme: Optional[str] = None
    tone_manner: Optional[str] = None
    posting_style: Optional[str] = None
    ng_words: Optional[str] = None

    # AI連携設定
    ai_enabled: Optional[bool] = None
    ai_provider_openai_key: Optional[str] = None
    ai_provider_openai_model: Optional[str] = None
    ai_provider_gemini_key: Optional[str] = None
    ai_provider_gemini_model: Optional[str] = None
    ai_provider_perplexity_key: Optional[str] = None
    ai_provider_perplexity_model: Optional[str] = None
    ai_provider_claude_key: Optional[str] = None
    ai_provider_claude_model: Optional[str] = None


class ProfileResponse(ProfileBase):
    """プロフィールレスポンススキーマ"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ========================================
# Item スキーマ
# ========================================

class ItemBase(BaseModel):
    """商品基底スキーマ"""
    name: str = Field(..., min_length=1, max_length=500)
    unique_id: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    brand_model: Optional[str] = None
    usage_scene: Optional[str] = None
    frequency: Optional[str] = None
    favorite_points: Optional[str] = None
    seasonality: Optional[str] = "通年"
    has_photo: bool = False
    photo_path: Optional[str] = None
    is_original_photo: bool = False
    has_item: bool = False
    priority: int = Field(default=3, ge=1, le=5)
    rakuten_url: Optional[str] = None
    room_url: Optional[str] = None
    memo: Optional[str] = None
    description: Optional[str] = None
    status: str = Field(default="未投稿")
    posted_at_history: Optional[List[str]] = None
    deleted_at: Optional[datetime] = None


class ItemCreate(ItemBase):
    """商品作成スキーマ"""
    pass


class ItemUpdate(BaseModel):
    """商品更新スキーマ（全フィールド任意）"""
    name: Optional[str] = Field(None, min_length=1, max_length=500)
    category: Optional[str] = None
    sub_category: Optional[str] = None
    brand_model: Optional[str] = None
    usage_scene: Optional[str] = None
    frequency: Optional[str] = None
    favorite_points: Optional[str] = None
    seasonality: Optional[str] = None
    has_photo: Optional[bool] = None
    photo_path: Optional[str] = None
    is_original_photo: Optional[bool] = None
    has_item: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    rakuten_url: Optional[str] = None
    room_url: Optional[str] = None
    memo: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    posted_at_history: Optional[List[str]] = None
    deleted_at: Optional[datetime] = None


class ItemResponse(ItemBase):
    """商品レスポンススキーマ"""
    id: int
    profile_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ItemListResponse(BaseModel):
    """商品一覧レスポンススキーマ"""
    total: int
    items: List[ItemResponse]


# ========================================
# Export スキーマ
# ========================================

class ExportResponse(BaseModel):
    """エクスポートレスポンススキーマ"""
    export_version: str = "1.0"
    exported_at: datetime
    profile: Optional[ProfileResponse] = None
    items: List[ItemResponse]
