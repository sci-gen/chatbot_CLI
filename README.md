シンプルな Ollama ベースの CLI チャットクライアントです。ローカルの Ollama API を使って対話を行います。

## 目的
- 最小限の CLI で会話できることを目標にしています。

## セットアップ
1. Python 3.10 を用意します（システムに複数バージョンある場合は `python3.10` を使ってください）。
2. 仮想環境を作成して有効化します:

```bash
python3.10 -m venv .venv
source .venv/bin/activate
```

3. 依存をインストールします（最小限の依存のみを `requirements.txt` に記載しています）:

```bash
pip install -r requirements.txt
```

## 実行方法
```bash
source .venv/bin/activate
python main.py
```

コマンドライン引数や環境変数でモデル名や temperature、OLLAMA ホストを変更できます（`main.py` の引数参照）。

## 環境変数
- `OLLAMA_HOST` — Ollama サーバの URL（デフォルト: `http://127.0.0.1:11434`）。

## ログ
- 会話ログは `logs/chat_log.jsonl` に JSON Lines 形式で保存されます（各行が1セッションまたは1エントリ）。
- 現在の `logs/chat_log.jsonl` はマージ済みの `response` フィールドを持つ人間可読なログです。過去に NDJSON ストリームの断片（raw fragments）をそのまま書き出していたログがある可能性がありますが、現状の実装ではストリーム断片はセッション中に一時的に保持され、ログには統合された `response` が書かれます。
