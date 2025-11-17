#!/bin/bash
# 共有用ZIPファイル作成スクリプト
# 使用方法: ./create_share_zip.sh [タイムスタンプ]
# 例: ./create_share_zip.sh 20251117_132712

# タイムスタンプを引数から取得（省略時は最新のoutputディレクトリを使用）
if [ -n "$1" ]; then
    TIMESTAMP="$1"
else
    # 最新のoutputディレクトリを取得
    TIMESTAMP=$(ls -1 output | grep '^[0-9]\{8\}_[0-9]\{6\}$' | sort -r | head -1)
    if [ -z "$TIMESTAMP" ]; then
        echo "❌ outputディレクトリに実行結果が見つかりません"
        exit 1
    fi
    echo "📁 最新の実行結果を使用: $TIMESTAMP"
fi

OUTPUT_DIR="output/$TIMESTAMP"

# 出力ディレクトリの存在確認
if [ ! -d "$OUTPUT_DIR" ]; then
    echo "❌ ディレクトリが見つかりません: $OUTPUT_DIR"
    exit 1
fi

WORK_DIR="/tmp/face_recognition_share_$$"
ZIP_NAME="output/share_result_${TIMESTAMP}.zip"

echo "========================================="
echo "📦 共有用ZIPファイル作成"
echo "========================================="
echo "実行結果: $OUTPUT_DIR"
echo "出力先: $ZIP_NAME"
echo "========================================="

# 一時作業ディレクトリを作成
rm -rf "$WORK_DIR"
mkdir -p "$WORK_DIR/output"

# HTMLファイルとログをコピー
echo "📄 HTMLファイルをコピー中..."
cp -r "$OUTPUT_DIR" "$WORK_DIR/output/"

# 検索対象ディレクトリ名を取得（後でHTMLのパス修正に使用）
SEARCH_DIR_FOR_PATH=$(grep "検索対象:" "$OUTPUT_DIR/search_log.log" | head -1 | awk '{print $2}')
if [ -z "$SEARCH_DIR_FOR_PATH" ]; then
    SEARCH_DIR_FOR_PATH="../codmon-servicesite-front/"
fi
SEARCH_DIR_BASENAME=$(basename "$SEARCH_DIR_FOR_PATH")

# targetディレクトリをコピー
echo "🎯 targetディレクトリをコピー中..."
cp -r target "$WORK_DIR/"

# 検索対象ディレクトリを特定
SEARCH_DIR=$(grep "検索対象:" "$OUTPUT_DIR/search_log.log" | head -1 | awk '{print $2}')
if [ -z "$SEARCH_DIR" ]; then
    echo "⚠️  検索対象ディレクトリが特定できません。デフォルトを使用します。"
    SEARCH_DIR="../codmon-servicesite-front/"
fi

# 検索対象ディレクトリから画像ファイルのみをコピー
echo "🔍 検索対象ディレクトリから画像をコピー中: $SEARCH_DIR"
if [ -d "$SEARCH_DIR" ]; then
    SEARCH_DIR_NAME=$(basename "$SEARCH_DIR")

    # 画像ファイルのみをコピー（ディレクトリ構造を保持）
    echo "📋 画像ファイルのみコピー中..."
    rsync -a \
        --exclude='node_modules' \
        --exclude='.nuxt' \
        --exclude='.output' \
        --exclude='.git' \
        --include='*/' \
        --include='*.jpg' \
        --include='*.jpeg' \
        --include='*.png' \
        --include='*.gif' \
        --include='*.bmp' \
        --include='*.webp' \
        --include='*.tiff' \
        --exclude='*' \
        "$SEARCH_DIR/" "$WORK_DIR/$SEARCH_DIR_NAME/"

    # HTMLファイル内の画像パスを修正
    echo "🔧 HTMLファイルの画像パスを修正中..."

    # target_images.htmlのパスを修正 (../../../target/ → ../../target/)
    if [ -f "$WORK_DIR/output/$TIMESTAMP/target_images.html" ]; then
        sed -i '' 's|src="../../../target/|src="../../target/|g' "$WORK_DIR/output/$TIMESTAMP/target_images.html"
    fi

    # search_images_*.htmlのパスを修正 (../../../検索dir/ → ../../検索dir/)
    if [ -f "$WORK_DIR/output/$TIMESTAMP/search_images_$SEARCH_DIR_NAME.html" ]; then
        sed -i '' "s|src=\"../../../$SEARCH_DIR_NAME/|src=\"../../$SEARCH_DIR_NAME/|g" "$WORK_DIR/output/$TIMESTAMP/search_images_$SEARCH_DIR_NAME.html"
    fi
else
    echo "⚠️  検索対象ディレクトリが見つかりません: $SEARCH_DIR"
fi

# ZIPファイルを作成
echo "📦 ZIPファイルを作成中..."
cd "$WORK_DIR"
zip -q -r "$(cd - > /dev/null && pwd)/$ZIP_NAME" . -x "*.DS_Store"

# 一時ディレクトリをクリーンアップ
cd - > /dev/null
rm -rf "$WORK_DIR"

echo ""
echo "========================================="
echo "✅ ZIPファイル作成完了！"
echo "========================================="
ls -lh "$ZIP_NAME"
echo ""
echo "📤 Google Driveにアップロードして共有してください。"
echo "========================================="
