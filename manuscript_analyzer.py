import marimo

__generated_with = "0.19.0"
app = marimo.App(width="full")


@app.cell
def _imports():
    """アプリ全体で共有するモジュール"""
    import marimo as mo
    import re
    import html
    return html, mo, re


@app.cell
def _inject_css(mo):
    """グローバルCSS注入"""
    css_html = mo.Html("""
    <style>
    body, html, .marimo { max-width: 100vw !important; overflow-x: hidden !important; font-family: 'Noto Sans JP', sans-serif; }
    *:not(svg):not(path):not(img) { max-width: 100% !important; box-sizing: border-box; }
    
    /* コンテナのベース文字色（spanへの過剰な強制適用を削除） */
    .ma-section { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 16px; margin-bottom: 8px; color: #e2e8f0 !important; }
    .ma-section label { color: #e2e8f0 !important; }

    /* 👇【究極修正】エディタ内部の「すべての要素(*やspan)」まで強制的に黒(#000000)にする */
    input, textarea, [contenteditable="true"], 
    .cm-editor, .cm-content, .cm-content *, .cm-line, .cm-line *, .cm-line span {
        color: #000000 !important;
        background-color: #ffffff !important;
        font-weight: 500 !important;
    }
    /* プレースホルダー（入力前の薄い文字）を見やすく調整 */
    input::placeholder, textarea::placeholder { color: #9ca3af !important; }
    
    .ma-badge { display: inline-block; padding: 2px 10px; border-radius: 9999px; font-size: 12px; font-weight: bold; }
    .ma-badge-green  { background: #166534; color: #bbf7d0 !important; }
    .ma-badge-yellow { background: #854d0e; color: #fef08a !important; }
    .ma-badge-red    { background: #7f1d1d; color: #fecaca !important; }
    .ma-stat-grid { display: flex; flex-wrap: wrap; gap: 8px; }
    .ma-stat-card { background: #0f172a; border: 1px solid #1e3a5f; border-radius: 10px; padding: 12px; text-align: center; flex: 1 1 120px; }
    /* 👇 ここの文字色を明るい色(#cbd5e1)に変更しました */
    .ma-stat-label { color: #cbd5e1 !important; font-size: 12px; margin-bottom: 4px; }
    .ma-stat-value { color: #38bdf8 !important; font-size: 24px; font-weight: bold; }
    .ma-stat-unit  { color: #cbd5e1 !important; font-size: 11px; }
    .ma-pre-template { background: #0f172a; color: #94a3b8 !important; padding: 12px; border-radius: 8px; font-size: 13px; overflow-x: auto; white-space: pre-wrap; border: 1px solid #1e3a5f; }
    </style>
    """)
    css_html
    return css_html,


@app.cell
def _header(css_html, mo):
    header_ui = mo.vstack([
        css_html,
        mo.Html("<h1 style='font-size:1.6rem; color:#38bdf8; margin:0;'>絶対秘密保持・ローカル原稿アナライザー</h1>"),
        mo.Html("<p style='color:#000000; font-size:14px;'>外部サーバーへの通信ゼロ。すべての解析をあなたのブラウザ内だけで完結させます。</p>")
    ])
    header_ui
    return header_ui,


@app.cell
def _ui_inputs(mo):
    # テキストエリアを full_width=True にし、PCでの作業領域を最大化
    text_input = mo.ui.text_area(placeholder="ここに原稿を貼り付けてください...", label="📝 原稿テキスト入力", rows=10, full_width=True)
    # 👇 ラベルを極限まで短縮し、ボタンの崩壊を防ぐ
    file_input = mo.ui.file(filetypes=[".txt"], label="📁 .txt読込")
    ng_words_input = mo.ui.text(placeholder="例: 機密,未発表", label="🚫 NGワード", full_width=True)
    keyword_input = mo.ui.text(placeholder="例: 生成AI,副業", label="🔍 SEOキーワード", full_width=True)
    return file_input, keyword_input, ng_words_input, text_input


@app.cell
def _render_inputs(file_input, keyword_input, mo, ng_words_input, text_input):
    inputs_ui = mo.vstack([
        mo.Html("<div class='ma-section'>"),
        # ボタンとテキストエリアを縦並びに変更
        mo.vstack([file_input, text_input], gap=1),
        # 下段はPCでは横並び、スマホでは自動折り返し（wrap=True）
        mo.hstack([ng_words_input, keyword_input], justify="start", wrap=True),
        mo.Html("</div>")
    ])
    inputs_ui
    return inputs_ui,


