"""
CSVエクスポート/インポート機能のテスト
"""
import pytest
import io
import csv


class TestCSVExport:
    """CSVエクスポートのテスト"""

    def test_csv_export_includes_new_fields(self, client, sample_item):
        """CSVエクスポートに新しいフィールドが含まれる"""
        # オリジナル写真、所持フラグ、商品紹介文を設定
        client.put(f"/api/items/{sample_item.id}", json={
            "is_original_photo": True,
            "has_item": True,
            "has_photo": True,
            "photo_path": "images/test.jpg",
            "description": "テスト紹介文です"
        })

        # エクスポート
        response = client.get("/api/export/csv")
        assert response.status_code == 200

        # CSVパース
        content = response.content.decode('utf-8')
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)

        # ヘッダー確認
        assert "画像あり" in reader.fieldnames
        assert "画像パス" in reader.fieldnames
        assert "オリジナル写真" in reader.fieldnames
        assert "所持している" in reader.fieldnames
        assert "商品紹介文" in reader.fieldnames

        # データ確認
        assert rows[0]["画像あり"] == "1"
        assert rows[0]["画像パス"] == "images/test.jpg"
        assert rows[0]["オリジナル写真"] == "1"
        assert rows[0]["所持している"] == "1"
        assert rows[0]["商品紹介文"] == "テスト紹介文です"

    def test_csv_export_header_order(self, client, sample_item):
        """CSVヘッダーの順序が正しい"""
        response = client.get("/api/export/csv")
        content = response.content.decode('utf-8')
        reader = csv.DictReader(io.StringIO(content))

        expected_headers = [
            'ID', 'Unique ID', '商品名', 'カテゴリ', 'サブカテゴリ', 'ブランド・型番',
            '用途・シーン', '使用頻度', '気に入っているポイント', '季節性',
            '画像あり', '画像パス', 'オリジナル写真', '所持している',
            '優先度', '投稿状況', '楽天市場URL', 'ROOM URL', '商品紹介文', 'メモ',
            '登録日時', '更新日時', '投稿日時'
        ]

        assert list(reader.fieldnames) == expected_headers

    def test_csv_export_boolean_values(self, client, sample_item):
        """Boolean値が正しく0/1で出力される"""
        # has_photo=False, is_original_photo=False, has_item=Trueの状態
        response = client.get("/api/export/csv")
        content = response.content.decode('utf-8')
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)

        assert rows[0]["画像あり"] == "0"
        assert rows[0]["オリジナル写真"] == "0"
        assert rows[0]["所持している"] == "1"

    def test_csv_export_filename_format(self, client, sample_item):
        """CSVファイル名にタイムスタンプが含まれる"""
        response = client.get("/api/export/csv")
        content_disposition = response.headers.get("Content-Disposition")

        assert "attachment; filename=rakuten_room_items_" in content_disposition
        assert ".csv" in content_disposition


class TestCSVImport:
    """CSVインポートのテスト"""

    def test_csv_import_with_new_fields(self, client, sample_profile):
        """CSVインポートで新しいフィールドを読み込める"""
        # CSVデータ作成
        csv_data = """商品名,カテゴリ,画像あり,画像パス,オリジナル写真,所持している,商品紹介文,優先度,投稿状況
テストインポート商品,家電,1,images/test.jpg,1,1,インポートテスト紹介文,5,未投稿
"""

        # インポート
        files = {"file": ("test.csv", csv_data, "text/csv")}
        response = client.post("/api/export/csv/import", files=files)
        assert response.status_code == 200

        result = response.json()
        assert result["imported_count"] == 1

        # データ確認
        response = client.get("/api/items")
        items = response.json()["items"]
        assert len(items) == 1

        item = items[0]
        assert item["name"] == "テストインポート商品"
        assert item["has_photo"] is True
        assert item["photo_path"] == "images/test.jpg"
        assert item["is_original_photo"] is True
        assert item["has_item"] is True
        assert item["description"] == "インポートテスト紹介文"

    def test_csv_import_boolean_parsing(self, client, sample_profile):
        """Boolean値の様々な形式をパースできる"""
        csv_data = """商品名,オリジナル写真,所持している
商品1,1,1
商品2,0,0
商品3,True,true
商品4,TRUE,TRUE
商品5,False,false
"""

        files = {"file": ("test.csv", csv_data, "text/csv")}
        response = client.post("/api/export/csv/import", files=files)
        assert response.status_code == 200

        # データ確認
        response = client.get("/api/items")
        items = response.json()["items"]

        # 名前でソートして確認
        items_by_name = {item["name"]: item for item in items}

        # 1, True, TRUEはTrue
        assert items_by_name["商品1"]["is_original_photo"] is True
        assert items_by_name["商品3"]["is_original_photo"] is True
        assert items_by_name["商品4"]["is_original_photo"] is True

        # 0, FalseはFalse
        assert items_by_name["商品2"]["is_original_photo"] is False
        assert items_by_name["商品5"]["is_original_photo"] is False

    def test_csv_import_skip_duplicates(self, client, sample_profile):
        """重複するUnique IDの商品はスキップされる"""
        # 最初のインポート
        csv_data1 = """Unique ID,商品名
unique-001,商品1
"""
        files = {"file": ("test1.csv", csv_data1, "text/csv")}
        response = client.post("/api/export/csv/import", files=files)
        assert response.json()["imported_count"] == 1

        # 同じUnique IDで再インポート
        csv_data2 = """Unique ID,商品名
unique-001,商品1（更新版）
"""
        files = {"file": ("test2.csv", csv_data2, "text/csv")}
        response = client.post("/api/export/csv/import", files=files)

        result = response.json()
        assert result["imported_count"] == 0
        assert result["skipped_count"] == 1

    def test_csv_import_missing_required_field(self, client, sample_profile):
        """必須フィールド（商品名）がない場合はエラー"""
        csv_data = """カテゴリ,優先度
家電,3
"""

        files = {"file": ("test.csv", csv_data, "text/csv")}
        response = client.post("/api/export/csv/import", files=files)

        result = response.json()
        assert result["imported_count"] == 0
        assert len(result["errors"]) > 0


