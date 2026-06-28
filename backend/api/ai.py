"""
AI API
"""
import importlib.util
from fastapi import APIRouter

router = APIRouter(prefix="/ai", tags=["AI"])


def is_package_installed(package_name: str) -> bool:
    """
    パッケージがインストールされているかチェック
    """
    return importlib.util.find_spec(package_name) is not None


@router.get("/available-providers")
def get_available_providers():
    """
    利用可能なAIプロバイダーを取得

    インストールされているAI SDKに基づいて、利用可能なプロバイダーのリストを返します。
    """
    providers = []

    # OpenAI
    if is_package_installed("openai"):
        providers.append({
            "id": "openai",
            "name": "OpenAI",
            "description": "GPT-4, GPT-3.5など"
        })

    # Google Gemini
    if is_package_installed("google.generativeai"):
        providers.append({
            "id": "gemini",
            "name": "Google Gemini",
            "description": "Gemini Pro, Gemini Flash"
        })

    # Perplexity
    # PerplexityはOpenAI互換APIなので、openaiパッケージがあれば利用可能
    if is_package_installed("openai"):
        providers.append({
            "id": "perplexity",
            "name": "Perplexity",
            "description": "Sonar, Llama models"
        })

    # Claude
    if is_package_installed("anthropic"):
        providers.append({
            "id": "claude",
            "name": "Claude",
            "description": "Claude 3.5 Sonnet, Claude 3 Opus"
        })

    return {"providers": providers}
