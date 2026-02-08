import os
import subprocess

# 設定
SOURCE_PY = "nisa_calc_v0.19.0.py"
OUTPUT_HTML = "index.html"

print(f"🚀 Starting Build Factory for {SOURCE_PY}...")

# 1. クリーンアップ (古いファイルを削除)
if os.path.exists(OUTPUT_HTML):
    os.remove(OUTPUT_HTML)
    print("🧹 Cleaned old HTML.")

# 2. marimo export コマンドの実行
print("🔨 Building raw HTML...")
try:
    subprocess.run(
        ["marimo", "export", "html-wasm", SOURCE_PY, "-o", OUTPUT_HTML, "--mode", "run"],
        check=True,
        shell=True
    )
except subprocess.CalledProcessError:
    print("❌ Error: Build failed.")
    exit(1)

# 3. 要件定義の注入 (Pythonによる精密外科手術)
print("💉 Injecting requirements...")
with open(OUTPUT_HTML, "r", encoding="utf-8") as f:
    content = f.read()

# 置換ターゲット（v0.19.0のデフォルト出力に基づく）
target_str = '"filename": "notebook.py",'
# 注入する文字列（JSON構文を絶対に壊さない形式）
inject_str = '"requirements": ["marimo==0.19.0", "pandas", "altair"], "filename": "notebook.py",'

if target_str in content:
    new_content = content.replace(target_str, inject_str)
    
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("✅ SUCCESS: Requirements injected correctly!")
else:
    print("⚠️ WARNING: Target string not found. Check the raw HTML.")

print("🎉 Process Complete.")