class TestJSONExport:
    """JSONエクスポートのテスト"""

    def test_ready_to_post_includes_new_fields(self, client, sample_item):
        """投稿準備済み商品エクスポートに新フィールドが含まれる"""
        # 商品を更新
        client.put(f"/api/items/{sample_item.id}", json={
            "status": "未投稿",
            "is_original_photo": True,
            "has_item": True,
            "description": "テスト紹介文"
        })

        # エクスポート
        response = client.get("/api/export/items/ready-to-post?limit=10")
        assert response.status_code == 200

        data = response.json()
        assert data["count"] == 1

        item = data["items"][0]
        assert "is_original_photo" in item
        assert "has_item" in item
        assert "description" in item
        assert item["is_original_photo"] is True
        assert item["has_item"] is True
        assert item["description"] == "テスト紹介文"


class TestReadyToPost:
    """ready-to-post エンドポイントのフィルタ・パラメータテスト"""

    def test_returns_room_url_and_status(self, client, sample_item):
        """レスポンスに room_url と status が含まれる"""
        response = client.get("/api/export/items/ready-to-post")
        assert response.status_code == 200

        item = response.json()["items"][0]
        assert "room_url" in item
        assert "status" in item

    def test_limit_parameter(self, client, sample_items):
        """limit パラメータで件数を絞れる"""
        response = client.get("/api/export/items/ready-to-post?limit=2")
        data = response.json()
        assert len(data["items"]) <= 2

    def test_min_priority_filter(self, client, sample_profile, db_session):
        """min_priority で優先度の低い商品を除外できる"""
        from backend.models import Item
        low = Item(profile_id=sample_profile.id, unique_id="low-1",
                   name="低優先度", priority=1, status="未投稿",
                   has_photo=False, is_original_photo=False, has_item=True)
        high = Item(profile_id=sample_profile.id, unique_id="high-1",
                    name="高優先度", priority=5, status="未投稿",
                    has_photo=False, is_original_photo=False, has_item=True)
        db_session.add_all([low, high])
        db_session.commit()

        response = client.get("/api/export/items/ready-to-post?min_priority=4")
        items = response.json()["items"]
        assert all(i["priority"] >= 4 for i in items)
        names = [i["name"] for i in items]
        assert "高優先度" in names
        assert "低優先度" not in names

    def test_require_photo_filter(self, client, sample_profile, db_session):
        """require_photo=true で画像なし商品を除外できる"""
        from backend.models import Item
        with_photo = Item(profile_id=sample_profile.id, unique_id="photo-1",
                          name="画像あり", priority=3, status="未投稿",
                          has_photo=True, is_original_photo=False, has_item=True)
        without_photo = Item(profile_id=sample_profile.id, unique_id="no-photo-1",
                             name="画像なし", priority=3, status="未投稿",
                             has_photo=False, is_original_photo=False, has_item=True)
        db_session.add_all([with_photo, without_photo])
        db_session.commit()

        response = client.get("/api/export/items/ready-to-post?require_photo=true")
        items = response.json()["items"]
        assert all(i["has_photo"] for i in items)
        names = [i["name"] for i in items]
        assert "画像あり" in names
        assert "画像なし" not in names

    def test_require_description_filter(self, client, sample_profile, db_session):
        """require_description=true で紹介文なし商品を除外できる"""
        from backend.models import Item
        with_desc = Item(profile_id=sample_profile.id, unique_id="desc-1",
                         name="紹介文あり", priority=3, status="未投稿",
                         has_photo=False, is_original_photo=False, has_item=True,
                         description="テスト紹介文")
        without_desc = Item(profile_id=sample_profile.id, unique_id="no-desc-1",
                            name="紹介文なし", priority=3, status="未投稿",
                            has_photo=False, is_original_photo=False, has_item=True)
        db_session.add_all([with_desc, without_desc])
        db_session.commit()

        response = client.get("/api/export/items/ready-to-post?require_description=true")
        items = response.json()["items"]
        names = [i["name"] for i in items]
        assert "紹介文あり" in names
        assert "紹介文なし" not in names

    def test_original_photo_only_filter(self, client, sample_profile, db_session):
        """original_photo_only=true でオリジナル写真のみ返す"""
        from backend.models import Item
        original = Item(profile_id=sample_profile.id, unique_id="orig-1",
                        name="オリジナル", priority=3, status="未投稿",
                        has_photo=True, is_original_photo=True, has_item=True)
        non_original = Item(profile_id=sample_profile.id, unique_id="non-orig-1",
                            name="非オリジナル", priority=3, status="未投稿",
                            has_photo=True, is_original_photo=False, has_item=True)
        db_session.add_all([original, non_original])
        db_session.commit()

        response = client.get("/api/export/items/ready-to-post?original_photo_only=true")
        items = response.json()["items"]
        assert all(i["is_original_photo"] for i in items)
        names = [i["name"] for i in items]
        assert "オリジナル" in names
        assert "非オリジナル" not in names

    def test_original_photo_first_ordering(self, client, sample_profile, db_session):
        """original_photo_first=true でオリジナル写真が先頭に来る"""
        from backend.models import Item
        non_original = Item(profile_id=sample_profile.id, unique_id="ord-non-1",
                            name="非オリジナル", priority=5, status="未投稿",
                            has_photo=True, is_original_photo=False, has_item=True)
        original = Item(profile_id=sample_profile.id, unique_id="ord-orig-1",
                        name="オリジナル", priority=3, status="未投稿",
                        has_photo=True, is_original_photo=True, has_item=True)
        db_session.add_all([non_original, original])
        db_session.commit()

        response = client.get("/api/export/items/ready-to-post?original_photo_first=true")
        items = response.json()["items"]
        # オリジナルが先頭（優先度が低くても）
        assert items[0]["is_original_photo"] is True

    def test_include_posted_returns_posted_items(self, client, sample_profile, db_session):
        """include_posted=true で投稿済みも含まれる"""
        from backend.models import Item
        posted = Item(profile_id=sample_profile.id, unique_id="posted-1",
                      name="投稿済み商品", priority=3, status="投稿済み",
                      has_photo=False, is_original_photo=False, has_item=True)
        unpublished = Item(profile_id=sample_profile.id, unique_id="unpub-1",
                           name="未投稿商品", priority=3, status="未投稿",
                           has_photo=False, is_original_photo=False, has_item=True)
        db_session.add_all([posted, unpublished])
        db_session.commit()

        response = client.get("/api/export/items/ready-to-post?include_posted=true")
        names = [i["name"] for i in response.json()["items"]]
        assert "投稿済み商品" in names
        assert "未投稿商品" in names

    def test_include_posted_false_excludes_posted(self, client, sample_profile, db_session):
        """include_posted=false（デフォルト）では投稿済みを除外する"""
        from backend.models import Item
        posted = Item(profile_id=sample_profile.id, unique_id="excl-posted-1",
                      name="投稿済み商品", priority=3, status="投稿済み",
                      has_photo=False, is_original_photo=False, has_item=True)
        db_session.add(posted)
        db_session.commit()

        response = client.get("/api/export/items/ready-to-post")
        names = [i["name"] for i in response.json()["items"]]
        assert "投稿済み商品" not in names

    def test_excludes_trash(self, client, sample_item, client_with_item=None):
        """ゴミ箱の商品は返さない"""
        # ゴミ箱へ移動
        client.delete(f"/api/items/{sample_item.id}")

        response = client.get("/api/export/items/ready-to-post")
        ids = [i["id"] for i in response.json()["items"]]
        assert sample_item.id not in ids
