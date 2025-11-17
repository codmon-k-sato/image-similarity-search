# 画像類似度検索ツール

## 概要

`target/`ディレクトリにある画像と類似した画像を指定ディレクトリから検索するツールです。
PyTorchのResNet50とFAISSを使用した高速な画像類似度検索を実行します。

## 主な機能

- **画像類似度検索**: ResNet50で画像特徴を抽出し、FAISSで高速検索
- **重複ファイル処理**: 同名・同階層で拡張子が異なる画像は1つだけ処理
- **HTML出力**: 検索結果、対象画像一覧、検索画像一覧をHTMLで可視化
- **実行ログ管理**: タイムスタンプ付きディレクトリで実行履歴を整理

## セットアップ

### 前提条件

- Python 3.10以上
- pyenv（推奨）またはシステムPython

### 新規環境でのセットアップ

#### 1. Python環境の準備

##### pyenvを使用する場合（推奨）

```bash
# Python 3.10.13をインストール
pyenv install 3.10.13

# このプロジェクトでPython 3.10.13を使用
cd /path/to/face_recognition
pyenv local 3.10.13
```

##### システムPythonを使用する場合

```bash
# Python 3.10以上がインストールされていることを確認
python3 --version
```

#### 2. 必要なライブラリのインストール

```bash
# PyTorchとtorchvisionのインストール
pip install torch torchvision

# FAISSのインストール
pip install faiss-cpu

# その他の依存ライブラリ
pip install numpy pillow opencv-python
```

#### 3. run_search.shのPythonパス設定

`run_search.sh`の15行目を環境に合わせて修正してください：

```bash
# pyenvを使用する場合
PYTHON="$(pyenv which python)"

# または、システムPythonを使用する場合
PYTHON="python3"

# または、特定のパスを指定する場合
PYTHON="$HOME/.pyenv/versions/3.10.13/bin/python"
```

## 参考: 開発環境の例

### Python環境
- **Pythonバージョン**: 3.10.13 (pyenv管理)
- **Pythonパス**: `~/.pyenv/versions/3.10.13/bin/python`

### インストール済みライブラリ
- PyTorch 2.9.1
- torchvision 0.24.1
- FAISS 1.12.0
- NumPy 2.2.6
- Pillow 12.0.0
- OpenCV 4.12.0

## 使用方法

### 事前準備: 検索したい画像の配置

実行前に、`target/`ディレクトリに検索したい画像を配置してください。

- `target/`ディレクトリには、MDが用意した探したい画像（検索の基準となる画像）を配置します
- このディレクトリ内の画像と類似した画像が、指定した検索対象ディレクトリから検索されます
- 対応画像形式: .jpg, .jpeg, .png, .bmp, .gif, .tiff, .webp

**例**:

```bash
target/
├── DSC00211.jpg
├── DSC00214.jpg
└── DSC00221.jpg
```

### 基本的な実行

```bash
# シェルスクリプトを使用（推奨）
./run_search.sh <検索対象ディレクトリ>

# 例
./run_search.sh ../codmon-servicesite-front/
```

### 直接Pythonで実行

```bash
export KMP_DUPLICATE_LIB_OK=TRUE
python image_similarity_faiss.py <検索対象ディレクトリ>
```

### 2枚の画像の類似度を確認

```bash
python check_similarity.py <画像1のパス> <画像2のパス>
```

### 共有用ZIPファイルの作成

検索結果を他の人と共有するためのZIPファイルを作成できます。

```bash
# 最新の実行結果からZIPを作成
./create_share_zip.sh

# 特定のタイムスタンプの実行結果からZIPを作成
./create_share_zip.sh 20251117_143029
```

**作成されるZIPファイル**:
- ファイル名: `output/share_result_<タイムスタンプ>.zip`
- サイズ: 約600MB
- 内容:
  - HTML報告書（画像類似度検索結果、対象画像一覧、検索画像一覧、ログ）
  - target画像 537枚
  - 検索対象ディレクトリの画像ファイルのみ（.jpg, .png, .webp等）
  - ソースコード、node_modules等の不要ファイルは完全に除外

**共有方法**:
1. 作成されたZIPファイルをGoogle Driveにアップロード
2. 共有リンクを作成して送付
3. 受け取った人はZIPを解凍後、`output/<タイムスタンプ>/`内のHTMLファイルをブラウザで開く

**HTMLファイルの特徴**:

- `image_similarity_faiss_report.html`: 画像がBase64埋め込みされているため単体で閲覧可能。パス表示は `/target/...` や `/検索dir/...` の形式で簡潔に表示
- `target_images.html`: 画像ファイルと一緒に解凍する必要あり。相対パスで画像を参照
- `search_images_*.html`: 画像ファイルと一緒に解凍する必要あり。相対パスで画像を参照

## 設定のカスタマイズ

`image_similarity_faiss.py`の26-30行目で以下の設定を変更できます：

```python
TOLERANCE = 0.87  # 類似度の閾値（0.0〜1.0、推奨: 0.80-0.90）
MAX_RESULTS = None  # 最大結果数（None = 無制限）
MAX_TARGET_IMAGES = None  # Target画像の最大数（None = 全て使用）
TOP_K = 5  # FAISS検索の候補数
```

