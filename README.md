シンプルな Ollama ベースの CLI チャットクライアントです。ローカルの Ollama API を使って対話を行います。


## ConversationChain / PromptTemplate / Memory

### ConversationChain（会話チェーン）とは
- 役割: 複数の処理（プロンプト作成、モデル呼び出し、メモリとのやり取りなど）を順序立てて実行する「パイプライン」です。
- 学べること: Chain の構成方法、入力→出力の受け渡し、既存処理から LangChain のチェーンへ移行する方法。
- 実装ヒント: LangChain の `ConversationChain` は内部で PromptTemplate と Memory を組み合わせて動きます。`ConversationChain` を使うと、個別の処理を自分で書くよりシンプルに会話の順序管理ができます。

### PromptTemplate（プロンプトテンプレート）とは
- 役割: モデルへ渡すテキストをテンプレート化して、可読性・再利用性・テストしやすさを高めるコンポーネントです。
- 学べること: 変数埋め、テンプレートの分割（system / user / example）、テンプレートのユニットテスト化。
- 実装ヒント: 現在 `main.py` に直書きしているプロンプトを `app/prompts.py` に集約し、LangChain の `PromptTemplate` を使って置き換えます。テンプレートには会話のルール（トーン、出力制約）を記述しておくと実験が楽になります。

### Memory（メモリ）とは — コンテクスト保持の仕組み
- 役割: 会話の「状態」を保存・復元するコンポーネントで、ユーザとの過去のやり取りをチェーンに提供します。Memory がコンテクストを保持します。
- 種類: 代表的なものに `ConversationBufferMemory`（直近の発話をバッファする）、`ConversationSummaryMemory`（履歴を要約して保持する）があります。
- 学べること: トークン制限を超えたときの要約戦略、履歴の永続化（ログと Memory の同期）、メモリのスコープ（セッション単位 or 永続的）設計。
- 実装ヒント: 現在の `logs/chat_log.jsonl` を読み書きするように Memory をラップすると、既存のログ保存機能と整合性を取れます。`app/memory.py` を作り、LangChain の Memory インターフェースを実装するアダプタを用意すると将来の切替が容易です。

### ConversationChain と Memory の違い
- ConversationChain: 処理のオーケストレーション（プロンプト生成 → モデル呼び出し → 応答整形 など）を司る。チェーンはフローを管理する。
- Memory: 会話のコンテクスト（過去発話や要約）を保存・供給するデータストア的役割。チェーンの外部からチェーンに状態を与える。

簡単に言うと「Chain がワークフローを動かす司令塔」で、「Memory がその司令塔に与えるコンテクスト（記憶）」です。

### このリポジトリでどこを編集するか（実践ガイド）
- `main.py`: LangChain ベースの起動オプション（例: `--langchain`）を追加して、既存の対話ループと切り替えられるようにします。
- `app/langchain_adapter.py` (新規): 現在の `app/ollama_llm.py` を LangChain の LLM インターフェースに適合させるアダプタを実装します。
- `app/prompts.py` (新規): PromptTemplate を定義して管理します。
- `app/memory.py` (新規): `ConversationBufferMemory` や要約メモリのラッパーを実装し、`logs/chat_log.jsonl` と同期するロジックを入れます。

### 学習の小さなステップ（プラクティス案）
1. `PromptTemplate` を作って template のユニットテストを書く（テンプレートの変数埋めが正しいかを確認）。
2. `langchain_adapter` を作り、簡単な `ConversationChain` を組み立ててローカル LLM に接続する。
3. `ConversationBufferMemory` を導入し、会話中に過去発話が反映されることを確認する。

### 参考実装のミニ契約（例）
- 入力: ユーザー発話 (str)
- 出力: モデル応答 (str)
- 正常条件: PromptTemplate に従ってモデルが応答を返し、Memory が会話を保存すること。


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
