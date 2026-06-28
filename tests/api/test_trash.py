"""
ゴミ箱機能のテスト
"""
import pytest
import io
from datetime import datetime


class TestTrashFeature:
    """ゴミ箱機能のテストクラス"""

    def test_delete_item_moves_to_trash(self, client, sample_item):
        """商品削除でゴミ箱に移動する"""
        item_id = sample_item.id

        # 削除実行
        response = client.delete(f"/api/items/{item_id}")
        assert response.status_code == 204

        # ゴミ箱に存在確認
        response = client.get("/api/items/trash")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["id"] == item_id
        assert data["items"][0]["deleted_at"] is not None

    def test_restore_item_from_trash(self, client, sample_item):
        """ゴミ箱から商品を復元できる"""
        item_id = sample_item.id

        # 削除
        client.delete(f"/api/items/{item_id}")

        # 復元
        response = client.post(f"/api/items/{item_id}/restore")
        assert response.status_code == 200
        restored = response.json()
        assert restored["deleted_at"] is None

        # 商品一覧に戻っている
        response = client.get("/api/items")
        items = response.json()
        assert items["total"] == 1
        assert items["items"][0]["id"] == item_id

    def test_restore_non_trash_item_fails(self, client, sample_item):
        """ゴミ箱にない商品の復元は失敗する"""
        item_id = sample_item.id

        # 削除していない商品を復元しようとする
        response = client.post(f"/api/items/{item_id}/restore")
        assert response.status_code == 400
        assert "not in trash" in response.json()["detail"].lower()

    def test_permanent_delete(self, client, sample_item):
        """商品を完全削除できる"""
        item_id = sample_item.id

        # 完全削除
        response = client.delete(f"/api/items/{item_id}/permanent")
        assert response.status_code == 204

        # 存在しない
        response = client.get(f"/api/items/{item_id}")
        assert response.status_code == 404

        # ゴミ箱にも存在しない
        response = client.get("/api/items/trash")
        assert response.json()["total"] == 0

    def test_trash_count_in_stats(self, client, sample_item):
        """統計情報にゴミ箱カウントが含まれる"""
        # 削除前
        response = client.get("/api/items/stats/summary")
        assert response.json()["trash_count"] == 0

        # 削除
        client.delete(f"/api/items/{sample_item.id}")

        # 削除後
        response = client.get("/api/items/stats/summary")
        stats = response.json()
        assert stats["trash_count"] == 1
        assert stats["total_items"] == 0  # ゴミ箱は除外される

    def test_items_list_excludes_trash(self, client, sample_item):
        """商品一覧はゴミ箱の商品を除外する"""
        # 削除前
        response = client.get("/api/items")
        assert response.json()["total"] == 1

        # 削除
        client.delete(f"/api/items/{sample_item.id}")

        # 削除後
        response = client.get("/api/items")
        assert response.json()["total"] == 0

    def test_trash_list_sorted_by_deleted_at(self, client, sample_items):
        """ゴミ箱は削除日時の新しい順でソートされる"""
        # 複数の商品を削除
        for item in sample_items[:3]:
            client.delete(f"/api/items/{item.id}")

        # ゴミ箱取得
        response = client.get("/api/items/trash")
        trash_items = response.json()["items"]

        # 削除日時の新しい順
        deleted_times = [item["deleted_at"] for item in trash_items]
        assert deleted_times == sorted(deleted_times, reverse=True)

    def test_search_does_not_include_trash(self, client, sample_item):
        """検索結果にゴミ箱の商品は含まれない"""
        # 削除
        client.delete(f"/api/items/{sample_item.id}")

        # 検索
        response = client.get(f"/api/items?search={sample_item.name}")
        assert response.json()["total"] == 0

    def test_permanent_delete_with_image(self, client, sample_item):
        """画像付き商品を完全削除すると画像も削除される"""
        item_id = sample_item.id

        # 画像をアップロード
        files = {
            "file": ("test.jpg", io.BytesIO(b"image"), "image/jpeg")
        }
        upload_response = client.post(f"/api/items/{item_id}/upload-image", files=files)
        assert upload_response.status_code == 200

        # 画像パスを取得
        photo_path = upload_response.json()["photo_path"]
        assert photo_path is not None

        # 完全削除
        response = client.delete(f"/api/items/{item_id}/permanent")
        assert response.status_code == 204

        # 商品が存在しないことを確認
        response = client.get(f"/api/items/{item_id}")
        assert response.status_code == 404
