"""
ログ書き出しユーティリティ。
"""

from __future__ import annotations

from typing import Any, List, Optional
import os
import json
import datetime


def merge_raw_lines(raw_lines: List[Any]) -> str:
    parts: List[str] = []
    for item in raw_lines:
        try:
            if isinstance(item, dict) and "response" in item:
                resp_part = item.get("response") or ""
                parts.append(str(resp_part))
            elif isinstance(item, str):
                parts.append(item)
            else:
                parts.append(str(item))
        except Exception:
            continue
    return "".join(parts).strip()


def write_chat_log(model: Optional[str], prompt: str, raw_lines: List[Any], log_path: Optional[str] = None) -> None:
    """ログを `logs/chat_log.jsonl` に追記する。

    Args:
        model: モデル名または None
        prompt: プロンプト文字列（テンプレート適用済み）
        raw_lines: Ollama の生レスポンス断片
        log_path: 異なるログパスを指定する場合に使う
    """
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    log_dir = os.path.abspath(os.path.join(base_dir, "logs"))
    os.makedirs(log_dir, exist_ok=True)
    if log_path is None:
        log_path = os.path.join(log_dir, "chat_log.jsonl")

    merged = merge_raw_lines(raw_lines)
    entry = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "user": "local_cli",
        "model": model,
        "prompt": prompt,
        "response": merged,
    }
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


__all__ = ["write_chat_log"]
