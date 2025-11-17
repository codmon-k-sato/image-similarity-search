# -*- coding: utf-8 -*-
import os
import sys
import glob
import time
import webbrowser
from datetime import datetime
import base64
import io

import numpy as np
from PIL import Image

import torch
import torch.nn as nn
import torchvision.transforms as T
import torchvision.models as models

import faiss  # pip install faiss-cpu

# Google Sheets連携は無効化されています
# import gspread
# from google.oauth2.service_account import Credentials

# ========================================
# 設定変数（ここで変更してください）
# ========================================
TOLERANCE = 0.87  # コサイン類似度の閾値（1.0が完全一致、推奨: 0.70-0.80）
MAX_RESULTS = None  # None にすると制限なし
MAX_TARGET_IMAGES = None  # Target画像の最大数（None = 全て使用）

TOP_K = 5  # FAISS が返す上位 K 件（候補数）。最も類似な1件を使うなら1で可

# Google Sheets設定
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1opng3SCJc4aJbGnXLB7wGc2NNQYnCe6nGtPRPgjackc/edit?gid=0#gid=0"
SPREADSHEET_ID = "1opng3SCJc4aJbGnXLB7wGc2NNQYnCe6nGtPRPgjackc"

# その他の設定
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp")
BATCH_SIZE = 25
ENABLE_SPREADSHEET = False  # Google Sheets連携を無効化
ENABLE_HTML_REPORT = True

# ========================================

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def setup_google_sheets():
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        credentials_path = os.path.join(script_dir, "credentials.json")
        if not os.path.exists(credentials_path):
            print(f"❌ Google Service Account credentials file not found: {credentials_path}")
            print("Skipping Google Sheets output.")
            return None
        credentials = Credentials.from_service_account_file(credentials_path, scopes=SCOPES)
        client = gspread.authorize(credentials)
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        worksheet = spreadsheet.sheet1
        return worksheet
    except Exception as e:
        print(f"❌ Error setting up Google Sheets: {e}")
        return None

def clear_spreadsheet(worksheet):
    try:
        worksheet.clear()
        time.sleep(2)
        return True
    except Exception as e:
        print(f"❌ Error clearing spreadsheet: {e}")
        return False