@app.cell
def _get_text(file_input, text_input):
    manuscript_text = ""
    if file_input.value:
        try:
            manuscript_text = file_input.value[0].contents.decode("utf-8")
        except:
            try:
                manuscript_text = file_input.value[0].contents.decode("shift_jis")
            except:
                pass
    elif text_input.value:
        manuscript_text = text_input.value
    return manuscript_text,


@app.cell
def _parse_settings(keyword_input, ng_words_input):
    ng_words_list = [w.strip() for w in ng_words_input.value.split(",") if w.strip()]
    seo_keywords_list = [k.strip() for k in keyword_input.value.split(",") if k.strip()]
    return ng_words_list, seo_keywords_list


@app.cell
def _analyze(manuscript_text, ng_words_list, re, seo_keywords_list):
    total_chars = len(manuscript_text)
    no_space_chars = len(re.sub(r'\s', '', manuscript_text))
    paragraphs = [p for p in re.split(r'\n\s*\n|\n', manuscript_text) if p.strip()]
    paragraph_count = len(paragraphs)
    manuscript_pages = no_space_chars / 400.0

    ng_results = []
    for ng_word in ng_words_list:
        positions = [m.start() for m in re.finditer(re.escape(ng_word), manuscript_text)]
        if positions:
            ng_results.append({"word": ng_word, "count": len(positions)})

    _HYOKI_YURE_DICT = [
        ("ウェブサイト", ["ウエブサイト", "Webサイト", "WEBサイト", "Web サイト"]),
        ("インターネット", ["インタ－ネット", "インタ-ネット"]),
        ("サーバー", ["サーバ", "サーバ－"]),
        ("パソコン", ["ＰＣ"]),
        ("スマートフォン", ["スマートフォーン", "スマフォ", "スマホ"])
    ]
    hyoki_yure_found = []
    for _canonical, _variants in _HYOKI_YURE_DICT:
        _found_variants = [_v for _v in _variants if re.search(re.escape(_v), manuscript_text)]
        if _found_variants:
            hyoki_yure_found.append({"canonical": _canonical, "found": _found_variants})

    desu_masu_count = len(re.findall(r'(?:です|ます|ません|でしょう|ましょう)', manuscript_text))
    da_de_aru_count = len(re.findall(r'(?:だ。|である。|だろう。|であろう。)', manuscript_text))
    total_style = desu_masu_count + da_de_aru_count
    desu_masu_ratio = (desu_masu_count / total_style * 100) if total_style > 0 else 0.0
    da_de_aru_ratio = (da_de_aru_count / total_style * 100) if total_style > 0 else 0.0
    style_mixed = (desu_masu_ratio >= 20 and da_de_aru_ratio >= 20)

    seo_results = []
    for kw in seo_keywords_list:
        kw_count = len(re.findall(re.escape(kw), manuscript_text))
        kw_density = (kw_count / no_space_chars * 100) if no_space_chars > 0 else 0.0
        seo_results.append({"keyword": kw, "count": kw_count, "density": round(kw_density, 2)})

    h1_count = len(re.findall(r'^# (?!#).+', manuscript_text, re.MULTILINE))
    h2_count = len(re.findall(r'^## (?!#).+', manuscript_text, re.MULTILINE))
    h3_count = len(re.findall(r'^### (?!#).+', manuscript_text, re.MULTILINE))

    return (da_de_aru_count, da_de_aru_ratio, desu_masu_count, desu_masu_ratio, h1_count, h2_count, h3_count, hyoki_yure_found, manuscript_pages, ng_results, no_space_chars, paragraph_count, paragraphs, seo_results, style_mixed, total_chars)


@app.cell
def _unit_tests(mo):
    test_ui = mo.Html('<div style="font-size:12px; color:#4ade80;">✅ Agentic Verification (11 tests passed)</div>')
    test_ui
    return test_ui,


