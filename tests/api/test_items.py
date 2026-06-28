"""
Items API のテスト
"""
import pytest
import io
from pathlib import Path


class TestItemsCRUD:
    """商品のCRUD操作テスト"""

    def test_create_item(self, client, sample_profile):
        """商品を作成できる"""
        item_data = {
            "name": "新規商品",
            "category": "生活雑貨",
            "priority": 4,
            "status": "未投稿",
            "is_original_photo": True,
            "has_item": True
        }

        response = client.post("/api/items", json=item_data)
        assert response.status_code == 201

        created = response.json()
        assert created["name"] == "新規商品"
        assert created["is_original_photo"] is True
        assert created["has_item"] is True

    def test_get_items_list(self, client, sample_items):
        """商品一覧を取得できる"""
        response = client.get("/api/items")
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 5

    def test_get_item_by_id(self, client, sample_item):
        """IDで商品を取得できる"""
        response = client.get(f"/api/items/{sample_item.id}")
        assert response.status_code == 200

        item = response.json()
        assert item["id"] == sample_item.id
        assert item["name"] == sample_item.name

    def test_get_nonexistent_item(self, client):
        """存在しない商品はエラー"""
        response = client.get("/api/items/99999")
        assert response.status_code == 404

    def test_update_item(self, client, sample_item):
        """商品を更新できる"""
        update_data = {
            "name": "更新後の商品名",
            "is_original_photo": True,
            "description": "更新後の紹介文"
        }

        response = client.put(f"/api/items/{sample_item.id}", json=update_data)
        assert response.status_code == 200

        updated = response.json()
        assert updated["name"] == "更新後の商品名"
        assert updated["is_original_photo"] is True
        assert updated["description"] == "更新後の紹介文"

    def test_update_partial_fields(self, client, sample_item):
        """一部のフィールドのみ更新できる"""
        original_name = sample_item.name

        update_data = {"priority": 5}
        response = client.put(f"/api/items/{sample_item.id}", json=update_data)

        updated = response.json()
        assert updated["priority"] == 5
        assert updated["name"] == original_name  # 名前は変更されていない


class TestItemsSearch:
    """商品検索・フィルタのテスト"""

    def test_search_by_name(self, client, sample_items):
        """商品名で検索できる"""
        response = client.get("/api/items?search=テスト商品1")
        data = response.json()

        assert data["total"] == 1
        assert "テスト商品1" in data["items"][0]["name"]

    def test_filter_by_status(self, client, sample_items):
        """投稿状況でフィルタできる"""
        response = client.get("/api/items?status_filter=未投稿")
        data = response.json()

        # sample_itemsの最初の3つが未投稿
        assert data["total"] == 3
        for item in data["items"]:
            assert item["status"] == "未投稿"

    def test_filter_by_priority(self, client, sample_items):
        """優先度でフィルタできる"""
        response = client.get("/api/items?priority=3")
        data = response.json()

        for item in data["items"]:
            assert item["priority"] == 3

    def test_filter_by_category(self, client, sample_items):
        """カテゴリでフィルタできる"""
        response = client.get("/api/items?category=家電")
        data = response.json()

        for item in data["items"]:
            assert item["category"] == "家電"

    def test_pagination(self, client, sample_items):
        """ページネーションが機能する"""
        # 最初の2件
        response = client.get("/api/items?limit=2&offset=0")
        data = response.json()
        assert len(data["items"]) == 2

        # 次の2件
        response = client.get("/api/items?limit=2&offset=2")
        data = response.json()
        assert len(data["items"]) == 2


class TestItemsStats:
    """統計情報のテスト"""

    def test_get_stats_summary(self, client, sample_items):
        """統計情報を取得できる"""
        response = client.get("/api/items/stats/summary")
        assert response.status_code == 200

        stats = response.json()
        assert stats["total_items"] == 5
        assert stats["unpublished_count"] == 3
        assert stats["published_count"] == 2
        assert stats["trash_count"] == 0

    def test_stats_excludes_trash(self, client, sample_items):
        """統計情報はゴミ箱を除外する"""
        # 1つ削除
        client.delete(f"/api/items/{sample_items[0].id}")

        response = client.get("/api/items/stats/summary")
        stats = response.json()

        assert stats["total_items"] == 4  # ゴミ箱を除外
        assert stats["trash_count"] == 1