**推奨設定**:
- 類似度閾値: 0.87（現在の設定）
  - 0.90以上: 非常に厳格（ほぼ同一画像のみ）
  - 0.80-0.90: 適切（類似画像を検出）
  - 0.70-0.80: 緩い（やや類似も含む）

## ファイル構成

```
face_recognition/
├── image_similarity_faiss.py  # メイン類似度検索スクリプト
├── create_image_list.py       # 画像一覧HTML生成スクリプト
├── check_similarity.py        # 2画像間の類似度確認ツール
├── run_search.sh              # 実行用シェルスクリプト
├── target/                    # 検索基準となる画像を格納
├── output/                    # 実行結果（タイムスタンプ別）
│   └── YYYYMMDD_HHMMSS/      # 実行日時ごとのディレクトリ
│       ├── image_similarity_faiss_report.html  # 検索結果レポート
│       ├── target_images.html                  # 対象画像一覧
│       ├── search_images_<dir>.html            # 検索画像一覧
│       └── search_log.log                       # 実行ログ
├── .gitignore                 # Git除外設定
└── README.md                  # このファイル
```

## 機能詳細

### 画像の重複処理

同じ階層にある同名で拡張子が異なる画像（例: `image.jpg`と`image.webp`）は、最初に見つかった1つだけが処理されます。これにより：
- 同じ画像の重複検索を防止
- 処理速度の向上
- 結果の見やすさ向上

### 対応画像形式

- `.jpg` / `.jpeg`
- `.png`
- `.bmp`
- `.gif`
- `.tiff`
- `.webp`

### 除外ディレクトリ

以下のディレクトリは自動的に検索対象から除外されます：
- `node_modules`
- `.nuxt/dist`

除外設定は`image_similarity_faiss.py`と`create_image_list.py`で変更可能です。

## 出力

すべての実行結果は`output/YYYYMMDD_HHMMSS/`ディレクトリに保存されます。

### 1. 検索結果レポート (`image_similarity_faiss_report.html`)
- マッチした画像のペアを表示
- 類似度スコアを表示
- 自動的にブラウザで開かれます

### 2. 対象画像一覧 (`target_images.html`)
- `target/`ディレクトリ内の全画像を表示
- 画像のパス情報を含む

### 3. 検索画像一覧 (`search_images_<ディレクトリ名>.html`)
- 検索対象ディレクトリ内の全画像を表示
- 重複除外後の画像一覧

### 4. 実行ログ (`search_log.log`)
- 実行時のすべての出力
- 進捗状況、警告、エラーメッセージ

## 技術詳細

### アルゴリズム

1. **特徴抽出**: ResNet50（ImageNet学習済み）で各画像を2048次元のベクトルに変換
2. **正規化**: L2正規化により、コサイン類似度を内積で計算可能に
3. **インデックス構築**: FAISS IndexFlatIPでTarget画像のインデックスを作成
4. **検索**: 各検索画像の特徴ベクトルをインデックスと照合
5. **フィルタリング**: 類似度が閾値以上の画像のみを結果として返す

### パフォーマンス最適化

- **FAISS使用**: 大量画像でも高速検索
- **バッチ処理**: 複数画像を効率的に処理
- **重複除外**: 同名・同階層の重複画像をスキップ
- **エラー処理**: 大きすぎる画像や破損画像をスキップ
- **メモリ管理**: 適切なメモリ解放

## トラブルシューティング

### 実行時エラー

#### `ModuleNotFoundError: No module named 'torch'`
```bash
pip install torch torchvision
```

#### `ModuleNotFoundError: No module named 'faiss'`
```bash
pip install faiss-cpu
```

#### `Permission denied: ./run_search.sh`
```bash
chmod +x run_search.sh
```

### 検索結果が少ない

1. 類似度閾値（`TOLERANCE`）を下げる（例: 0.87 → 0.80）
2. Target画像が適切か確認
3. 検索対象ディレクトリに画像が存在するか確認

### メモリ不足

1. 検索対象ディレクトリを分割して実行
2. `MAX_TARGET_IMAGES`を設定して対象画像数を制限

## Google Sheets連携

現在は無効化されています（`ENABLE_SPREADSHEET = False`）。
有効化する場合：

1. `image_similarity_faiss.py`の19-21行目のコメントを解除
2. `ENABLE_SPREADSHEET = True`に変更（39行目）
3. `gspread`と`google-auth`をインストール
4. `credentials.json`をプロジェクトルートに配置

## 開発履歴

### 2025-11-14
- 不要なPythonファイルを削除（`show_images.py`, `test_*.py`, `organize_output.py`, `find_person.py`）
- `credentials.json`を削除（Google Sheets連携は無効化済み）
- 類似度閾値を0.87に調整
- README.mdを最新化（新規環境セットアップ手順を追加）

### 2025-11-13
- 初版作成
- Python 3.10.13環境構築
- PyTorch + FAISS実装
- 画像一覧HTML生成機能追加
- タイムスタンプ別ディレクトリ管理実装
- 重複ファイル処理機能追加
- .webp形式対応

## ライセンス

内部利用のため、ライセンスは指定なし
