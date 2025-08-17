from app.prompts import render_conversation_prompt


def test_render_without_history():
    out = render_conversation_prompt("こんにちは", history=None)
    assert "ユーザー: こんにちは" in out
    assert "過去の会話" not in out


def test_render_with_history():
    hist = "ユーザー: 前の質問\nアシスタント: 前の回答"
    out = render_conversation_prompt("次の質問です", history=hist)
    assert "過去の会話" in out
    assert "ユーザー: 次の質問です" in out