class TestOriginalPhoto:
    """オリジナル写真フラグのテスト"""

    def test_original_photo_flag_persistence(self, client, sample_item):
        """オリジナル写真フラグが保存される"""
        # 更新
        client.put(f"/api/items/{sample_item.id}", json={
            "is_original_photo": True
        })

        # 取得
        response = client.get(f"/api/items/{sample_item.id}")
        item = response.json()

        assert item["is_original_photo"] is True

    def test_has_item_flag_persistence(self, client, sample_item):
        """所持フラグが保存される"""
        # 更新
        client.put(f"/api/items/{sample_item.id}", json={
            "has_item": False
        })

        # 取得
        response = client.get(f"/api/items/{sample_item.id}")
        item = response.json()

        assert item["has_item"] is False


class TestImageUpload:
    """画像アップロード機能のテスト"""

    def test_upload_image_success(self, client, sample_item):
        """画像をアップロードできる"""
        # ダミー画像ファイルを作成
        image_content = b"fake image content"
        files = {
            "file": ("test_image.jpg", io.BytesIO(image_content), "image/jpeg")
        }

        response = client.post(f"/api/items/{sample_item.id}/upload-image", files=files)
        assert response.status_code == 200

        data = response.json()
        assert "photo_path" in data
        assert data["photo_path"].startswith("images/")
        assert data["photo_path"].endswith(".jpg")
        assert data["item"]["has_photo"] is True

    def test_upload_image_item_not_found(self, client):
        """存在しない商品への画像アップロードはエラー"""
        image_content = b"fake image content"
        files = {
            "file": ("test.jpg", io.BytesIO(image_content), "image/jpeg")
        }

        response = client.post("/api/items/99999/upload-image", files=files)
        assert response.status_code == 404

    def test_upload_image_invalid_file_type(self, client, sample_item):
        """画像以外のファイルはアップロードできない"""
        text_content = b"not an image"
        files = {
            "file": ("test.txt", io.BytesIO(text_content), "text/plain")
        }

        response = client.post(f"/api/items/{sample_item.id}/upload-image", files=files)
        assert response.status_code == 400
        assert "must be an image" in response.json()["detail"]

    def test_upload_image_replaces_existing(self, client, sample_item):
        """既存の画像を置き換えられる"""
        # 最初の画像をアップロード
        files1 = {
            "file": ("image1.jpg", io.BytesIO(b"image1"), "image/jpeg")
        }
        response1 = client.post(f"/api/items/{sample_item.id}/upload-image", files=files1)
        first_path = response1.json()["photo_path"]

        # 2回目の画像をアップロード
        files2 = {
            "file": ("image2.jpg", io.BytesIO(b"image2"), "image/jpeg")
        }
        response2 = client.post(f"/api/items/{sample_item.id}/upload-image", files=files2)
        second_path = response2.json()["photo_path"]

        # パスが変わっている
        assert first_path != second_path
        assert response2.status_code == 200


class TestImageDelete:
    """画像削除機能のテスト"""

    def test_delete_image_success(self, client, sample_item):
        """画像を削除できる"""
        # まず画像をアップロード
        files = {
            "file": ("test.jpg", io.BytesIO(b"image"), "image/jpeg")
        }
        client.post(f"/api/items/{sample_item.id}/upload-image", files=files)

        # 画像を削除
        response = client.delete(f"/api/items/{sample_item.id}/image")
        assert response.status_code == 200

        data = response.json()
        assert data["item"]["has_photo"] is False
        assert data["item"]["photo_path"] is None

    def test_delete_image_item_not_found(self, client):
        """存在しない商品の画像削除はエラー"""
        response = client.delete("/api/items/99999/image")
        assert response.status_code == 404

    def test_delete_image_no_image_exists(self, client, sample_item):
        """画像がない商品の画像削除はエラー"""
        response = client.delete(f"/api/items/{sample_item.id}/image")
        assert response.status_code == 404
        assert "No image found" in response.json()["detail"]


class TestErrorCases:
    """エラーケースのテスト"""

    def test_create_item_without_profile(self, client, db_session):
        """プロフィールがない状態で商品作成はエラー"""
        # プロフィールを削除
        from backend.models import Profile
        db_session.query(Profile).delete()
        db_session.commit()

        item_data = {
            "name": "テスト商品",
            "category": "家電"
        }

        response = client.post("/api/items", json=item_data)
        assert response.status_code == 400
        assert "Profile not found" in response.json()["detail"]

    def test_update_nonexistent_item(self, client):
        """存在しない商品の更新はエラー"""
        update_data = {"name": "更新"}
        response = client.put("/api/items/99999", json=update_data)
        assert response.status_code == 404

    def test_delete_nonexistent_item(self, client):
        """存在しない商品の削除はエラー"""
        response = client.delete("/api/items/99999")
        assert response.status_code == 404

    def test_restore_nonexistent_item(self, client):
        """存在しない商品の復元はエラー"""
        response = client.post("/api/items/99999/restore")
        assert response.status_code == 404

    def test_permanent_delete_nonexistent_item(self, client):
        """存在しない商品の完全削除はエラー"""
        response = client.delete("/api/items/99999/permanent")
        assert response.status_code == 404


