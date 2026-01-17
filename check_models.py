from google import genai

# ==========================================
# APIキー設定
# ==========================================
API_KEY = "AIzaSyDSl1JF9XwNfm86WJesj0Y9KApD7_zNAss"  # ここにあなたのAPIキーを入れてください

client = genai.Client(api_key=API_KEY)

print("🔎 APIキーで利用可能なモデルを検索中...\n")

try:
    for m in client.models.list():
        # "generateContent"（文章生成）に対応しているモデルだけを表示
        if "generateContent" in m.supported_actions:
            # モデル名を表示
            print(f"✅ {m.name}")
            
except Exception as e:
    print(f"❌ エラーが発生しました: {e}")
    print("ヒント: APIキー自体が間違っているか、有効化されていない可能性があります。")