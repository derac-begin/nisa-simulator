import os
from google import genai # 新しいライブラリのインポート方法
from dotenv import load_dotenv  # 追加

# .envファイルを読み込む
load_dotenv()

# ==========================================
# 1. 設定エリア
# ==========================================
# コードからキーを消し、環境変数から取得する
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("APIキーが見つかりません。.envファイルを確認してください。")

# 操作対象のファイル名
TARGET_FILE = "bodymake_app.py"

# Geminiの設定（クライアント初期化）
client = genai.Client(api_key=API_KEY)

# ==========================================
# 2. Mini-Opal のロジック (New SDK Version)
# ==========================================
def read_file(filepath):
    """現在のコードを読み込む"""
    if not os.path.exists(filepath):
        return ""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

def write_file(filepath, content):
    """新しいコードを書き込む"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

def main():
    print(f"💎 Mini-Opal (v2.0) 起動: 対象ファイル [{TARGET_FILE}]")
    
    # 1. 現在のコードを読み取る
    current_code = read_file(TARGET_FILE)
    if not current_code:
        print(f"エラー: {TARGET_FILE} が見つかりません。")
        return

    # 2. ユーザー指示
    print("-" * 40)
    user_instruction = input("指示を入力してください (例: BMIの計算機能も追加して): \n>> ")
    if not user_instruction:
        return

    print("\n🤔 Geminiが思考中...")

    # 3. プロンプト作成
    prompt = f"""
    あなたは優秀なPythonエンジニアです。marimoというライブラリを使っています。
    以下のPythonコードを、ユーザーの指示に従って修正し、
    **修正後の完全なPythonコードのみ**を出力してください。
    Markdownのコードブロック（```python ... ```）は不要です。
    説明も不要です。コードの中身だけを返してください。

    【現在のコード】
    {current_code}

    【ユーザーの指示】
    {user_instruction}
    """

    # 4. APIを実行（ここが最新の書き方です）
    try:
        # モデル名を "gemini-3-flash-preview" に変更！
        response = client.models.generate_content(
            model="gemini-3-flash-preview", 
            contents=prompt
        )
        new_code = response.text
        
        # 簡易クリーニング
        new_code = new_code.replace("```python", "").replace("```", "").strip()

    except Exception as e:
        print(f"APIエラーが発生しました: {e}")
        # もしモデル名エラーが出る場合は、利用可能なモデル一覧を表示するヒント
        if "404" in str(e):
            print("ヒント: 'gemini-1.5-flash' が使えない可能性があります。")
        return

    # 5. 安全弁：確認
    print("-" * 40)
    print("✨ 生成されたコードのプレビュー（先頭5行）:")
    print("\n".join(new_code.split("\n")[:5]))
    print("...")
    print("-" * 40)
    
    confirm = input(">> このコードで上書きしてよろしいですか？ (y/n): ")

    # 6. 実装
    if confirm.lower() == "y":
        write_file(TARGET_FILE, new_code)
        print(f"✅ {TARGET_FILE} を更新しました！ブラウザを確認してください。")
    else:
        print("❌ 更新をキャンセルしました。")

if __name__ == "__main__":
    main()