# image_to_base64.py
import base64

# 画像ファイル名（必要に応じて変更してください）
IMAGE_PATH = "header_nisa_calc.png"

try:
    with open(IMAGE_PATH, "rb") as image_file:
        # 画像を読み込んでBase64エンコード
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        
    print("--- 以下の文字列をコピーしてください ---")
    print(encoded_string)
    print("---------------------------------------")
    
except FileNotFoundError:
    print(f"エラー: {IMAGE_PATH} が見つかりません。ファイル名を確認してください。")