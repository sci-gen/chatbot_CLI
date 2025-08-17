"""
Ollama 用の LangChain LLM ラッパー

注意: Ollama がローカルで動作しており、対象のモデルが ollama に pull されていることを前提とします。
環境変数:
  OLLAMA_HOST - 例: http://127.0.0.1:11434
  OLLAMA_MODEL - 例: mistral:latest
"""

from typing import Any, List, Mapping, Optional
import os
import requests
import json
from langchain.llms.base import LLM


class OllamaLLM(LLM):
    """LangChain 用の軽量 Ollama LLM ラッパークラス。

    簡単な HTTP 経由で Ollama のローカル API を叩き、レスポンスのテキストを返します。

    属性:
        model: 使用する ollama モデル名（例: "mistral:latest"）
        base_url: Ollama サーバの URL（デフォルト http://127.0.0.1:11434）
        temperature: 出力のランダム性
    """

    model: str = os.getenv("OLLAMA_MODEL", "mistral:latest")
    base_url: str = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    temperature: float = 0.2

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        """プロンプトを送って生成テキストを返す。

        Ollama の現在のレスポンスは NDJSON（行単位の JSON 断片）で返ることがあるため、
        ストリーミングで各行をパースし、"response" フィールドを順に連結して最終結果を返します。
        この実装は内部で generate_with_raw を使います。
        """
        text, _raw = self.generate_with_raw(prompt)
        return text

    def generate_with_raw(self, prompt: str, timeout: int = 120) -> tuple[str, List[object]]:
        """プロンプトを送って、組み立てたテキストと生のレスポンス行リストを返す。

        Returns:
            (text, raw_lines)
            - text: 結合された応答テキスト
            - raw_lines: サーバから受け取った各行を解析したオブジェクトまたは生文字列のリスト
        """
        payload: Mapping[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "temperature": float(self.temperature),
        }

        url = f"{self.base_url.rstrip('/')}/api/generate"
        try:
            with requests.post(url, json=payload, stream=True, timeout=timeout) as resp:
                resp.raise_for_status()
                parts, raw_lines = self._read_stream(resp)

                result = "".join(parts).strip()
                if result:
                    return result, raw_lines
                return resp.text, raw_lines
        except Exception as exc:
            raise RuntimeError(f"Ollama request failed: {exc}")

    def _read_stream(self, resp: requests.Response) -> tuple[List[str], List[object]]:
        """レスポンスのストリームを読み、テキスト断片(parts)と生行(raw_lines)を返す。

        - 各行を JSON パースできればオブジェクトとして raw_lines に追加。
        - 解析できなければ生文字列を raw_lines に追加し、parts にも加える。
        - オブジェクトに 'response' フィールドがあれば順に parts に追加する。
        - オブジェクトに 'done' が立っている場合はループを抜ける。
        """
        parts: List[str] = []
        raw_lines: List[object] = []
        for raw_line in resp.iter_lines(decode_unicode=True):
            if raw_line is None or raw_line == "":
                continue
            # try parse JSON; 成功すればオブジェクトを保存、失敗すれば文字列を保存
            try:
                obj = json.loads(raw_line)
                raw_lines.append(obj)
            except Exception:
                raw_lines.append(raw_line)
                # 解析できない行は応答テキストとしても付与
                parts.append(raw_line)
                continue

            # 'response' フィールドを順に結合
            if isinstance(obj, dict) and "response" in obj:
                resp_part = obj.get("response") or ""
                parts.append(str(resp_part))

            if isinstance(obj, dict) and obj.get("done"):
                break

        return parts, raw_lines

    def _identifying_params(self) -> Mapping[str, Any]:
        """LLM の識別パラメータを返す."""
        return {"model": self.model, "temperature": self.temperature}

    @property
    def _llm_type(self) -> str:
        """LLM 種別を返す（LangChain 内部用）。"""
        return "ollama"