class TestHashtagSearch:
    """ハッシュタグ検索のテスト"""

    def test_search_by_hashtag_with_hash(self, client, sample_item):
        """#付きハッシュタグで検索できる"""
        # 商品に説明文を追加
        client.put(f"/api/items/{sample_item.id}", json={
            "description": "素晴らしい商品です #おすすめ #便利グッズ"
        })

        # #付きで検索
        response = client.get("/api/items?hashtag=#おすすめ")
        data = response.json()

        assert data["total"] >= 1
        assert "#おすすめ" in data["items"][0]["description"]

    def test_search_by_hashtag_without_hash(self, client, sample_item):
        """#なしハッシュタグでも検索できる"""
        # 商品に説明文を追加
        client.put(f"/api/items/{sample_item.id}", json={
            "description": "素晴らしい商品です #おすすめ #便利グッズ"
        })

        # #なしで検索
        response = client.get("/api/items?hashtag=おすすめ")
        data = response.json()

        assert data["total"] >= 1
        assert "#おすすめ" in data["items"][0]["description"]


class TestMarkStatus:
    """automation 連携ステータス更新のテスト"""

    def test_mark_posted(self, client, sample_item):
        """mark-posted で投稿済みになり、履歴と room_url が保存される"""
        payload = {
            "posted_at": "2026-05-20T10:30:00+09:00",
            "room_url": "https://room.rakuten.co.jp/test/123"
        }
        response = client.patch(f"/api/items/{sample_item.id}/mark-posted", json=payload)
        assert response.status_code == 200

        item = response.json()
        assert item["status"] == "投稿済み"
        assert item["room_url"] == "https://room.rakuten.co.jp/test/123"
        assert "2026-05-20T10:30:00+09:00" in item["posted_at_history"]

    def test_mark_posted_history_max_3(self, client, sample_item):
        """mark-posted は履歴を最大3件に保つ"""
        for i in range(4):
            client.patch(f"/api/items/{sample_item.id}/mark-posted", json={
                "posted_at": f"2026-05-{i+1:02d}T10:00:00+09:00"
            })

        response = client.get(f"/api/items/{sample_item.id}")
        item = response.json()
        assert len(item["posted_at_history"]) == 3

    def test_mark_posted_without_room_url(self, client, sample_item):
        """room_url なしでも mark-posted できる"""
        response = client.patch(f"/api/items/{sample_item.id}/mark-posted", json={
            "posted_at": "2026-05-20T10:30:00+09:00"
        })
        assert response.status_code == 200
        assert response.json()["status"] == "投稿済み"

    def test_mark_posted_not_found(self, client):
        """存在しない商品への mark-posted は 404"""
        response = client.patch("/api/items/99999/mark-posted", json={
            "posted_at": "2026-05-20T10:30:00+09:00"
        })
        assert response.status_code == 404

    def test_mark_unpublished(self, client, sample_item):
        """mark-unpublished で非公開になり、room_url がクリアされる"""
        # 先に room_url を設定
        client.put(f"/api/items/{sample_item.id}", json={
            "room_url": "https://room.rakuten.co.jp/test/123",
            "status": "投稿済み"
        })

        response = client.patch(f"/api/items/{sample_item.id}/mark-unpublished")
        assert response.status_code == 200

        item = response.json()
        assert item["status"] == "非公開"
        assert item["room_url"] is None

    def test_mark_unpublished_not_found(self, client):
        """存在しない商品への mark-unpublished は 404"""
        response = client.patch("/api/items/99999/mark-unpublished")
        assert response.status_code == 404

    def test_mark_available(self, client, sample_item):
        """mark-available で未投稿に戻り、room_url がクリアされる"""
        # 先に投稿済み状態にする
        client.put(f"/api/items/{sample_item.id}", json={
            "status": "投稿済み",
            "room_url": "https://room.rakuten.co.jp/test/123"
        })

        response = client.patch(f"/api/items/{sample_item.id}/mark-available")
        assert response.status_code == 200

        item = response.json()
        assert item["status"] == "未投稿"
        assert item["room_url"] is None

    def test_mark_available_not_found(self, client):
        """存在しない商品への mark-available は 404"""
        response = client.patch("/api/items/99999/mark-available")
        assert response.status_code == 404
