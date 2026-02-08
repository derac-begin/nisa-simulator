Write-Host "🚀 Starting Safe Build Process..." -ForegroundColor Cyan

# 1. Clean old files
if (Test-Path "index.html") { Remove-Item "index.html" -Force }
Write-Host "🧹 Cleaned old index.html"

# 2. Export new WASM
Write-Host "🔨 Building WASM..."
marimo export html-wasm nisa_calc_v0.19.0.py -o index.html --mode run

# 3. Inject Requirements (The Fix)
$file = "index.html"
if (Test-Path $file) {
    $content = Get-Content -Path $file -Raw -Encoding UTF8
    
    # 修正対象の文字列を探して置換
    $target = '"filename": "notebook.py",'
    $replacement = '"requirements": ["marimo==0.19.0", "pandas", "altair"], "filename": "notebook.py",'
    
    if ($content -match "requirements") {
        Write-Host "⚠️ Requirements already present." -ForegroundColor Yellow
    } else {
        $newContent = $content.Replace($target, $replacement)
        Set-Content -Path $file -Value $newContent -Encoding UTF8
        Write-Host "✅ INJECTED: marimo==0.19.0 requirement fixed!" -ForegroundColor Green
    }
} else {
    Write-Host "❌ Error: index.html was not generated." -ForegroundColor Red
    exit 1
}

Write-Host "🎉 Build Complete. Ready to deploy." -ForegroundColor Cyan