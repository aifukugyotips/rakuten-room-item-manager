"""
プロンプト生成のユニットテスト
"""
import pytest
from backend.prompts import (
    get_system_prompt,
    get_gemini_prompt,
    MASTER_PROMPT_BASE,
    TONE_FRIENDLY,
    PERPLEXITY_ADDITIONAL_RULE
)


class TestPromptGeneration:
    """プロンプト生成のテスト"""

    def test_get_system_prompt_friendly(self):
        """親しみやすいトーンのプロンプトを生成できる"""
        prompt = get_system_prompt("親しみやすい", is_perplexity=False)

        assert MASTER_PROMPT_BASE in prompt
        assert TONE_FRIENDLY in prompt
        assert "適度に絵文字を使って見た目を楽しくする" in prompt

    def test_get_system_prompt_professional(self):
        """専門的トーンのプロンプトを生成できる"""
        prompt = get_system_prompt("専門的", is_perplexity=False)

        assert "機能・スペックや利点を論理的に説明" in prompt

    def test_get_system_prompt_casual(self):
        """カジュアルトーンのプロンプトを生成できる"""
        prompt = get_system_prompt("カジュアル", is_perplexity=False)

        assert "友達にすすめるような距離感" in prompt

    def test_get_system_prompt_polite(self):
        """ていねいトーンのプロンプトを生成できる"""
        prompt = get_system_prompt("ていねい", is_perplexity=False)

        assert "よろしければ" in prompt or "おすすめです" in prompt

    def test_get_system_prompt_frank(self):
        """フランクトーンのプロンプトを生成できる"""
        prompt = get_system_prompt("フランク", is_perplexity=False)

        assert "友人に話すような口調" in prompt

    def test_get_system_prompt_default(self):
        """未知のトーンはデフォルト（親しみやすい）になる"""
        prompt = get_system_prompt("未知のトーン", is_perplexity=False)

        assert TONE_FRIENDLY in prompt

    def test_perplexity_additional_rule(self):
        """Perplexity用の追加ルールが含まれる"""
        prompt = get_system_prompt("親しみやすい", is_perplexity=True)

        assert PERPLEXITY_ADDITIONAL_RULE in prompt
        assert "出典リンクや引用番号" in prompt

    def test_perplexity_rule_not_included(self):
        """Perplexity以外は追加ルールが含まれない"""
        prompt = get_system_prompt("親しみやすい", is_perplexity=False)

        assert PERPLEXITY_ADDITIONAL_RULE not in prompt

    def test_get_gemini_prompt(self):
        """Gemini用プロンプトを生成できる"""
        user_prompt = "テスト商品の紹介文を生成してください"
        prompt = get_gemini_prompt("親しみやすい", user_prompt)

        assert MASTER_PROMPT_BASE in prompt
        assert TONE_FRIENDLY in prompt
        assert user_prompt in prompt

    def test_prompt_includes_emoji_instruction(self):
        """絵文字使用の指示が含まれる"""
        prompt = get_system_prompt("親しみやすい")

        assert "適度に絵文字を使って見た目を楽しくする（1-2個程度）" in prompt
        assert "適度に絵文字を使って見た目を楽しくする（2-3個程度" in prompt

    def test_prompt_includes_hashtag_instruction(self):
        """ハッシュタグの指示が含まれる"""
        prompt = get_system_prompt("親しみやすい")

        assert "各タグの先頭に必ず # を付けて出力してください" in prompt
        assert "カテゴリタグを優先し" in prompt

    def test_prompt_prohibits_price_info(self):
        """価格・キャンペーン情報の禁止が含まれる"""
        prompt = get_system_prompt("親しみやすい")

        assert "ポイント還元・送料無料・セールなどの価格・キャンペーン情報には一切言及しないでください" in prompt

    def test_prompt_includes_blank_line_instruction(self):
        """空行挿入の指示が含まれる"""
        prompt = get_system_prompt("親しみやすい")

        assert "必ず空行（改行）を入れてください" in prompt
