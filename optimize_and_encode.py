import base64
import io
from PIL import Image
import os

# 入力ファイル名
INPUT_IMAGE = "header_nisa_calc.png"
# 出力ファイル名
OUTPUT_TEXT = "optimized_header_base64.txt"

# 目標設定
MAX_WIDTH = 800  # スマホなら幅800pxあれば十分綺麗です
QUALITY = 80     # 画質80% (見た目はほぼ変わらず容量激減)

try:
    # 1. 画像を開く
    with Image.open(INPUT_IMAGE) as img:
        print(f"元画像サイズ: {img.size} / モード: {img.mode}")
        
        # 2. リサイズ (アスペクト比維持)
        if img.width > MAX_WIDTH:
            ratio = MAX_WIDTH / img.width
            new_height = int(img.height * ratio)
            img = img.resize((MAX_WIDTH, new_height), Image.Resampling.LANCZOS)
            print(f"リサイズ後: {img.size}")

        # 3. JPEG変換のためにRGBモードにする (透明度がある場合は白背景にする)
        if img.mode in ('RGBA', 'P'):
            bg = Image.new('RGB', img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
            img = bg

        # 4. メモリ上でJPEG圧縮
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=QUALITY, optimize=True)
        img_bytes = buffer.getvalue()
        
        # 5. Base64エンコード
        encoded_string = base64.b64encode(img_bytes).decode('utf-8')

    # 6. 保存
    with open(OUTPUT_TEXT, "w", encoding="utf-8") as f:
        f.write(encoded_string)

    print("-" * 30)
    print(f"✅ 完了！軽量化されたデータを '{OUTPUT_TEXT}' に保存しました。")
    print(f"📊 文字数: {len(encoded_string):,} 文字")
    
    # サイズ評価
    kb_size = len(encoded_string) / 1000
    print(f"📦 推定サイズ: 約 {kb_size:.1f} KB")
    
    if kb_size > 500:
        print("⚠️ まだ少し大きいです。MAX_WIDTH や QUALITY を下げてみてください。")
    else:
        print("🎉 完璧なサイズです！これをアプリに貼り付けてください。")

except FileNotFoundError:
    print(f"❌ エラー: '{INPUT_IMAGE}' が見つかりません。")
except Exception as e:
    print(f"❌ エラー: {e}")