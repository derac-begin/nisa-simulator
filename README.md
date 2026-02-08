# 🚀 Serverless Python Apps

このリポジトリは、Python (`marimo`) で作成されたアプリケーションを WebAssembly (WASM) に変換し、GitHub Pages 上でサーバーレス運用しているプロジェクトです。

**Concept:** "Modern Freeze" Strategy (Stable v0.19.0)

---

## 📱 Application List (Live Demos)

ブラウザ上で Python が動作するため、インストール不要で即座に使用可能です。

| App Name | Description | Status |
| :--- | :--- | :--- |
| **[📈 積立NISAシミュレーター](https://derac-begin.github.io/nisa-simulator/)** | `index.html`<br>積立投資の複利効果を可視化するシミュレーター。 | 🟢 Live |
| **[🏠 住宅ローン計算アプリ](https://derac-begin.github.io/nisa-simulator/mortgage.html)** | `mortgage.html`<br>元利均等・元金均等返済の比較シミュレーション。 | 🟢 Live |
| **[💪 PFCバランス計算機](https://derac-begin.github.io/nisa-simulator/pfc.html)** | `pfc.html`<br>ダイエット・増量向けの主要栄養素(PFC)計算ツール。 | 🟢 Live |
| **[📅 AI Shift Scheduler](https://derac-begin.github.io/nisa-simulator/shift_scheduler.html)** | `shift_scheduler.html`<br>スタッフの希望を反映するシフト自動作成ツール。 | 🟢 Live |

---

## 🛠️ Tech Stack

- **Core Framework:** [marimo](https://marimo.io/) (v0.19.0)
- **Runtime:** Pyodide (WebAssembly)
- **Visualization:** Altair, Vega-Lite
- **Data Processing:** Pandas
- **Hosting:** GitHub Pages

---

## 📂 Directory Structure

```text
.
├── assets/             # WASM Assets & CSS
├── src/                # Python Source Codes (v0.19.0)
├── archive/            # Legacy Codes
├── tools/              # Utility Scripts
└── *.html              # Deployed Applications
```

---

## ⚠️ Disclaimer

本リポジトリで公開されている計算ツール（金融・健康計算等）の結果は、あくまでシミュレーションであり、実際の数値を保証するものではありません。利用によって生じた損害等について、開発者は一切の責任を負いません。