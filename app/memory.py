"""Memory ラッパー: ログと LangChain の ConversationBufferMemory を同期する簡易アダプタ。

このモジュールは段階的移行のための軽量実装です。将来的には
LangChain の Memory を直接 ConversationChain に渡す構成に置き換えられます。
"""
from __future__ import annotations

from typing import Optional
import os
import json
import datetime

from langchain.memory import ConversationBufferMemory


class ChatMemoryAdapter:
    """会話履歴を保持し、既存ログと同期する簡易アダプタ。

    主なメソッド:
    - load_history_text() -> str: render_conversation_prompt に渡せる履歴テキストを返す
    - add_interaction(user, assistant): メモリに追加し、ログに追記する
    """

    def __init__(self, log_path: Optional[str] = None) -> None:
        # デフォルトのログパスはこのリポジトリの logs/chat_log.jsonl
        if log_path is None:
            log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logs"))
            os.makedirs(log_dir, exist_ok=True)
            log_path = os.path.join(log_dir, "chat_log.jsonl")

        self.log_path = log_path
        # LangChain の ConversationBufferMemory を内部に保持
        self.memory = ConversationBufferMemory(memory_key="history", return_messages=False)

        # 既存ログをロードしてメモリに反映
        self._load_logs_into_memory()

    def _load_logs_into_memory(self) -> None:
        if not os.path.exists(self.log_path):
            return

        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                for line in f:
                    parsed = self._load_log_line(line)
                    if not parsed:
                        continue
                    user, assistant = parsed
                    # try to save into memory; ignore failures but continue
                    self._save_context(user, assistant)
        except Exception:
            # 失敗しても起動を止めない
            return


    def _load_log_line(self, line: str) -> tuple[str, str] | None:
        """ログ行をパースして (user, assistant) を返す。失敗時は None を返す。

        期待する行は JSON で 'prompt' と 'response' を含む。空行や解析エラーは None。
        """
        try:
            line = line.strip()
            if not line:
                return None
            entry = json.loads(line)
            user = entry.get("prompt") or ""
            assistant = entry.get("response") or ""
            if not user and not assistant:
                return None
            return user, assistant
        except Exception:
            return None


    def _save_context(self, user: str, assistant: str) -> bool:
        """メモリへ往復を保存する。成功なら True、失敗なら False を返す。"""
        try:
            self.memory.save_context({"input": user}, {"output": assistant})
            return True
        except Exception:
            return False

    def load_history_text(self) -> str:
        """メモリから履歴テキストを取り出す。

        ConversationBufferMemory の load_memory_variables を使い、"history" キー
        の値（プレーンテキスト）を返します。
        """
        try:
            vars = self.memory.load_memory_variables({})
            return (vars.get("history") or "").strip()
        except Exception:
            return ""

    def add_interaction(self, user: str, assistant: str) -> bool:
        """新しい往復をメモリに保存する。

        Returns:
            True: メモリへの保存に成功
            False: 失敗（内部で例外は吸収される）
        """
        # 内部の _save_context は例外を吸収して True/False を返すため、
        # ここではその戻り値をそのまま返します。
        return self._save_context(user, assistant)


__all__ = ["ChatMemoryAdapter"]
