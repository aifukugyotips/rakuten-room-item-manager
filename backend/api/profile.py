"""
Profile API
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Profile
from backend.schemas import ProfileCreate, ProfileUpdate, ProfileResponse

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.get("", response_model=Optional[ProfileResponse])
def get_profile(db: Session = Depends(get_db)):
    """
    プロフィールを取得

    プロフィールは1件のみ存在する前提
    """
    profile = db.query(Profile).first()
    return profile


@router.post("", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
def create_profile(profile_data: ProfileCreate, db: Session = Depends(get_db)):
    """
    プロフィールを作成

    既にプロフィールが存在する場合はエラー
    """
    # 既存のプロフィールをチェック
    existing_profile = db.query(Profile).first()
    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile already exists. Use PUT to update."
        )

    # プロフィールを作成
    profile_dict = profile_data.model_dump()

    # room_idの前後の空白を削除
    if profile_dict.get('room_id'):
        profile_dict['room_id'] = profile_dict['room_id'].strip()

    profile = Profile(**profile_dict)
    db.add(profile)
    db.commit()
    db.refresh(profile)

    return profile


@router.put("/{profile_id}", response_model=ProfileResponse)
def update_profile(
    profile_id: int,
    profile_data: ProfileUpdate,
    db: Session = Depends(get_db)
):
    """
    プロフィールを更新
    """
    # プロフィールを取得
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile with id {profile_id} not found"
        )

    # 更新（None以外のフィールドのみ）
    update_data = profile_data.model_dump(exclude_unset=True)

    # room_idの前後の空白を削除
    if 'room_id' in update_data and update_data['room_id']:
        update_data['room_id'] = update_data['room_id'].strip()

    for key, value in update_data.items():
        setattr(profile, key, value)

    db.commit()
    db.refresh(profile)

    return profile


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_profile(profile_id: int, db: Session = Depends(get_db)):
    """
    プロフィールを削除
    """
    # プロフィールを取得
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile with id {profile_id} not found"
        )

    db.delete(profile)
    db.commit()

    return None
