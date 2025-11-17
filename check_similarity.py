#!/usr/bin/env python3
"""
2つの画像の類似度を計算するスクリプト
"""
import os
import sys
import numpy as np
from PIL import Image
import torch
import torchvision.transforms as T
import torchvision.models as models

class FeatureExtractor:
    def __init__(self):
        self.device = torch.device("cpu")
        self.backbone = models.resnet50(pretrained=True)
        self.backbone = torch.nn.Sequential(*(list(self.backbone.children())[:-1]))
        self.backbone = self.backbone.to(self.device)
        self.backbone.eval()

        self.transform = T.Compose([
            T.Resize((224, 224)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406],
                        std=[0.229, 0.224, 0.225])
        ])
        for p in self.backbone.parameters():
            p.requires_grad = False

    def extract(self, image_path):
        try:
            img = Image.open(image_path).convert("RGB")
            x = self.transform(img).unsqueeze(0).to(self.device)
            with torch.no_grad():
                feats = self.backbone(x)
            feats = feats.squeeze().cpu().numpy().astype('float32')
            norm = np.linalg.norm(feats)
            if norm > 0:
                feats = feats / norm
            img.close()
            return feats
        except Exception as e:
            print(f"Error processing {image_path}: {e}")
            return None

def cosine_similarity(vec1, vec2):
    """コサイン類似度を計算"""
    return np.dot(vec1, vec2)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("使用方法: python check_similarity.py <画像1のパス> <画像2のパス>")
        sys.exit(1)

    image1_path = sys.argv[1]
    image2_path = sys.argv[2]

    if not os.path.exists(image1_path):
        print(f"❌ 画像1が見つかりません: {image1_path}")
        sys.exit(1)

    if not os.path.exists(image2_path):
        print(f"❌ 画像2が見つかりません: {image2_path}")
        sys.exit(1)

    print("=" * 60)
    print("🔍 画像類似度チェック")
    print("=" * 60)
    print(f"画像1: {image1_path}")
    print(f"画像2: {image2_path}")
    print("=" * 60)

    extractor = FeatureExtractor()

    print("🧠 特徴抽出中...")
    feat1 = extractor.extract(image1_path)
    feat2 = extractor.extract(image2_path)

    if feat1 is None or feat2 is None:
        print("❌ 特徴抽出に失敗しました")
        sys.exit(1)

    similarity = cosine_similarity(feat1, feat2)

    print("=" * 60)
    print(f"📊 コサイン類似度: {similarity:.6f}")
    print("=" * 60)

    # 判定を表示
    if similarity >= 0.90:
        print("✅ 非常に類似している（0.90以上）")
    elif similarity >= 0.80:
        print("🟡 類似している（0.80-0.90）")
    elif similarity >= 0.70:
        print("🟠 やや類似している（0.70-0.80）")
    else:
        print("❌ 類似度が低い（0.70未満）")
