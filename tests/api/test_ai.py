"""
AI生成機能のテスト（モック使用）
"""
import pytest
from unittest.mock import AsyncMock, patch


class TestAIGeneration:
    """AI生成機能のテスト"""

    @pytest.mark.asyncio
    async def test_ai_generation_adds_original_photo_tag(self, client, sample_profile):
        """オリジナル写真フラグで#オリジナル写真が自動付与される"""

        # モックAIレスポンス
        mock_response = "テスト紹介文\n\n詳細な説明です。\n\n#テスト #商品"

        with patch("backend.api.items._call_openai", new_callable=AsyncMock) as mock_ai:
            mock_ai.return_value = mock_response

            # AI生成リクエスト
            response = client.post("/api/items/generate-description", json={
                "item": {
                    "name": "テスト商品",
                    "category": "家電",
                    "is_original_photo": True  # オリジナル写真ON
                },
                "profile": {
                    "ai_enabled": True,
                    "ai_provider_openai_key": "test_key",
                    "ai_provider_openai_model": "gpt-4",
                    "tone_manner": "親しみやすい"
                },
                "provider": "openai"
            })

            assert response.status_code == 200
            result = response.json()

            # #オリジナル写真が自動付与されている
            assert "#オリジナル写真" in result["description"]
            assert result["provider"] == "openai"
            assert result["model"] == "gpt-4"

    @pytest.mark.asyncio
    async def test_ai_generation_without_original_photo(self, client, sample_profile):
        """オリジナル写真フラグがOFFの場合はタグが付与されない"""

        mock_response = "テスト紹介文\n\n詳細な説明です。\n\n#テスト #商品"

        with patch("backend.api.items._call_openai", new_callable=AsyncMock) as mock_ai:
            mock_ai.return_value = mock_response

            response = client.post("/api/items/generate-description", json={
                "item": {
                    "name": "テスト商品",
                    "is_original_photo": False  # オリジナル写真OFF
                },
                "profile": {
                    "ai_enabled": True,
                    "ai_provider_openai_key": "test_key",
                    "ai_provider_openai_model": "gpt-4",
                    "tone_manner": "親しみやすい"
                },
                "provider": "openai"
            })

            result = response.json()

            # #オリジナル写真は付与されていない
            assert "#オリジナル写真" not in result["description"]

    def test_ai_disabled_returns_error(self, client, sample_profile):
        """AI連携が無効の場合はエラー"""
        response = client.post("/api/items/generate-description", json={
            "item": {"name": "テスト商品"},
            "profile": {
                "ai_enabled": False  # AI無効
            },
            "provider": "openai"
        })

        assert response.status_code == 400
        assert "not enabled" in response.json()["detail"].lower()

    def test_missing_api_key_returns_error(self, client, sample_profile):
        """APIキーがない場合はエラー"""
        response = client.post("/api/items/generate-description", json={
            "item": {"name": "テスト商品"},
            "profile": {
                "ai_enabled": True,
                "ai_provider_openai_key": None,  # APIキーなし
                "ai_provider_openai_model": "gpt-4"
            },
            "provider": "openai"
        })

        assert response.status_code == 400
        assert "not configured" in response.json()["detail"].lower()

    def test_unsupported_provider_returns_error(self, client, sample_profile):
        """サポートされていないプロバイダーはエラー"""
        response = client.post("/api/items/generate-description", json={
            "item": {"name": "テスト商品"},
            "profile": {
                "ai_enabled": True
            },
            "provider": "unknown_provider"
        })

        assert response.status_code == 400
        assert "Unsupported" in response.json()["detail"]

    def test_gemini_missing_config_returns_error(self, client, sample_profile):
        """Gemini設定がない場合はエラー"""
        response = client.post("/api/items/generate-description", json={
            "item": {"name": "テスト商品"},
            "profile": {
                "ai_enabled": True,
                "ai_provider_gemini_key": None,
                "ai_provider_gemini_model": None
            },
            "provider": "gemini"
        })

        assert response.status_code == 400
        assert "Gemini" in response.json()["detail"]

    def test_perplexity_missing_config_returns_error(self, client, sample_profile):
        """Perplexity設定がない場合はエラー"""
        response = client.post("/api/items/generate-description", json={
            "item": {"name": "テスト商品"},
            "profile": {
                "ai_enabled": True,
                "ai_provider_perplexity_key": None,
                "ai_provider_perplexity_model": None
            },
            "provider": "perplexity"
        })

        assert response.status_code == 400
        assert "Perplexity" in response.json()["detail"]

    def test_claude_missing_config_returns_error(self, client, sample_profile):
        """Claude設定がない場合はエラー"""
        response = client.post("/api/items/generate-description", json={
            "item": {"name": "テスト商品"},
            "profile": {
                "ai_enabled": True,
                "ai_provider_claude_key": None,
                "ai_provider_claude_model": None
            },
            "provider": "claude"
        })

        assert response.status_code == 400
        assert "Claude" in response.json()["detail"]


class TestAIProviders:
    """AIプロバイダーのテスト"""

    def test_get_available_providers(self, client):
        """利用可能なプロバイダーを取得できる"""
        response = client.get("/api/ai/available-providers")
        assert response.status_code == 200

        providers = response.json()
        assert "providers" in providers
        assert isinstance(providers["providers"], list)
