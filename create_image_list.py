#!/usr/bin/env python3
"""
画像一覧HTMLを生成するスクリプト
"""
import os
import sys
import glob
from datetime import datetime

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp")

def get_images_from_dir(dir_path, excluded_dirs=None):
    """ディレクトリから画像ファイルを再帰的に取得（同名・同階層で拡張子違いは1つだけ）"""
    image_paths = []
    excluded_dirs = excluded_dirs or []
    seen_basenames = {}  # {(dir_path, basename_without_ext): full_path}

    for root, dirs, files in os.walk(dir_path):
        # 除外ディレクトリをスキップ
        if any(os.path.abspath(root).startswith(excluded) for excluded in excluded_dirs):
            continue

        for file in files:
            if file.lower().endswith(IMAGE_EXTENSIONS):
                full_path = os.path.join(root, file)
                basename_without_ext = os.path.splitext(file)[0]
                key = (root, basename_without_ext)

                # 同じ階層・同じ名前の画像が既にある場合はスキップ
                if key not in seen_basenames:
                    seen_basenames[key] = full_path
                    image_paths.append(full_path)

    return sorted(image_paths)

def generate_image_list_html(image_paths, title, output_path, base_dir=None):
    """画像一覧HTMLを生成"""
    html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        h1 {{
            color: #333;
            text-align: center;
            margin-bottom: 10px;
            font-size: 2.5em;
        }}
        .stats {{
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-size: 1.1em;
        }}
        .image-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
            gap: 10px;
            margin-top: 30px;
        }}
        .image-card {{
            background: white;
            border-radius: 6px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        .image-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.2);
        }}
        .image-wrapper {{
            width: 100%;
            height: 100px;
            overflow: hidden;
            background: #f5f5f5;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .image-wrapper img {{
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }}
        .image-info {{
            padding: 8px;
            background: #fafafa;
        }}
        .image-name {{
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
            word-break: break-all;
            font-size: 0.9em;
        }}
        .image-path {{
            color: #666;
            font-size: 0.75em;
            word-break: break-all;
            margin-top: 5px;
        }}
        .image-size {{
            color: #999;
            font-size: 0.8em;
            margin-top: 5px;
        }}
        .filter-section {{
            margin: 20px 0;
            text-align: center;
        }}
        .filter-input {{
            padding: 10px 20px;
            font-size: 1em;
            border: 2px solid #ddd;
            border-radius: 25px;
            width: 300px;
            outline: none;
        }}
        .filter-input:focus {{
            border-color: #667eea;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <div class="stats">
            全 <strong>{len(image_paths)}</strong> 枚の画像
        </div>

        <div class="filter-section">
            <input type="text" id="filter" class="filter-input" placeholder="ファイル名で絞り込み...">
        </div>

        <div class="image-grid" id="imageGrid">
"""

    for i, img_path in enumerate(image_paths):
        # 表示用の相対パス（パス表示用）
        if base_dir:
            try:
                rel_path = os.path.relpath(img_path, base_dir)
            except:
                rel_path = img_path
        else:
            rel_path = img_path

        img_name = os.path.basename(img_path)

        # ファイルサイズを取得
        try:
            file_size = os.path.getsize(img_path)
            if file_size < 1024:
                size_str = f"{file_size} B"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size / 1024:.1f} KB"
            else:
                size_str = f"{file_size / (1024 * 1024):.2f} MB"
        except:
            size_str = "Unknown"

        # HTMLファイルからの相対パスを計算（画像参照用）
        # output_pathは後で設定されるので、ここでは計算できない
        # 一旦絶対パスを保持しておき、後で置換する
        abs_path = os.path.abspath(img_path)

        html_content += f"""
            <div class="image-card" data-name="{img_name.lower()}">
                <div class="image-wrapper">
                    <img src="__ABS_PATH__{abs_path}" alt="{img_name}" loading="lazy">
                </div>
                <div class="image-info">
                    <div class="image-name">{img_name}</div>
                    <div class="image-path">{rel_path}</div>
                    <div class="image-size">{size_str}</div>
                </div>
            </div>
"""

    html_content += """
        </div>
    </div>

    <script>
        // フィルタリング機能
        document.getElementById('filter').addEventListener('input', function(e) {
            const filterValue = e.target.value.toLowerCase();
            const cards = document.querySelectorAll('.image-card');

            cards.forEach(card => {
                const name = card.getAttribute('data-name');
                if (name.includes(filterValue)) {
                    card.style.display = '';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    </script>
</body>
</html>
"""

    # HTMLファイルの保存先ディレクトリを取得
    html_dir = os.path.dirname(os.path.abspath(output_path))

    # 絶対パスを相対パスに置換
    import re
    def replace_abs_path(match):
        abs_path = match.group(1)
        try:
            # HTMLファイルからの相対パスを計算
            rel_path = os.path.relpath(abs_path, html_dir)
            return f'src="{rel_path}"'
        except:
            # 相対パス計算に失敗した場合は絶対パスを維持
            return f'src="{abs_path}"'

    html_content = re.sub(r'src="__ABS_PATH__([^"]+)"', replace_abs_path, html_content)

    # ファイルに書き込み
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    return output_path

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 引数で検索ディレクトリとタイムスタンプを受け取る
    # 使用方法: python create_image_list.py [検索ディレクトリ] [タイムスタンプ]
    search_dir = sys.argv[1] if len(sys.argv) > 1 else "../codmon-servicesite-front/"
    timestamp = sys.argv[2] if len(sys.argv) > 2 else datetime.now().strftime('%Y%m%d_%H%M%S')

    # タイムスタンプディレクトリに保存
    output_root = os.path.join(script_dir, "output", timestamp)
    os.makedirs(output_root, exist_ok=True)

    print("=" * 60)
    print("📸 画像一覧HTML生成ツール")
    print("=" * 60)

    # 1. targetディレクトリの画像一覧（output直下に保存）
    target_dir = os.path.join(script_dir, "target")
    if os.path.exists(target_dir):
        print(f"\n🎯 Targetディレクトリの画像を収集中...")
        target_images = get_images_from_dir(target_dir)
        print(f"   見つかった画像: {len(target_images)}枚")

        if target_images:
            target_output = os.path.join(output_root, "target_images.html")
            generate_image_list_html(
                target_images,
                "Target画像一覧",
                target_output,
                base_dir=target_dir
            )
            print(f"   ✅ HTML生成: {target_output}")
        else:
            print(f"   ⚠️  画像が見つかりませんでした")
    else:
        print(f"\n⚠️  Targetディレクトリが見つかりません: {target_dir}")

    # 2. 検索対象ディレクトリの画像一覧（output直下に保存、ディレクトリ名を含む）
    search_dir_abs = os.path.abspath(search_dir)

    if os.path.exists(search_dir_abs):
        print(f"\n🔍 検索対象ディレクトリの画像を収集中...")
        print(f"   ディレクトリ: {search_dir}")

        # 除外ディレクトリを設定
        excluded_dirs = [
            os.path.join(search_dir_abs, ".nuxt", "dist"),
            os.path.join(search_dir_abs, "node_modules")
        ]

        search_images = get_images_from_dir(search_dir_abs, excluded_dirs)
        print(f"   見つかった画像: {len(search_images)}枚")

        if search_images:
            # ディレクトリ名をファイル名に含める
            dir_name = os.path.basename(search_dir_abs)
            search_output = os.path.join(output_root, f"search_images_{dir_name}.html")
            generate_image_list_html(
                search_images,
                f"検索対象画像一覧 - {dir_name}",
                search_output,
                base_dir=search_dir_abs
            )
            print(f"   ✅ HTML生成: {search_output}")
        else:
            print(f"   ⚠️  画像が見つかりませんでした")
    else:
        print(f"\n⚠️  検索対象ディレクトリが見つかりません: {search_dir}")

    print("\n" + "=" * 60)
    print("✅ 処理完了！")
    print("=" * 60)
    print(f"\n出力先: {output_root}/")

if __name__ == "__main__":
    main()