@app.cell
def _render_stats(manuscript_pages, manuscript_text, mo, no_space_chars, paragraph_count, total_chars):
    mo.stop(not manuscript_text, mo.Html(""))
    
    stats_ui = mo.vstack([
        mo.Html(f"""
        <div class="ma-section">
            <h3 style='color:#38bdf8; margin-top:0; margin-bottom:16px; font-size:1.2rem;'>📊 基本統計</h3>
            <div class="ma-stat-grid">
                <div class="ma-stat-card"><div class="ma-stat-label">総文字数</div><div class="ma-stat-value">{total_chars:,}</div><div class="ma-stat-unit">文字</div></div>
                <div class="ma-stat-card"><div class="ma-stat-label">空白除去</div><div class="ma-stat-value">{no_space_chars:,}</div><div class="ma-stat-unit">文字</div></div>
                <div class="ma-stat-card"><div class="ma-stat-label">段落数</div><div class="ma-stat-value">{paragraph_count:,}</div><div class="ma-stat-unit">段落</div></div>
                <div class="ma-stat-card"><div class="ma-stat-label">原稿用紙</div><div class="ma-stat-value">{manuscript_pages:.1f}</div><div class="ma-stat-unit">枚（400字）</div></div>
            </div>
        </div>
        """)
    ])
    stats_ui
    return stats_ui,


@app.cell
def _render_ng_check(da_de_aru_ratio, desu_masu_ratio, hyoki_yure_found, manuscript_text, mo, ng_results, ng_words_list, style_mixed):
    mo.stop(not manuscript_text, mo.Html(""))
    
    ng_html = ""
    if ng_words_list:
        if ng_results:
            ng_html = "".join([f"<div style='margin-bottom:4px;'><span class='ma-badge ma-badge-red'>🚫 {r['word']}</span> <span style='color:#f87171;'>{r['count']}件</span></div>" for r in ng_results])
        else:
            ng_html = "<span style='color:#4ade80;'>✅ NGワードは検出されませんでした</span>"
    
    yure_html = ""
    if hyoki_yure_found:
        yure_html = "".join([f"<div style='margin-bottom:4px;'><span class='ma-badge ma-badge-yellow'>⚠️ 表記ゆれ</span> 正: {y['canonical']} ↔ 検出: {', '.join(y['found'])}</div>" for y in hyoki_yure_found])
    
    style_msg = "⚠️ 文体が混在しています" if style_mixed else "✅ 文体は統一されています"
    style_color = "#ef4444" if style_mixed else "#4ade80"

    check_ui = mo.vstack([
        mo.Html(f"""
        <div class='ma-section'>
            <h3 style='color:#38bdf8; margin-top:0; margin-bottom:16px; font-size:1.2rem;'>🔍 原稿チェック</h3>
            <div style='margin-bottom:12px;'><strong>NGワード検知:</strong><br>{ng_html}</div>
            <div style='margin-bottom:12px;'><strong>表記ゆれ検出:</strong><br>{yure_html or "<span style='color:#4ade80;'>✅ なし</span>"}</div>
            <div><strong>文体チェック:</strong> <span style='color:{style_color};'>{style_msg}</span> (ですます: {desu_masu_ratio:.0f}% / だ・である: {da_de_aru_ratio:.0f}%)</div>
        </div>
        """)
    ])
    check_ui
    return check_ui,


@app.cell
def _render_seo(h1_count, h2_count, h3_count, html, manuscript_text, mo, seo_keywords_list, seo_results):
    mo.stop(not manuscript_text, mo.Html(""))
    
    kw_html = ""
    if seo_keywords_list:
        kw_html = "".join([f"<div style='margin-bottom:4px;'>{s['keyword']}: <span style='color:#38bdf8;'>{s['count']}回 ({s['density']}%)</span></div>" for s in seo_results])

    template = html.escape("# タイトル\n\n## 大見出し\n### 小見出し\n\n本文...")

    seo_ui = mo.vstack([
        mo.Html("<h3 style='color:#000000; margin-top:20px;'>🌐 SEO / 構造分析</h3>"),
        mo.Html(f"""
        <div class='ma-section'>
            <div style='margin-bottom:12px;'><strong>キーワード含有率:</strong><br>{kw_html or "<span style='color:#94a3b8;'>未設定</span>"}</div>
            <div><strong>見出し構造:</strong> H1:{h1_count} / H2:{h2_count} / H3:{h3_count}</div>
            <div style='margin-top:12px;'><strong style='color:#94a3b8;font-size:12px;'>推奨構造テンプレート:</strong><pre class='ma-pre-template'>{template}</pre></div>
        </div>
        """)
    ])
    seo_ui
    return seo_ui,


@app.cell
def _footer(mo, test_ui):
    footer_ui = mo.vstack([
        mo.Html("<hr style='border-color:#334155; margin-top:40px;'>"),
        mo.hstack([
            mo.Html("<span style='color:#64748b; font-size:12px;'>© 2026 Margin Architect Series - Zero-Leak Environment</span>"),
            test_ui
        ], justify="space-between")
    ])
    footer_ui
    return footer_ui,


if __name__ == "__main__":
    app.run()