def write_to_sheet_batch(worksheet, results, batch_size=BATCH_SIZE):
    try:
        if not clear_spreadsheet(worksheet):
            print("⚠️  Failed to clear spreadsheet, but continuing...")
        headers = ["対象画像", "マッチした画像パス", "Similarity"]
        worksheet.update(values=[headers], range_name='A1:C1')
        time.sleep(2)
        if not results:
            return True
        total_batches = (len(results) + batch_size - 1) // batch_size
        for i in range(0, len(results), batch_size):
            batch = results[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            batch_data = []
            for result in batch:
                row = [
                    result['target_image'],
                    result['matched_path'],
                    result['similarity']
                ]
                batch_data.append(row)
            if batch_data:
                start_row = 2 + i
                end_row = start_row + len(batch_data) - 1
                range_name = f"A{start_row}:C{end_row}"
                try:
                    worksheet.update(values=batch_data, range_name=range_name)
                    if batch_num < total_batches:
                        time.sleep(2)
                except Exception as batch_error:
                    print(f"❌ Error writing batch {batch_num}: {batch_error}")
                    time.sleep(5)
                    continue
        return True
    except Exception as e:
        print(f"❌ Error writing to spreadsheet: {e}")
        return False

def image_to_base64(image_path, max_size=(150, 112)):
    """画像をサムネイル化してBase64エンコード"""
    try:
        img = Image.open(image_path)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        buffered = io.BytesIO()
        # RGBに変換（PNGやGIFの透過対応）
        if img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = rgb_img
        img.save(buffered, format="JPEG", quality=75)
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/jpeg;base64,{img_str}"
    except Exception as e:
        print(f"⚠️  Failed to encode {image_path}: {e}")
        return ""

def generate_html_report(results):
    print("📄 Generating HTML report with embedded images...")
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Image Similarity Results (FAISS)</title>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 30px; }}
            .summary {{ background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }}
            .result {{ background: white; margin: 20px 0; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .images {{ display: flex; gap: 30px; align-items: flex-start; flex-wrap: wrap; }}
            .image-container {{ text-align: center; flex: 1; min-width: 250px; }}
            .image-container img {{ max-width: 200px; max-height: 200px; }}
            .image-path {{ font-size: 12px; color: #666; word-break: break-all; margin-top: 5px; background: #f8f9fa; padding: 5px; border-radius: 4px; }}
            .distance {{ font-size: 20px; font-weight: bold; margin: 10px 0; padding: 10px; border-radius: 5px; text-align: center; background: #2196F3; color: white; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔍 Image Similarity Results (FAISS)</h1>
            <p>Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>

        <div class="summary">
            <h2>📊 Summary</h2>
            <p>Total Matches: {len(results)}</p>
            <p>Tolerance (similarity threshold): {TOLERANCE}</p>
        </div>
    """
    # パスを簡略化する関数
    script_dir = os.path.dirname(os.path.abspath(__file__))
    def simplify_path(path):
        """絶対パスを /target/... や /検索dir/... の形式に簡略化"""
        abs_path = os.path.abspath(path)
        # targetディレクトリの場合
        if '/target/' in abs_path:
            return '/target/' + abs_path.split('/target/')[-1]
        # 検索対象ディレクトリの場合（プロジェクトルートの親ディレクトリ内）
        parent_dir = os.path.dirname(script_dir)
        if parent_dir in abs_path and script_dir not in abs_path:
            # 親ディレクトリからの相対パスを取得
            rel_path = os.path.relpath(abs_path, parent_dir)
            return '/' + rel_path
        # その他の場合はファイル名のみ
        return os.path.basename(abs_path)

    for i, result in enumerate(results, 1):
        sim = float(result['similarity'])
        # 画像をBase64エンコード
        target_base64 = image_to_base64(result['target_image_path'])
        matched_base64 = image_to_base64(result['matched_path'])

        # パス表示を簡略化
        target_display_path = simplify_path(result['target_image_path'])
        matched_display_path = simplify_path(result['matched_path'])

        html_content += f"""
        <div class="result">
            <h3>Match #{i} - Similarity: {sim:.3f}</h3>
            <div class="images">
                <div class="image-container">
                    <h4>Target</h4>
                    <img src="{target_base64}" alt="Target Image">
                    <div class="image-path">{target_display_path}</div>
                </div>
                <div class="image-container">
                    <h4>Matched</h4>
                    <img src="{matched_base64}" alt="Matched Image">
                    <div class="image-path">{matched_display_path}</div>
                </div>
            </div>
        </div>
        """
    html_content += """
        <div style="text-align:center; margin:40px 0; padding:20px; background:white; border-radius:10px;">
            <h3>🎉 Report Generated Successfully!</h3>
            <p>このHTMLファイルは画像を埋め込んでいるため、単体で共有可能です。</p>
        </div>
    </body>
    </html>
    """
    # 実行日時ごとのoutputディレクトリを作成
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # 環境変数からタイムスタンプを取得（run_search.shから渡される）
    timestamp = os.environ.get('OUTPUT_TIMESTAMP', datetime.now().strftime('%Y%m%d_%H%M%S'))
    output_dir = os.path.join(script_dir, "output", timestamp)
    os.makedirs(output_dir, exist_ok=True)

    report_path = os.path.join(output_dir, f"image_similarity_faiss_report.html")
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        try:
            file_url = f"file://{os.path.abspath(report_path)}"
            webbrowser.open(file_url)
        except Exception:
            pass
        print(f"✅ HTML report generated: {report_path}")
        return report_path
    except Exception as e:
        print(f"❌ Error generating HTML report: {e}")
        return None

# --------- 特徴抽出 ----------
class FeatureExtractor:
    def __init__(self, device=None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        model = models.resnet50(pretrained=True)
        modules = list(model.children())[:-1]
        self.backbone = nn.Sequential(*modules).to(self.device)
        self.backbone.eval()
        self.transform = T.Compose([
            T.Resize(256),
            T.CenterCrop(224),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406],
                        std=[0.229, 0.224, 0.225])
        ])
        for p in self.backbone.parameters():
            p.requires_grad = False

    def extract(self, image_path):
        img = None
        x = None
        try:
            # 画像ファイルのサイズチェック（大きすぎる場合はスキップ）
            file_size = os.path.getsize(image_path)
            if file_size > 50 * 1024 * 1024:  # 50MB以上はスキップ
                return None

            img = Image.open(image_path).convert("RGB")

            # 画像サイズチェック（大きすぎる場合はスキップ）
            if img.width > 10000 or img.height > 10000:
                if img:
                    img.close()
                return None

            x = self.transform(img).unsqueeze(0).to(self.device)
            with torch.no_grad():
                feats = self.backbone(x)
            feats = feats.squeeze().cpu().numpy().astype('float32')  # 2048
            norm = np.linalg.norm(feats)
            if norm > 0:
                feats = feats / norm

            # メモリを解放
            if img:
                img.close()
            del img, x

            return feats
        except Exception as e:
            # エラー時はメモリを確実に解放
            try:
                if img:
                    img.close()
                if x is not None:
                    del x
            except:
                pass
            return None

def get_images_from_dir(dir_path):
    image_paths = []
    for ext in IMAGE_EXTENSIONS:
        image_paths.extend(glob.glob(os.path.join(dir_path, f"*{ext}")))
        image_paths.extend(glob.glob(os.path.join(dir_path, f"*{ext.upper()}")))
    return sorted(image_paths)

def compute_embeddings_for_list(paths, extractor, show_progress=False):
    embeddings = []
    valid_paths = []
    error_count = 0
    for i, p in enumerate(paths):
        if show_progress and i % 50 == 0:
            print(f"   Processed {i}/{len(paths)} (errors: {error_count})")
        try:
            f = extractor.extract(p)
            if f is not None:
                embeddings.append(f)
                valid_paths.append(p)
            else:
                error_count += 1
        except Exception as e:
            error_count += 1
            continue

    if show_progress and error_count > 0:
        print(f"   ⚠️  Skipped {error_count} problematic images")

    if embeddings:
        return np.vstack(embeddings).astype('float32'), valid_paths
    else:
        return np.array([], dtype='float32').reshape(0,2048), []

# --------- メイン ----------
SEARCH_ROOT = sys.argv[1] if len(sys.argv) > 1 else "."

# 除外ディレクトリを動的に構築
SEARCH_ROOT_ABS = os.path.abspath(SEARCH_ROOT)
EXCLUDED_DIRS = [
    os.path.join(SEARCH_ROOT_ABS, ".nuxt", "dist"),
    os.path.join(SEARCH_ROOT_ABS, "node_modules")
]

script_dir = os.path.dirname(os.path.abspath(__file__))
target_dir = os.path.join(script_dir, "target")

print("=" * 60)
print("🔍 Image Similarity (FAISS accelerated)")
print("=" * 60)
print(f"📊 Settings:")
print(f"   - Similarity threshold: {TOLERANCE}")
print(f"   - Max Results: {MAX_RESULTS if MAX_RESULTS else 'No limit'}")
print(f"   - Max Target Images: {MAX_TARGET_IMAGES if MAX_TARGET_IMAGES else 'No limit'}")
print(f"   - Search Root: {SEARCH_ROOT}")
print(f"   - Target Directory: {target_dir}")
print(f"   - Spreadsheet Output: {ENABLE_SPREADSHEET}")
print(f"   - HTML Report: {ENABLE_HTML_REPORT}")
print("=" * 60)

if not os.path.exists(target_dir):
    print(f"❌ Target directory not found: {target_dir}")
    sys.exit(1)

worksheet = None
if ENABLE_SPREADSHEET:
    worksheet = setup_google_sheets()

# ターゲット埋め込み作成とインデックス構築
target_image_paths = get_images_from_dir(target_dir)
if not target_image_paths:
    print("❌ No target images found.")
    sys.exit(1)

# Target画像数を制限（設定されている場合）
if MAX_TARGET_IMAGES is not None and len(target_image_paths) > MAX_TARGET_IMAGES:
    print(f"ℹ️  Limiting target images from {len(target_image_paths)} to {MAX_TARGET_IMAGES}")
    target_image_paths = target_image_paths[:MAX_TARGET_IMAGES]

extractor = FeatureExtractor()
print(f"🧠 Extracting target features from {len(target_image_paths)} images...")
target_embeddings, valid_target_paths = compute_embeddings_for_list(target_image_paths, extractor, show_progress=True)
if target_embeddings.shape[0] == 0:
    print("❌ Failed to compute target embeddings.")
    sys.exit(1)

dim = target_embeddings.shape[1]  # 2048
# FAISS 内積インデックス（L2 正規化済みベクトルに対して内積がコサイン類似度）
index = faiss.IndexFlatIP(dim)
print(f"📚 Adding {target_embeddings.shape[0]} vectors to FAISS index...")
index.add(target_embeddings)  # ベクトルを追加

# 検索対象画像パスを収集（同名・同階層で拡張子違いは1つだけ）
search_image_paths = []
seen_basenames = {}  # {(dir_path, basename_without_ext): full_path}
for root, _, files in os.walk(SEARCH_ROOT):
    if any(os.path.abspath(root).startswith(excluded) for excluded in EXCLUDED_DIRS):
        continue
    if os.path.abspath(root) == os.path.abspath(target_dir):
        continue
    for file in files:
        if file.lower().endswith(IMAGE_EXTENSIONS):
            full_path = os.path.join(root, file)
            basename_without_ext = os.path.splitext(file)[0]
            key = (root, basename_without_ext)

            # 同じ階層・同じ名前の画像が既にある場合はスキップ
            if key not in seen_basenames:
                seen_basenames[key] = full_path
                search_image_paths.append(full_path)

print(f"🔎 Found {len(search_image_paths)} images to search through.")

results = []
match_count = 0
BATCH_READ = 1  # クエリをバッチで処理（メモリ使用量を抑えるため）
all_similarities = []  # すべての類似度を記録

for i in range(0, len(search_image_paths), BATCH_READ):
    batch_paths = search_image_paths[i:i+BATCH_READ]
    batch_num = i//BATCH_READ + 1
    total_batches = (len(search_image_paths) + BATCH_READ - 1)//BATCH_READ

    # 100画像ごとに進捗表示
    if batch_num % 100 == 1 or batch_num == 1:
        print(f"🔍 Processing image {i+1}/{len(search_image_paths)}...")

    try:
        batch_embeddings, valid_batch_paths = compute_embeddings_for_list(batch_paths, extractor)
    except Exception as batch_error:
        print(f"   ⚠️  Image {i+1} failed, skipping...")
        continue
    if batch_embeddings.shape[0] == 0:
        continue
    # FAISS による検索（内積なので高いほど類似）
    # k = TOP_K（候補数）
    D, I = index.search(batch_embeddings, TOP_K)  # D: (b, k) similarities, I: (b, k) indices
    for bi in range(D.shape[0]):
        if MAX_RESULTS and match_count >= MAX_RESULTS:
            break
        sims = D[bi]  # shape (k,)
        idxs = I[bi]
        # 最も類似な候補（k=TOP_Kのうちの1つ）が閾値以上なら記録
        best_k = int(np.argmax(sims))
        best_sim = float(sims[best_k])
        best_idx = int(idxs[best_k])

        # すべての類似度を記録
        all_similarities.append(best_sim)
        if best_sim >= TOLERANCE:
            matched_target_path = valid_target_paths[best_idx]
            matched_target_name = os.path.basename(matched_target_path)
            matched_search_path = valid_batch_paths[bi]
            match_count += 1
            print(f"✅ Match {match_count}: {matched_search_path}  <->  {matched_target_name}  (sim={best_sim:.3f})")
            results.append({
                'target_image': matched_target_name,
                'target_image_path': matched_target_path,
                'matched_path': matched_search_path,
                'similarity': f"{best_sim:.3f}"
            })
            if MAX_RESULTS and match_count >= MAX_RESULTS:
                break

print("🏁 Search completed.")
print(f"📊 Total matches found: {len(results)}")

# 類似度の統計情報を表示
if all_similarities:
    all_similarities_arr = np.array(all_similarities)
    print(f"\n📈 Similarity Statistics:")
    print(f"   - Max similarity: {np.max(all_similarities_arr):.4f}")
    print(f"   - Mean similarity: {np.mean(all_similarities_arr):.4f}")
    print(f"   - Median similarity: {np.median(all_similarities_arr):.4f}")
    print(f"   - Min similarity: {np.min(all_similarities_arr):.4f}")
    print(f"   - Threshold: {TOLERANCE}")
    # 上位10件を表示
    top_10_idx = np.argsort(all_similarities_arr)[-10:][::-1]
    print(f"\n🔝 Top 10 similarities:")
    for idx in top_10_idx:
        if idx < len(search_image_paths):
            print(f"   - {all_similarities_arr[idx]:.4f}: {search_image_paths[idx]}")

# 出力
if results:
    if ENABLE_HTML_REPORT:
        report_path = generate_html_report(results)
        if report_path:
            print(f"✅ HTML report available: {os.path.abspath(report_path)}")
    if ENABLE_SPREADSHEET and worksheet:
        print("\n📝 Writing results to Google Sheets...")
        success = write_to_sheet_batch(worksheet, results)
        if success:
            print(f"🔗 Spreadsheet available: {SPREADSHEET_URL}")
        else:
            print("❌ Failed to write to spreadsheet.")
else:
    print("ℹ️ No matches found.")

print("\n" + "=" * 60)
print("✅ Process completed!")
print("=" * 60)
