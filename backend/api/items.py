"""
Items API
"""
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Body
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel

from backend.database import get_db
from backend.models import Item, Profile
from backend.schemas import ItemCreate, ItemUpdate, ItemResponse, ItemListResponse
from backend.config import BASE_DIR
from backend.prompts import get_system_prompt, get_gemini_prompt

router = APIRouter(prefix="/items", tags=["Items"])


@router.get("", response_model=ItemListResponse)
def get_items(
    search: Optional[str] = Query(None, description="商品名で検索"),
    hashtag: Optional[str] = Query(None, description="ハッシュタグで検索"),
    status_filter: Optional[str] = Query(None, description="投稿状況でフィルタ（未投稿/下書き/投稿済み/非公開）"),
    priority: Optional[int] = Query(None, ge=1, le=5, description="優先度でフィルタ（1-5）"),
    category: Optional[str] = Query(None, description="カテゴリでフィルタ"),
    limit: int = Query(100, ge=1, le=1000, description="取得件数"),
    offset: int = Query(0, ge=0, description="オフセット"),
    db: Session = Depends(get_db)
):
    """
    商品一覧を取得

    検索・フィルタ機能付き
    """
    # クエリの基本部分（ゴミ箱を除外）
    query = db.query(Item).filter(Item.deleted_at.is_(None))

    # 検索フィルタ
    if search:
        query = query.filter(Item.name.contains(search))

    # ハッシュタグフィルタ
    if hashtag:
        # #を含む場合と含まない場合の両方に対応
        search_tag = hashtag if hashtag.startswith('#') else f'#{hashtag}'
        query = query.filter(Item.description.contains(search_tag))

    # 投稿状況フィルタ
    if status_filter:
        query = query.filter(Item.status == status_filter)

    # 優先度フィルタ
    if priority:
        query = query.filter(Item.priority == priority)

    # カテゴリフィルタ
    if category:
        query = query.filter(Item.category == category)

    # 総件数を取得
    total = query.count()

    # 優先度順、更新日時順でソート
    query = query.order_by(Item.priority.desc(), Item.updated_at.desc())

    # ページネーション
    items = query.offset(offset).limit(limit).all()

    return ItemListResponse(total=total, items=items)


@router.get("/trash", response_model=ItemListResponse)
def get_trash_items(
    limit: int = Query(100, ge=1, le=1000, description="取得件数"),
    offset: int = Query(0, ge=0, description="オフセット"),
    db: Session = Depends(get_db)
):
    """
    ゴミ箱の商品一覧を取得（削除日時が新しい順）
    """
    query = db.query(Item).filter(Item.deleted_at.isnot(None))

    # 総件数を取得
    total = query.count()

    # 削除日時の新しい順でソート
    query = query.order_by(Item.deleted_at.desc())

    # ページネーション
    items = query.offset(offset).limit(limit).all()

    return ItemListResponse(total=total, items=items)


@router.get("/stats/summary")
def get_stats(db: Session = Depends(get_db)):
    """
    統計情報を取得（ゴミ箱を除く）
    """
    total_items = db.query(Item).filter(Item.deleted_at.is_(None)).count()
    unpublished_count = db.query(Item).filter(Item.status == "未投稿", Item.deleted_at.is_(None)).count()
    published_count = db.query(Item).filter(Item.status == "投稿済み", Item.deleted_at.is_(None)).count()
    draft_count = db.query(Item).filter(Item.status == "下書き", Item.deleted_at.is_(None)).count()
    trash_count = db.query(Item).filter(Item.deleted_at.isnot(None)).count()

    return {
        "total_items": total_items,
        "unpublished_count": unpublished_count,
        "published_count": published_count,
        "draft_count": draft_count,
        "trash_count": trash_count,
    }


@router.get("/{item_id}", response_model=ItemResponse)
def get_item(item_id: int, db: Session = Depends(get_db)):
    """
    商品詳細を取得
    """
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found"
        )

    return item


@router.post("", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(item_data: ItemCreate, db: Session = Depends(get_db)):
    """
    商品を作成
    """
    # プロフィールが存在するか確認
    profile = db.query(Profile).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile not found. Please create a profile first."
        )

    # 商品を作成
    item_dict = item_data.model_dump()
    item = Item(**item_dict, profile_id=profile.id)

    # unique_idがなければ生成
    if not item.unique_id:
        item.unique_id = str(uuid.uuid4())

    db.add(item)
    db.commit()
    db.refresh(item)

    return item


