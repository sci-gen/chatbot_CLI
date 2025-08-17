"""PromptTemplate を管理するモジュール。

LangChain の `PromptTemplate` を優先して使いますが、開発環境に
langchain が無い場合でも動作するようにフォールバック実装を用意します。

提供する関数:
- render_conversation_prompt(user_input, history) -> str
  会話用テンプレートに user_input と履歴を埋め込んだ文字列を返します。
"""
from __future__ import annotations

from typing import Optional

from langchain.prompts import PromptTemplate


# 会話用の基本テンプレート。history が空の場合でも読みやすいように整形する。
_CONVERSATION_TEMPLATE = (
    "あなたは親切で協力的なアシスタントです。\n"
    "{history}\n"
    "ユーザー: {input}\n"
    "アシスタント:"
)


conversation_template = PromptTemplate(
    input_variables=["history", "input"], template=_CONVERSATION_TEMPLATE
)


def render_conversation_prompt(user_input: str, history: Optional[str] = None) -> str:
    """会話テンプレートに履歴とユーザー入力を埋め込んだ文字列を返す。

    Args:
        user_input: ユーザーの現在の発話。
        history: これまでの会話履歴（プレーンテキスト）。None または空は無視される。

    Returns:
        LLM に渡すためのプロンプト文字列。
    """
    hist = (history or "").strip()
    hist_text = f"過去の会話:\n{hist}" if hist else ""
    return conversation_template.format(history=hist_text, input=user_input)


if __name__ == "__main__":
    # 簡易動作確認
    print(render_conversation_prompt("こんにちは", "ユーザー: 以前の発話\nアシスタント: 以前の応答"))
