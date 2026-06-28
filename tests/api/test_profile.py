"""
Profile API のテスト
"""
import pytest


class TestProfileCRUD:
    """プロフィールのCRUD操作テスト"""

    def test_create_profile(self, client):
        """プロフィールを作成できる"""
        profile_data = {
            "room_name": "新規ROOM",
            "room_id": "new_room",
            "target_audience": "30代男性",
            "tone_manner": "親しみやすい"
        }

        response = client.post("/api/profile", json=profile_data)
        assert response.status_code == 201

        created = response.json()
        assert created["room_name"] == "新規ROOM"
        assert created["room_id"] == "new_room"

    def test_get_profile(self, client, sample_profile):
        """プロフィールを取得できる"""
        response = client.get("/api/profile")
        assert response.status_code == 200

        # プロフィールは1件のみ
        profile = response.json()
        assert profile["id"] == sample_profile.id
        assert profile["room_name"] == sample_profile.room_name

    def test_update_profile(self, client, sample_profile):
        """プロフィールを更新できる"""
        update_data = {
            "room_name": "更新後のROOM名",
            "tone_manner": "フランク"
        }

        response = client.put(f"/api/profile/{sample_profile.id}", json=update_data)
        assert response.status_code == 200

        updated = response.json()
        assert updated["room_name"] == "更新後のROOM名"
        assert updated["tone_manner"] == "フランク"

    def test_delete_profile(self, client, sample_profile):
        """プロフィールを削除できる"""
        response = client.delete(f"/api/profile/{sample_profile.id}")
        assert response.status_code == 204

        # 取得するとNullが返る
        response = client.get("/api/profile")
        assert response.status_code == 200
        assert response.json() is None


class TestProfileAISettings:
    """AI連携設定のテスト"""

    def test_ai_settings_persistence(self, client, sample_profile):
        """AI設定が保存される"""
        update_data = {
            "ai_enabled": True,
            "ai_provider_openai_key": "new_test_key",
            "ai_provider_openai_model": "gpt-4-turbo"
        }

        response = client.put(f"/api/profile/{sample_profile.id}", json=update_data)
        updated = response.json()

        assert updated["ai_enabled"] is True
        assert updated["ai_provider_openai_key"] == "new_test_key"
        assert updated["ai_provider_openai_model"] == "gpt-4-turbo"

    def test_multiple_ai_providers(self, client, sample_profile):
        """複数のAIプロバイダー設定が可能"""
        update_data = {
            "ai_provider_openai_key": "openai_key",
            "ai_provider_openai_model": "gpt-4",
            "ai_provider_gemini_key": "gemini_key",
            "ai_provider_gemini_model": "gemini-pro",
            "ai_provider_claude_key": "claude_key",
            "ai_provider_claude_model": "claude-3-sonnet"
        }

        response = client.put(f"/api/profile/{sample_profile.id}", json=update_data)
        updated = response.json()

        assert updated["ai_provider_openai_key"] == "openai_key"
        assert updated["ai_provider_gemini_key"] == "gemini_key"
        assert updated["ai_provider_claude_key"] == "claude_key"
