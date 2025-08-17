"""
最小限の対話型 CLI 実行スクリプト。

ローカルの OllamaLLM を使って対話を行います。サーバ起動用の処理は削除し、
直接 `python main.py` または `python main.py --model MODEL` のようにして使います。
"""

from __future__ import annotations

import argparse
import sys
import traceback
from typing import Optional
import json
import datetime
import os
import re
from typing import Any, List

from app.ollama_llm import OllamaLLM
from app.prompts import render_conversation_prompt
from app.memory import ChatMemoryAdapter
from app.logger import write_chat_log


def build_llm(
    model: Optional[str] = None, temperature: Optional[float] = None
) -> OllamaLLM:
    """OllamaLLM のインスタンスを構築して返す。

    Args:
        model: 使用するモデル名。None の場合は OllamaLLM のデフォルト。
        temperature: 温度パラメータ。None の場合はデフォルトを使用。

    Returns:
        構成済みの OllamaLLM インスタンス。
    """
    llm = OllamaLLM()
    if model:
        llm.model = model
    if temperature is not None:
        llm.temperature = float(temperature)
    return llm


def run_cli(model: Optional[str] = None, temperature: Optional[float] = None) -> None:
    """対話型 CLI を起動する。

    ユーザ入力を受け取り、OllamaLLM に投げて応答を表示する。
    """
    llm = build_llm(model=model, temperature=temperature)
    memory = ChatMemoryAdapter()
    print("対話型 CLI を開始します。終了するには /exit または Ctrl-C を押してください。\n")
    try:
        while True:
            try:
                user_input = input("あなた: ").strip()
            except EOFError:
                print("\n終了します。")
                break

            if not user_input:
                continue
            if user_input.lower() in {"/exit", "/quit"}:
                print("終了します。")
                break

            # 履歴をテンプレートに組み込み
            history_text = memory.load_history_text()
            prompt = render_conversation_prompt(user_input, history_text)

            try:
                # 生ログ（raw_lines）も取得する
                reply, raw_lines = llm.generate_with_raw(prompt)
                # メモリに記録（失敗したら警告）
                saved = memory.add_interaction(user_input, reply)
                if not saved:
                    print("警告: メモリへの保存に失敗しました。")
                try:
                    write_chat_log(getattr(llm, "model", None), prompt, raw_lines)
                except Exception:
                    # ログ失敗は致命的でない
                    pass
            except Exception as exc:
                print(f"エラー: {exc}")
                print(traceback.format_exc())
                continue

            # モデル名を短縮表示: 'namespace/mistral:latest' -> 'mistral'
            raw_model = getattr(llm, "model", None) or "Bot"
            try:
                short_model = raw_model.split("/")[-1].split(":")[0]
                model_label = short_model or raw_model
            except Exception:
                model_label = raw_model
            print(f"{model_label}: {reply}\n")
    except KeyboardInterrupt:
        print("\n中断しました。")


def parse_args(argv: list[str]) -> argparse.Namespace:
    """コマンドライン引数をパースする（CLI 用、サーバ関係は削除）。"""
    parser = argparse.ArgumentParser(description="シンプルな対話型 CLI (Ollama)")
    parser.add_argument("--model", type=str, help="使用するモデル名 (例: mistral:latest)")
    parser.add_argument("--temperature", type=float, help="生成の温度 (例: 0.2)")
    return parser.parse_args(argv)


def merge_raw_lines(raw_lines: List[Any]) -> str:
    """raw_lines (parsed objects or raw strings) から連続する 'response' を結合して1つの文字列を返す。"""
    parts: List[str] = []
    for item in raw_lines:
        try:
            if isinstance(item, dict) and "response" in item:
                resp_part = item.get("response") or ""
                parts.append(str(resp_part))
            elif isinstance(item, str):
                parts.append(item)
            else:
                # Unknown type: stringify
                parts.append(str(item))
        except Exception:
            continue
    return "".join(parts).strip()


def write_chat_log(llm: OllamaLLM, prompt: str, raw_lines: List[Any]) -> None:
    """ログを `chatbot_CLI/logs/chat_log.jsonl` に追記する。

    raw_lines をマージして 'response' フィールドに入れる。
    セキュリティとログ肥大化を避けるため、元の生の raw_lines はログに書き込みません。
    """
    log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "logs"))
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "chat_log.jsonl")

    merged = merge_raw_lines(raw_lines)
    entry = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "user": "local_cli",
        "model": getattr(llm, "model", None),
        "prompt": prompt,
        "response": merged,
    }
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main(argv: Optional[list[str]] = None) -> None:
    """エントリポイント。シンプルに CLI を起動する。"""
    args = parse_args(sys.argv[1:] if argv is None else argv)
    run_cli(model=getattr(args, "model", None), temperature=getattr(args, "temperature", None))


if __name__ == "__main__":
    main()
