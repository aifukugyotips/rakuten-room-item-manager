"""
Export API
"""
import csv
import io
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, Query, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Profile, Item
from backend.schemas import ExportResponse

router = APIRouter(prefix="/export", tags=["Export"])


@router.get("/json", response_model=ExportResponse)
def export_json(db: Session = Depends(get_db)):
    """
    全データをJSON形式でエクスポート

    オートメーションツールとの連携用
    """
    # プロフィールを取得
    profile = db.query(Profile).first()

    # 全商品を取得
    items = db.query(Item).order_by(Item.priority.desc(), Item.created_at.desc()).all()

    return ExportResponse(
        export_version="1.0",
        exported_at=datetime.utcnow(),
        profile=profile,
        items=items
    )


@router.get("/csv")
def export_csv(db: Session = Depends(get_db)):
    """
    全商品データをCSV形式でエクスポート
    """
    # 全商品を取得
    items = db.query(Item).order_by(Item.priority.desc(), Item.created_at.desc()).all()

    # CSV文字列を作成
    output = io.StringIO()
    writer = csv.writer(output)

    # ヘッダー行
    writer.writerow([
        'ID', 'Unique ID', '商品名', 'カテゴリ', 'サブカテゴリ', 'ブランド・型番',
        '用途・シーン', '使用頻度', '気に入っているポイント', '季節性',
        '画像あり', '画像パス', 'オリジナル写真', '所持している',
        '優先度', '投稿状況', '楽天市場URL', 'ROOM URL', '商品紹介文', 'メモ',
        '登録日時', '更新日時', '投稿日時'
    ])

    # データ行
    for item in items:
        writer.writerow([
            item.id,
            item.unique_id or '',
            item.name,
            item.category or '',
            item.sub_category or '',
            item.brand_model or '',
            item.usage_scene or '',
            item.frequency or '',
            item.favorite_points or '',
            item.seasonality or '',
            '1' if item.has_photo else '0',
            item.photo_path or '',
            '1' if item.is_original_photo else '0',
            '1' if item.has_item else '0',
            item.priority,
            item.status,
            item.rakuten_url or '',
            item.room_url or '',
            item.description or '',
            item.memo or '',
            item.created_at.isoformat() if item.created_at else '',
            item.updated_at.isoformat() if item.updated_at else '',
            item.posted_at_history[0] if item.posted_at_history and len(item.posted_at_history) > 0 else '',
        ])

    # CSVファイルとして返す
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=rakuten_room_items_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )


@router.get("/items/ready-to-post")
def export_ready_to_post(
    limit: int = Query(10, ge=1, le=100, description="取得件数"),
    min_priority: int = Query(1, ge=1, le=5, description="最低優先度"),
    require_photo: bool = Query(False, description="画像ありのみ"),
    require_description: bool = Query(False, description="紹介文ありのみ"),
    original_photo_first: bool = Query(False, description="オリジナル写真を先頭に"),
    original_photo_only: bool = Query(False, description="is_original_photo=True のみ"),
    include_posted: bool = Query(False, description="投稿済みも含める（ローテーション再投稿用）"),
    db: Session = Depends(get_db)
):
    """
    投稿準備済み商品を取得

    オートメーションツール連携用。
    優先度が高い順に未投稿の商品を取得。
    include_posted=true にすると投稿済み商品も返す（ローテーション再投稿用）。
    """
    statuses = ["未投稿", "投稿済み"] if include_posted else ["未投稿"]

    query = (
        db.query(Item)
        .filter(Item.status.in_(statuses))
        .filter(Item.deleted_at.is_(None))
        .filter(Item.priority >= min_priority)
    )

    if require_photo:
        query = query.filter(Item.has_photo == True)

    if require_description:
        query = query.filter(Item.description.isnot(None), Item.description != "")

    if original_photo_only:
        query = query.filter(Item.is_original_photo == True)

    if original_photo_first:
        query = query.order_by(
            Item.is_original_photo.desc(),
            Item.priority.desc(),
            Item.updated_at.asc(),
        )
    else:
        query = query.order_by(Item.priority.desc(), Item.updated_at.asc())

    items = query.limit(limit).all()

    return {
        "count": len(items),
        "items": [
            {
                "id": item.id,
                "name": item.name,
                "category": item.category,
                "priority": item.priority,
                "favorite_points": item.favorite_points,
                "description": item.description,
                "rakuten_url": item.rakuten_url,
                "has_photo": item.has_photo,
                "photo_path": item.photo_path,
                "is_original_photo": item.is_original_photo,
                "has_item": item.has_item,
                "room_url": item.room_url,
                "status": item.status,
            }
            for item in items
        ]
    }


@router.post("/csv/import")
async def import_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    CSV形式で商品データをインポート
    """
    # プロフィールが存在するか確認
    profile = db.query(Profile).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile not found. Please create a profile first."
        )

    # CSVファイルを読み込み
    contents = await file.read()
    decoded = contents.decode('utf-8')
    reader = csv.DictReader(io.StringIO(decoded))

    imported_count = 0
    skipped_count = 0
    errors = []

    for row_num, row in enumerate(reader, start=2):  # ヘッダーの次の行から
        try:
            # 商品名が必須
            name = row.get('商品名', '').strip()
            if not name:
                errors.append(f"行{row_num}: 商品名が必須です")
                continue

            # Unique IDの取得または生成
            unique_id = row.get('Unique ID', '').strip()
            if not unique_id:
                unique_id = str(uuid.uuid4())

            # 重複チェック（unique_idで）
            existing_item = db.query(Item).filter(Item.unique_id == unique_id).first()
            if existing_item:
                skipped_count += 1
                continue

            # 画像情報の取得
            has_photo_value = row.get('画像あり', '0').strip()
            has_photo = has_photo_value in ('1', 'True', 'true', 'TRUE')

            is_original_photo_value = row.get('オリジナル写真', '0').strip()
            is_original_photo = is_original_photo_value in ('1', 'True', 'true', 'TRUE')

            has_item_value = row.get('所持している', '0').strip()
            has_item = has_item_value in ('1', 'True', 'true', 'TRUE')

            # 商品を作成
            item = Item(
                profile_id=profile.id,
                unique_id=unique_id,
                name=name,
                category=row.get('カテゴリ') or None,
                sub_category=row.get('サブカテゴリ') or None,
                brand_model=row.get('ブランド・型番') or None,
                usage_scene=row.get('用途・シーン') or None,
                frequency=row.get('使用頻度') or None,
                favorite_points=row.get('気に入っているポイント') or None,
                seasonality=row.get('季節性', '通年'),
                has_photo=has_photo,
                photo_path=row.get('画像パス') or None,
                is_original_photo=is_original_photo,
                has_item=has_item,
                priority=int(row.get('優先度', 3)),
                status=row.get('投稿状況', '未投稿'),
                rakuten_url=row.get('楽天市場URL') or None,
                room_url=row.get('ROOM URL') or None,
                description=row.get('商品紹介文') or None,
                memo=row.get('メモ') or None,
            )

            db.add(item)
            imported_count += 1

        except Exception as e:
            errors.append(f"行{row_num}: {str(e)}")

    # コミット
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"データベースエラー: {str(e)}"
        )

    message = f"{imported_count}件の商品をインポートしました"
    if skipped_count > 0:
        message += f"（{skipped_count}件をスキップ：重複）"

    return {
        "imported_count": imported_count,
        "skipped_count": skipped_count,
        "errors": errors,
        "message": message
    }
