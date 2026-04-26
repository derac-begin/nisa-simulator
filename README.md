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
| **[💰 Margin Architect](https://derac-begin.github.io/nisa-simulator/margin_architect.html)** | `margin_architect.html`<br>利益防衛ラインを可視化する価格戦略シミュレーター。 | 🟢 Live |
| **[🛡️ Secure QR Batch Maker (QRコード一括生成くん)](https://derac-begin.github.io/nisa-simulator/qr_batch.html)** | `qr_batch.html`<br>CSVファイルを読み込み、複数のQRコードを瞬時に一括生成してZIPファイルとしてダウンロードできるユーティリティアプリ。 | 🟢 Live |
| **[🔒 Zero-Leak Manuscript Analyzer (絶対秘密保持・ローカル原稿アナライザー)](https://derac-begin.github.io/nisa-simulator/manuscript_analyzer.html)** | `manuscript_analyzer.html`<br>データはブラウザのメモリ上でのみ処理され、機密情報の漏洩リスク0%を保証する完全オフラインの原稿解析アプリ。 | 🟢 Live |
| **[🧹 Zero-Leak Customer Data Cleanser (絶対秘密保持・顧客データクレンザー)](https://derac-begin.github.io/nisa-simulator/data_cleanser.html)** | `data_cleanser.html`<br>情報漏洩リスク0%。PCから一歩もデータを出さずに、バラバラの顧客リストを一瞬で名寄せ・クレンジングする完全オフラインツール。 | 🟢 Live |
| **[📊 WASM-FinCSV Transformer (完全オフライン・金融CSVコンバーター)](https://derac-begin.github.io/nisa-simulator/fin_transformer.html)** | `fin_transformer.html`<br>情報漏洩リスク0%。機密性の高い金融系CSVデータを、安全かつ瞬時に変換・フォーマット整形するツール。 | 🟢 Live |
| **[💪 PFC Balance Simulator (完全オフライン・パーソナル栄養管理)](https://derac-begin.github.io/nisa-simulator/pfc_simulator.html)** | `pfc_simulator.html`<br>情報漏洩リスク0%。体重・体脂肪率・活動レベルから基礎代謝を自動計算し、目標達成に向けた最適なタンパク質・脂質・炭水化物の摂取量をリアルタイムで可視化する栄養管理アプリ。 | 🟢 Live |
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
├── src/                # Python Source Codes (v0.19.0 のみ)
├── *.html              # Deployed Applications (WASM Build)
├── .gitignore          # 開発環境・レガシーファイルの隠蔽
└── .nojekyll           # GitHub Pages Bypass (必須インフラ)
```

---

## ⚠️ Disclaimer

本リポジトリで公開されている計算ツール（金融・健康計算等）の結果は、あくまでシミュレーションであり、実際の数値を保証するものではありません。利用によって生じた損害等について、開発者は一切の責任を負いません。

## 💼 開発のご依頼・作成ツールの提供について
「情報漏洩0%・完全オフライン」を前提とした WASM (WebAssembly) アプリの開発や、業務効率化ツールの制作はココナラにて承っております。
過去に開発したツール（金融CSV変換、PFCシミュレータ等）もこちらで公開していますので、ぜひご覧ください。
**[👉 ココナラ マイページ / ポートフォリオはこちら](https://coconala.com/users/423965)**

## ブログ
- **技術ブログ（Qiita）**: [https://qiita.com/derac-begin](https://qiita.com/derac-begin)

## SNS(趣味用アカウント)
- **Threads**: [https://www.threads.com/@mont_belle3](https://www.threads.com/@mont_belle3)
- **Instagram**: [https://www.instagram.com/mont_belle3/](https://www.instagram.com/mont_belle3/)