# 楽天ROOMアイテムマネージャー

## 📖 プロジェクトについて

楽天ROOMに投稿する商品の管理を、自分用に効率化するためのWebツールです。

同じようなニーズがある方の参考になればと思い、最小限の構成で公開しています。

**開発について:**
一部のコーディングやテストに [Claude Code](https://claude.ai/code) を利用しています。

## 🔧 メンテナンス方針

このリポジトリは個人用ツールを参考までに公開しているもので、**積極的なメンテナンスは行っていません**。

必要に応じてフォークし、自由にカスタマイズしてご利用ください。

## 🎯 主要機能

- **プロフィール管理**: ROOMの方向性・ターゲット・投稿スタイルを設定
- **商品管理**: 商品の登録・編集・削除・検索・フィルタリング
- **画像管理**: 商品画像のアップロード・削除（JPG, PNG, GIF, WebP対応）。アップロード時に1:1クロップ調整が可能
- **オリジナル写真**: オリジナル写真フラグで「#オリジナル写真」を自動付与
- **ゴミ箱機能**: 誤削除を防ぐソフトデリート機能、復元・完全削除が可能
- **AI連携**: OpenAI、Google Gemini、Perplexity、Claude APIを使った商品紹介文の自動生成
- **4つの表示モード**: グリッド、リスト、コンパクト、カレンダー表示に切り替え可能
- **優先度管理**: 投稿優先度を5段階で設定
- **状態管理**: 未投稿/下書き/投稿済み/非公開で商品の状態を管理
- **所持管理**: 所持しているかどうかのフラグ管理
- **投稿履歴管理**: 最大3件の投稿日時を手動で記録・編集・削除可能（JST表示対応）
- **CSVエクスポート・インポート**: データのバックアップと復元（画像パス、オリジナル写真、商品紹介文含む）
- **キーボードショートカット**: 検索、新規登録、表示切替、商品ナビゲーションなど
- **オートメーション連携**: 投稿完了・非公開・再投稿可能マーク API（外部自動化ツールとの連携用）
- **SQLiteデータベース**: 永続化されたデータ保存

## 🚀 クイックスタート

### 0. Poetryのインストール（未インストールの場合）

**Mac/Linux:**

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

インストール後、以下でPATHを通してから `poetry --version` で確認してください:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

ターミナルを開き直しても毎回有効にするには `.zshrc` にも追記します:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc && source ~/.zshrc
```

**Windows (PowerShell):**

```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
```

インストール後、以下でPATHを通してから `poetry --version` で確認してください:

```powershell
$env:PATH = "$env:APPDATA\Python\Scripts;$env:PATH"
```

ターミナルを開き直しても毎回有効にするには、Windowsの「システムの詳細設定」→「環境変数」→ユーザーの `Path` に `%APPDATA%\Python\Scripts` を追加してください。

---

### 1. 依存関係のインストール

**Poetryを使う場合（推奨）:**

```bash
poetry install
```

個別にAI SDKを追加する場合:

```bash
# OpenAI SDK（OpenAI、Perplexity API用）
poetry add openai

# Google Gemini SDK
poetry add google-generativeai

# Anthropic Claude SDK
poetry add anthropic
```

**Poetryを使わない場合:**

まず仮想環境を作成してアクティベートします:

```bash
# Mac/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

次に必要なパッケージをインストール:

```bash
# 基本パッケージ
pip install fastapi uvicorn[standard] sqlalchemy pydantic python-multipart

# AI SDK（必要なものだけインストール）
pip install openai              # OpenAI、Perplexity API用
pip install google-generativeai  # Google Gemini用
pip install anthropic           # Anthropic Claude用
```

### 2. データベース初期化（初回のみ）

```bash
poetry run python scripts/init_db.py
```

### 3. サーバー起動

```bash
./scripts/start.sh
```

または

```bash
poetry run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. アプリケーションにアクセス

- **アプリケーション**: http://localhost:8000
- **APIドキュメント**: http://localhost:8000/docs
- **API ReDoc**: http://localhost:8000/redoc

## 📁 プロジェクト構成

```
rakuten-room-item-manager/
├── frontend/                  # フロントエンド（Alpine.js + TailwindCSS）
│   ├── index.html            # メインHTML（全画面を含む）
│   ├── css/
│   │   └── style.css         # カスタムCSS
│   └── js/
│       └── app-api.js        # Alpine.jsアプリケーションロジック（API版）
├── backend/                   # バックエンド（FastAPI）
│   ├── main.py               # FastAPIメインアプリケーション
│   ├── config.py             # 設定ファイル
│   ├── database.py           # データベース接続
│   ├── models.py             # SQLAlchemyモデル
│   ├── schemas.py            # Pydanticスキーマ
│   ├── prompts.py            # AIプロンプト設定
│   └── api/                  # APIルーター
│       ├── profile.py        # Profile API
│       ├── items.py          # Items API
│       ├── export.py         # Export API
│       └── ai.py             # AI API
├── data/                      # データ保存ディレクトリ
│   └── rakuten_room.db       # SQLiteデータベース
├── images/                    # 商品画像保存ディレクトリ
├── scripts/                   # ユーティリティスクリプト
│   ├── init_db.py            # DB初期化スクリプト
│   └── start.sh              # サーバー起動スクリプト
├── pyproject.toml            # Poetry依存関係管理
└── README.md
```

## 🖥️ 画面構成

### 1. 初回起動画面（プロフィール初期設定）

初回起動時に表示される画面です。最低限必要な情報のみを設定します。

**入力項目:**
- **ROOM名** (必須): あなたのROOMの名前
- **ルームID** (オプション): 設定すると商品一覧画面にルームへのリンクが表示されます

**スキップも可能:**
「スキップ（後で設定）」をクリックすると、ROOM名なしで始められます。

その他の詳細設定（ターゲット層、投稿スタイル、AI連携など）は、後から「設定」メニューで設定できます。

### 2. 商品一覧画面（メイン画面）

登録した商品の一覧を表示し、管理します。

**表示モード:**
- **グリッド表示**: 画像を大きく表示するカード型レイアウト
- **リスト表示**: 詳細情報を含むリスト型レイアウト
- **コンパクト表示**: テーブル形式の最小限表示
- **カレンダー表示**: 投稿履歴をカレンダー形式で表示

**機能:**
- 検索: 商品名・ハッシュタグで検索
- フィルタ: 投稿状況、優先度でフィルタリング
- 新規登録: 商品を追加
- クイック編集: 商品画像または商品名をクリックすると編集モーダルが開く
- 削除: 商品をゴミ箱に移動（ソフトデリート）
- 統計表示: 登録商品数、未投稿数、今週投稿数、ゴミ箱カウント
- CSVエクスポート: 全商品データをCSV形式でダウンロード
- キーボードナビゲーション: 矢印キーで商品間移動、Enterで編集（詳細は後述）
- ゴミ箱: 削除した商品の復元・完全削除

### 3. プロフィール設定画面

ROOMのプロフィール情報とAI連携設定を編集します。設定メニューから2つの設定画面にアクセスできます。

**基本情報設定:**
- ROOM名
- ルームID
- 投稿者名
- ターゲット層
- ROOMの方向性
- ROOMテーマ
- トーン&マナー（親しみやすい/専門的/カジュアル/ていねい/フランク）
- 投稿スタイル
- 使いたくない言葉

**AI連携設定:**
- AI連携の有効/無効
- OpenAI API設定（GPT-4、GPT-3.5など）
- Google Gemini API設定（Gemini Pro、Flashなど）
- Perplexity API設定（Sonar、Llamaモデル）
- Claude API設定（Claude 3.5 Sonnet、Opusなど）

### 4. 商品登録・編集モーダル

商品の詳細情報を登録・編集するモーダルウィンドウです。

**入力項目:**
- **基本情報**: 商品名、カテゴリ、サブカテゴリ、ブランド・型番、所持している（チェックボックス）
- **商品画像**: 画像のアップロード・削除（JPG、PNG、GIF、WebP対応）、オリジナル写真（チェックボックス）
- **使用状況**: 用途・シーン、使用頻度、気に入っているポイント
- **投稿設定**: 投稿状況、優先度、季節性
- **投稿履歴**: 最大3件の投稿日時を追加・編集・削除可能（JST表示）
- **リンク**: 楽天市場URL、ROOM URL
- **商品紹介文**: AI自動生成に対応
- **メモ**: 自由記述

**AI機能:**
- 商品情報とプロフィール設定を基に、AIが商品紹介文を自動生成
- 複数のAIプロバイダーから選択可能
- オリジナル写真にチェックを入れると、生成時に「#オリジナル写真」が自動付与される

**キーボードショートカット:**
- `Ctrl/⌘ + Enter`: 保存
- `Esc`: キャンセル

## 🛠️ 技術スタック

### フロントエンド

- **HTML5**: マークアップ
- **Alpine.js 3.x**: リアクティブなUI構築
- **TailwindCSS**: ユーティリティファーストCSSフレームワーク
- **Vanilla JavaScript**: アプリケーションロジック

**特徴:**
- ビルド不要（CDN経由で読み込み）
- 即座に動作
- 軽量（数千件でも高速）

### バックエンド

- **Python 3.11+**: 開発言語
- **FastAPI 0.110+**: Web APIフレームワーク
- **SQLAlchemy 2.0+**: ORM
- **SQLite 3.x**: データベース
- **Pydantic 2.6+**: バリデーション
- **Uvicorn 0.27+**: ASGIサーバー
- **Poetry 1.7+**: 依存関係管理

**AI SDK:**
- **OpenAI Python SDK**: GPTモデル連携（Perplexity APIもOpenAI互換のため同じSDKを使用）
- **Google Generative AI SDK**: Geminiモデル連携
- **Anthropic SDK**: Claudeモデル連携

**特徴:**
- RESTful API
- 自動APIドキュメント生成（Swagger UI / ReDoc）
- CORS対応
- 型安全（Pydantic）
- 静的ファイル配信

## 📝 使い方

### 1. 初期設定

1. http://localhost:8000 にアクセス
2. プロフィール初期設定画面が表示される
3. ROOM名を入力（ルームIDは任意）
4. 「保存して始める」をクリック

**スキップも可能:**
「スキップ（後で設定）」をクリックすると、ROOM名なしで始められます。後から設定メニューの「基本情報設定」で設定できます。

### 2. AI連携を設定（オプション）

1. ヘッダーの「⚙️ 設定」をクリック
2. 「🤖 AI連携設定」を選択
3. AI連携を有効化
4. 使用したいAIプロバイダーのAPIキーとモデルを設定
5. 「保存」をクリック

### 3. 商品を登録

1. 「➕ 新規登録」ボタンをクリック
2. 商品情報を入力
3. （オプション）画像をアップロード（選択後に1:1クロップ調整画面が表示されます）
4. （オプション）「AI生成」ボタンで商品紹介文を自動生成
5. 「保存」をクリック

### 4. 商品を検索・フィルタ

- **検索**: 検索ボックスに商品名を入力
- **投稿状況フィルタ**: 未投稿、下書き、投稿済み、非公開で絞り込み
- **優先度フィルタ**: ⭐1〜5で絞り込み
- **表示切り替え**: グリッド、リスト、コンパクト、カレンダー表示を切り替え

### 5. 商品を編集・削除

- **クイック編集**: 商品画像または商品名をクリック
- **編集ボタン**: 商品の「編集」ボタンをクリック
- **削除**: 商品の「削除」ボタンをクリック（ゴミ箱へ移動）

### 6. データのエクスポート

1. 「エクスポート」ボタンをクリック
2. CSVファイルがダウンロードされます（ファイル名にタイムスタンプ付き）

### 7. データのインポート

1. 「インポート」ボタンをクリック
2. CSVファイルを選択
3. データが自動的にインポートされます

### 8. ゴミ箱機能

1. 商品を削除すると、ゴミ箱に移動します
2. ヘッダーの「🗑️ ゴミ箱」ボタンをクリック
3. ゴミ箱画面で以下の操作が可能：
   - **復元**: 商品を元に戻す
   - **完全削除**: 商品を永久に削除

### 9. キーボードショートカット

マウスを使わずにキーボードだけで快適に操作できます。

**商品一覧画面:**
- `N`: 新規商品登録
- `/`: 検索フォーカス
- `1`: グリッド表示
- `2`: リスト表示
- `3`: コンパクト表示
- `4`: カレンダー表示
- `Esc`: 商品ナビゲーション開始
- `?`: ショートカットヘルプ表示

**商品ナビゲーションモード:**
- `↑↓←→`: 商品間移動（グリッドは4方向、リスト/コンパクトは上下のみ）
- `Enter`: 選択中の商品を編集
- `D`: 選択中の商品を削除（ゴミ箱へ）
- `Esc`: ナビゲーション解除

**検索フォーカス中:**
- `Esc`: 商品ナビゲーションモードに戻る

**商品編集モーダル:**
- `Ctrl/⌘ + Enter`: 保存
- `Esc`: キャンセル

## 📡 オートメーション連携 API

外部の自動化ツールと連携するためのエンドポイントです。

### 投稿準備済み商品の取得

```
GET /api/export/items/ready-to-post
```

| パラメータ | 型 | 説明 |
|---|---|---|
| `limit` | int | 取得件数（1〜100、デフォルト10） |
| `min_priority` | int | 最低優先度（1〜5） |
| `require_photo` | bool | 画像ありのみ |
| `require_description` | bool | 紹介文ありのみ |
| `original_photo_only` | bool | オリジナル写真のみ |
| `original_photo_first` | bool | オリジナル写真を先頭に並べる |
| `include_posted` | bool | 投稿済みも含める（ローテーション再投稿用） |

### ステータス更新

| エンドポイント | 説明 |
|---|---|
| `PATCH /api/items/{id}/mark-posted` | 投稿済みにマーク。`posted_at`（ISO 8601）と任意で`room_url`をボディに渡す。投稿履歴に追記（最大3件） |
| `PATCH /api/items/{id}/mark-unpublished` | 非公開にマーク。`room_url`をクリア |
| `PATCH /api/items/{id}/mark-available` | 未投稿に戻す（ローテーション削除後の再投稿用）。`room_url`をクリア |

## 🔄 データの管理

**データベース:**
- データは`data/rakuten_room.db`に保存されます

**画像ファイル:**
- アップロードされた画像は`images/`ディレクトリに保存されます
- ファイル名はUUID + 拡張子で自動生成されます（例: `abc123-def456.jpg`）
- **注意**: `images/`ディレクトリは`.gitignore`で除外されているため、Gitリポジトリには含まれません
- 画像を永続化したい場合は、別途バックアップを取るか、クラウドストレージ等への保存が必要です

**バックアップ:**
- CSVエクスポート機能を使って、定期的にデータをバックアップすることをお勧めします

**CSVに含まれる情報:**
- 基本情報（ID、商品名、カテゴリなど）
- 画像情報（画像パス、オリジナル写真フラグ）
- 所持フラグ
- 商品紹介文
- 投稿履歴（最新の1件）
- その他すべてのフィールド

## 🤝 開発環境

### 必要なもの

- Python 3.11+
- Poetry（依存関係管理）
- モダンなWebブラウザ（Chrome、Firefox、Safari、Edgeなど）

### オプション（AI連携を使用する場合）

以下のいずれかのAPIキーが必要です。APIキーの取得方法は各公式サイトをご確認ください。

- [OpenAI API](https://platform.openai.com/api-keys) - GPT-4、GPT-3.5等
- [Google AI Studio](https://aistudio.google.com/app/apikey) - Gemini Pro、Flash等
- [Perplexity API](https://www.perplexity.ai/settings/api) - Sonar、Llama等
- [Anthropic Console](https://console.anthropic.com/settings/keys) - Claude 3.5 Sonnet、Opus等

いずれか1つ以上のAPIキーがあれば、AI連携機能を利用できます。

**注意:** Perplexity APIはOpenAI互換APIのため、OpenAI SDKを使用します。別途SDKのインストールは不要です。

## 🔧 高度な設定（任意）

### AIプロンプトのカスタマイズ

AI生成される商品紹介文のトーンや内容をカスタマイズできます。

**変更方法:**
1. `backend/prompts.py` ファイルを開く
2. 以下の設定を編集:

**基本設定（MASTER_PROMPT_BASE）:**
- 一覧用ファーストビューの文字数（デフォルト: 26文字）
- 商品詳細文の文字数（デフォルト: 200〜350文字）
- ハッシュタグの生成ルール
- 出力形式

**トーン別設定:**
- `TONE_FRIENDLY` - 親しみやすい（デフォルト）
- `TONE_PROFESSIONAL` - 専門的
- `TONE_CASUAL` - カジュアル
- `TONE_POLITE` - ていねい
- `TONE_FRANK` - フランク

各トーンの語尾、表現方法、文体をカスタマイズできます。

**例:** 一覧用ファーストビューを30文字に変更したい場合
```python
# backend/prompts.py の14行目付近
- 26文字まで  # 変更前
- 30文字まで  # 変更後
```

## ⚠️ 注意事項

**プライバシーとセキュリティ:**
- このツールで入力・保存されるデータは、全て利用者のローカルPC上に保存されます
- 開発者（筆者）がデータを収集・閲覧することは一切ありません
- データはデータベースファイル（`data/rakuten_room.db`）に保存されます

**非公式の個人プロジェクト:**
- このツールは**非公式の個人プロジェクト**です。楽天グループ株式会社およびその関連会社とは一切関係ありません。
- 「楽天ROOM」「楽天市場」は楽天グループ株式会社の商標または登録商標です。
- このツールの使用により生じたいかなる損害についても、開発者は責任を負いかねます。

## 📄 ライセンス

MIT License

## 📧 関連リンク

- **note**: https://note.com/ai_fukugyo_tips

同様のテーマに関する記事は note をご覧ください。
