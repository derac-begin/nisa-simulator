import base64
import os

# 画像ファイル名
IMAGE_PATH = "header_nisa_calc.png"
# 保存するテキストファイル名
OUTPUT_FILE = "header_base64.txt"

try:
    # 1. 画像を読み込んでBase64変換
    with open(IMAGE_PATH, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    
    # 2. テキストファイルに書き出し（UTF-8）
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(encoded_string)
        
    print(f"✅ 成功！Base64文字列を '{OUTPUT_FILE}' に保存しました。")
    print(f"   - 文字数: {len(encoded_string):,} 文字")
    print("   - このファイルを開いて、中身を「すべて選択(Ctrl+A)」してコピーしてください。")
    
except FileNotFoundError:
    print(f"❌ エラー: '{IMAGE_PATH}' が見つかりません。同じフォルダに画像を置いてください。")
except Exception as e:
    print(f"❌ エラーが発生しました: {e}")