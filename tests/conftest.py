"""
pytest設定と共通フィクスチャ
"""
import pytest
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from backend.database import Base, get_db
from backend.main import app
from backend.models import Profile, Item

# テスト用データベース
TEST_DB_PATH = "test_rakuten_room.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///./{TEST_DB_PATH}"


@pytest.fixture(scope="function")
def db_session():
    """テスト用データベースセッション"""
    # テスト用DBを作成
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)

    # テストDB削除
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def sample_profile(db_session):
    """テスト用プロフィール"""
    profile = Profile(
        room_name="テストROOM",
        room_id="test_room",
        owner_name="テスト太郎",
        target_audience="20-30代女性",
        room_direction="シンプルライフ",
        room_theme="暮らし、インテリア",
        tone_manner="親しみやすい",
        posting_style="商品の良さを丁寧に伝える",
        ng_words="最安値、激安",
        ai_enabled=True,
        ai_provider_openai_key="test_key",
        ai_provider_openai_model="gpt-4"
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)
    return profile


@pytest.fixture
def sample_item(db_session, sample_profile):
    """テスト用商品"""
    item = Item(
        profile_id=sample_profile.id,
        unique_id="test-unique-id-001",
        name="テスト商品",
        category="家電",
        sub_category="キッチン家電",
        brand_model="テストブランド TM-001",
        usage_scene="毎日の料理",
        frequency="毎日",
        favorite_points="使いやすくて便利",
        seasonality="通年",
        priority=3,
        status="未投稿",
        has_photo=False,
        is_original_photo=False,
        has_item=True
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)
    return item


@pytest.fixture
def sample_items(db_session, sample_profile):
    """テスト用商品（複数）"""
    items = []
    for i in range(5):
        item = Item(
            profile_id=sample_profile.id,
            unique_id=f"test-unique-id-{i:03d}",
            name=f"テスト商品{i+1}",
            category="家電" if i % 2 == 0 else "生活雑貨",
            priority=i % 5 + 1,
            status="未投稿" if i < 3 else "投稿済み",
            has_photo=False,
            is_original_photo=False,
            has_item=True
        )
        db_session.add(item)
        items.append(item)

    db_session.commit()
    for item in items:
        db_session.refresh(item)

    return items