@router.put("/{item_id}", response_model=ItemResponse)
def update_item(
    item_id: int,
    item_data: ItemUpdate,
    db: Session = Depends(get_db)
):
    """
    商品を更新
    """
    # 商品を取得
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found"
        )

    # 更新（None以外のフィールドのみ）
    update_data = item_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(item, key, value)

    db.commit()
    db.refresh(item)

    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    """
    商品をゴミ箱へ移動（ソフトデリート）
    """
    # 商品を取得
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found"
        )

    # ゴミ箱へ移動（deleted_atに現在時刻を設定）
    item.deleted_at = datetime.utcnow()
    db.commit()

    return None


@router.post("/{item_id}/restore", response_model=ItemResponse)
def restore_item(item_id: int, db: Session = Depends(get_db)):
    """
    ゴミ箱から商品を復元
    """
    # 商品を取得
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found"
        )

    if item.deleted_at is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Item is not in trash"
        )

    # 復元（deleted_atをNULLに）
    item.deleted_at = None
    db.commit()
    db.refresh(item)

    return item


@router.delete("/{item_id}/permanent", status_code=status.HTTP_204_NO_CONTENT)
def delete_item_permanent(item_id: int, db: Session = Depends(get_db)):
    """
    商品を完全削除（物理削除）
    """
    # 商品を取得
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found"
        )

    # 画像がある場合は削除
    if item.photo_path:
        file_path = BASE_DIR / item.photo_path
        if file_path.exists():
            try:
                os.remove(file_path)
            except Exception:
                pass  # 削除失敗しても続行

    # 物理削除
    db.delete(item)
    db.commit()

    return None


