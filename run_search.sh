#!/bin/bash
# 顔認識検索スクリプト実行用のラッパー

# 使用方法を表示
if [ $# -eq 0 ]; then
    echo "使用方法: ./run_search.sh <検索対象ディレクトリ>"
    echo "例: ./run_search.sh ../codmon-servicesite-front/"
    exit 1
fi

# OpenMPライブラリの競合を回避
export KMP_DUPLICATE_LIB_OK=TRUE

# Pythonパス
PYTHON="/Users/k_sato/.pyenv/versions/3.10.13/bin/python"

# スクリプトのディレクトリに移動
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# タイムスタンプを生成（実行日時ごとのディレクトリ名）
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# タイムスタンプを環境変数としてエクスポート（Pythonスクリプトで使用）
export OUTPUT_TIMESTAMP="$TIMESTAMP"

# 実行日時ごとのoutputディレクトリを作成
OUTPUT_DIR="$SCRIPT_DIR/output/$TIMESTAMP"
mkdir -p "$OUTPUT_DIR"

# ログファイルパス
LOG_FILE="$OUTPUT_DIR/search_log.log"

echo "========================================="
echo "🔍 顔認識検索を開始します"
echo "========================================="
echo "検索対象: $1"
echo "出力先: $OUTPUT_DIR"
echo "ログファイル: $LOG_FILE"
echo "========================================="
echo ""

# 実行
$PYTHON -u image_similarity_faiss.py "$1" 2>&1 | tee "$LOG_FILE"

# 画像一覧HTMLも生成
echo ""
echo "📸 画像一覧HTMLを生成中..."
$PYTHON -u create_image_list.py "$1" "$TIMESTAMP" 2>&1 | tee -a "$LOG_FILE"

# 結果を表示
echo ""
echo "========================================="
echo "✅ 検索が完了しました"
echo "========================================="
echo "ログファイル: $LOG_FILE"

# HTMLレポートを確認
HTML_REPORT="$OUTPUT_DIR/image_similarity_faiss_report.html"
if [ -f "$HTML_REPORT" ]; then
    echo "HTMLレポート: $HTML_REPORT"
    echo ""
    echo "ブラウザで自動的に開かれます..."
else
    echo "HTMLレポートが生成されませんでした。"
fi

echo ""
echo "すべての結果は $OUTPUT_DIR に保存されています。"