@router.post("/{item_id}/upload-image")
async def upload_image(
    item_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    商品画像をアップロード
    """
    # 商品を取得
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found"
        )

    # 画像ファイルかどうかチェック
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be an image"
        )

    # 画像保存ディレクトリ
    images_dir = BASE_DIR / "images"
    images_dir.mkdir(exist_ok=True)

    # ファイル名を生成（UUID + 元の拡張子）
    file_extension = Path(file.filename).suffix
    filename = f"{uuid.uuid4()}{file_extension}"
    file_path = images_dir / filename

    # ファイルを保存
    try:
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save image: {str(e)}"
        )

    # 既存の画像があれば削除
    if item.photo_path:
        old_file_path = BASE_DIR / item.photo_path
        if old_file_path.exists():
            try:
                os.remove(old_file_path)
            except Exception:
                pass  # 削除失敗しても続行

    # データベースを更新
    item.has_photo = True
    item.photo_path = f"images/{filename}"
    db.commit()
    db.refresh(item)

    return {
        "message": "Image uploaded successfully",
        "photo_path": item.photo_path,
        "item": item
    }


@router.delete("/{item_id}/image")
def delete_image(
    item_id: int,
    db: Session = Depends(get_db)
):
    """
    商品画像を削除
    """
    # 商品を取得
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found"
        )

    # 画像がない場合
    if not item.photo_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No image found for this item"
        )

    # ファイルを削除
    file_path = BASE_DIR / item.photo_path
    if file_path.exists():
        try:
            os.remove(file_path)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete image: {str(e)}"
            )

    # データベースを更新
    item.has_photo = False
    item.photo_path = None
    db.commit()
    db.refresh(item)

    return {"message": "Image deleted successfully", "item": item}


class MarkPostedRequest(BaseModel):
    posted_at: str           # ISO 8601形式 例: "2026-05-20T10:30:00+09:00"
    room_url: Optional[str] = None  # 投稿後のROOM URL（automation から渡す）


@router.patch("/{item_id}/mark-posted", response_model=ItemResponse)
def mark_posted(
    item_id: int,
    request: MarkPostedRequest,
    db: Session = Depends(get_db)
):
    """
    商品を投稿済みとしてマーク

    automation から投稿完了通知を受けて呼び出す。
    status を「投稿済み」に更新し、posted_at_history に追記（最大3件）。
    room_url が渡された場合はROOM投稿ページURLを保存する。
    """
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found"
        )

    item.status = "投稿済み"

    history = list(item.posted_at_history or [])
    history.append(request.posted_at)
    item.posted_at_history = history[-3:]  # 最大3件

    if request.room_url:
        item.room_url = request.room_url

    db.commit()
    db.refresh(item)

    return item


@router.patch("/{item_id}/mark-unpublished", response_model=ItemResponse)
def mark_unpublished(
    item_id: int,
    db: Session = Depends(get_db)
):
    """
    商品を非公開としてマーク

    automation から売り切れ・URL無効の検出時に呼び出す。
    status を「非公開」に更新し、room_url をクリアする。
    """
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found"
        )

    item.status = "非公開"
    item.room_url = None

    db.commit()
    db.refresh(item)

    return item


@router.patch("/{item_id}/mark-available", response_model=ItemResponse)
def mark_available(
    item_id: int,
    db: Session = Depends(get_db)
):
    """
    商品を再投稿可能な状態に戻す（ローテーション用）

    オリジナル写真投稿のローテーション削除後に automation から呼び出す。
    status を「未投稿」に戻し、room_url をクリアする（→ ready-to-post に再出現）。
    """
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found"
        )

    item.status = "未投稿"
    item.room_url = None

    db.commit()
    db.refresh(item)

    return item


class GenerateDescriptionRequest(BaseModel):
    """商品紹介文生成リクエスト"""
    item: Dict[str, Any]
    profile: Dict[str, Any]
    provider: str = "openai"  # openai, gemini, perplexity, claude


@router.post("/generate-description")
async def generate_description(
    request: GenerateDescriptionRequest,
    db: Session = Depends(get_db)
):
    """
    AI で商品紹介文を生成

    商品情報とプロフィール設定を基に、AIを使って商品紹介文を生成します。
    """
    item_data = request.item
    profile_data = request.profile
    provider = request.provider

    # AI連携が有効かチェック
    if not profile_data.get("ai_enabled"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="AI integration is not enabled. Please enable it in settings."
        )

    # プロバイダーに応じてAPIキーとモデル名を取得
    if provider == "openai":
        api_key = profile_data.get("ai_provider_openai_key")
        model = profile_data.get("ai_provider_openai_model")
        if not api_key or not model:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OpenAI API key or model name is not configured."
            )
    elif provider == "gemini":
        api_key = profile_data.get("ai_provider_gemini_key")
        model = profile_data.get("ai_provider_gemini_model")
        if not api_key or not model:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google Gemini API key or model name is not configured."
            )
    elif provider == "perplexity":
        api_key = profile_data.get("ai_provider_perplexity_key")
        model = profile_data.get("ai_provider_perplexity_model")
        if not api_key or not model:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Perplexity API key or model name is not configured."
            )
    elif provider == "claude":
        api_key = profile_data.get("ai_provider_claude_key")
        model = profile_data.get("ai_provider_claude_model")
        if not api_key or not model:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Claude API key or model name is not configured."
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported AI provider: {provider}"
        )

    # トーン&マナーを取得
    tone_manner = profile_data.get("tone_manner", "親しみやすい")

    # プロンプトを構築
    prompt = _build_description_prompt(item_data, profile_data)

    # AI APIを呼び出し
    try:
        if provider == "openai":
            description = await _call_openai(api_key, model, prompt, tone_manner)
        elif provider == "gemini":
            description = await _call_gemini(api_key, model, prompt, tone_manner)
        elif provider == "perplexity":
            description = await _call_perplexity(api_key, model, prompt, tone_manner)
        elif provider == "claude":
            description = await _call_claude(api_key, model, prompt, tone_manner)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate description: {str(e)}"
        )

    # オリジナル写真の場合、ハッシュタグを自動付与
    if item_data.get("is_original_photo"):
        description = description.rstrip()
        if not description.endswith("#オリジナル写真"):
            description += " #オリジナル写真"

    return {"description": description, "provider": provider, "model": model}


async def _call_openai(api_key: str, model: str, prompt: str, tone_manner: str) -> str:
    """
    OpenAI APIを呼び出して商品紹介文を生成
    """
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=api_key)

    # トーン&マナーに応じたシステムプロンプトを取得
    system_prompt = get_system_prompt(tone_manner, is_perplexity=False)

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=500
        )

        description = response.choices[0].message.content.strip()
        return description

    except Exception as e:
        raise Exception(f"OpenAI API error: {str(e)}")


async def _call_gemini(api_key: str, model: str, prompt: str, tone_manner: str) -> str:
    """
    Google Gemini APIを呼び出して商品紹介文を生成
    """
    import google.generativeai as genai

    try:
        genai.configure(api_key=api_key)

        # トーン&マナーに応じたシステムプロンプトとユーザープロンプトを結合
        full_prompt = get_gemini_prompt(tone_manner, prompt)

        model_instance = genai.GenerativeModel(model)
        response = model_instance.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=500,
            )
        )

        description = response.text.strip()
        return description

    except Exception as e:
        raise Exception(f"Google Gemini API error: {str(e)}")


async def _call_perplexity(api_key: str, model: str, prompt: str, tone_manner: str) -> str:
    """
    Perplexity APIを呼び出して商品紹介文を生成

    PerplexityはOpenAI互換APIを提供しているため、OpenAIクライアントを使用
    """
    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://api.perplexity.ai"
    )

    # トーン&マナーに応じたシステムプロンプトを取得(Perplexity専用ルール付き)
    system_prompt = get_system_prompt(tone_manner, is_perplexity=True)

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=500
        )

        description = response.choices[0].message.content.strip()
        return description

    except Exception as e:
        raise Exception(f"Perplexity API error: {str(e)}")


async def _call_claude(api_key: str, model: str, prompt: str, tone_manner: str) -> str:
    """
    Claude APIを呼び出して商品紹介文を生成
    """
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=api_key)

    # トーン&マナーに応じたシステムプロンプトを取得
    system_prompt = get_system_prompt(tone_manner, is_perplexity=False)

    try:
        response = await client.messages.create(
            model=model,
            max_tokens=500,
            temperature=0.7,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        description = response.content[0].text.strip()
        return description

    except Exception as e:
        raise Exception(f"Claude API error: {str(e)}")


def _normalize_comma_separated_text(text: str) -> str:
    """
    カンマ・スペース区切りのテキストを正規化

    全角カンマ、半角カンマ、全角スペース、半角スペースで分割し、
    カンマ区切りに統一して返す
    """
    import re

    if not text or not text.strip():
        return '未設定'

    # 複数の区切り文字で分割（全角カンマ、半角カンマ、全角スペース、半角スペース）
    items = re.split(r'[、,\s　]+', text.strip())

    # 空の要素を除去し、前後の空白をトリム
    items = [item.strip() for item in items if item.strip()]

    if not items:
        return '未設定'

    # カンマ区切りで結合
    return '、'.join(items)


def _build_description_prompt(item_data: Dict[str, Any], profile_data: Dict[str, Any]) -> str:
    """
    商品紹介文生成用のプロンプトを構築
    """
    # ROOMテーマとNGワードを正規化
    room_theme = _normalize_comma_separated_text(profile_data.get('room_theme', ''))
    ng_words = _normalize_comma_separated_text(profile_data.get('ng_words', ''))
    if ng_words == '未設定':
        ng_words = 'なし'

    prompt = f"""以下の情報を基に、楽天ROOMに投稿する商品紹介文を生成してください。

## 商品情報
- 商品名: {item_data.get('name', '未設定')}
- カテゴリ: {item_data.get('category', '未設定')}
- ブランド・型番: {item_data.get('brand_model', '未設定')}
- お気に入りポイント: {item_data.get('favorite_points', '未設定')}
- 使用シーン: {item_data.get('usage_scene', '未設定')}
- 使用頻度: {item_data.get('frequency', '未設定')}
- 季節性: {item_data.get('seasonality', '未設定')}

## プロフィール・投稿スタイル
- ROOMの方向性: {profile_data.get('room_direction', '未設定')}
- ターゲット層: {profile_data.get('target_audience', '未設定')}
- ROOMテーマ: {room_theme}
- トーン&マナー: {profile_data.get('tone_manner', '親しみやすい')}
- 投稿スタイル: {profile_data.get('posting_style', '未設定')}
- 使いたくない言葉: {ng_words}

上記の情報を踏まえ、魅力的で読みやすい商品紹介文を200-300文字程度で生成してください。
"""

    return prompt
