import marimo

__generated_with = "0.19.0"
app = marimo.App(width="full")


@app.cell
def __():
    import marimo as mo
    import pandas as pd
    import io
    import re
    import unicodedata
    import altair as alt
    return alt, io, mo, pd, re, unicodedata


@app.cell
def __(mo):
    # ==========================================
    # 1. State Management (状態管理の導入)
    # ==========================================
    # DOMのvalue同期不良を防ぐため、Python側でクリック回数を直接管理する
    get_clean_clicks, set_clean_clicks = mo.state(0)
    get_dedup_clicks, set_dedup_clicks = mo.state(0)
    return get_clean_clicks, get_dedup_clicks, set_clean_clicks, set_dedup_clicks


@app.cell
def __(mo, set_clean_clicks, set_dedup_clicks):
    # ==========================================
    # 2. Static UI Definitions (UX正常化・ラベル適正化)
    # ==========================================
    # Input要素(file)はラベル分離、Button要素はテキストとしてlabelを復活
    file_upload = mo.ui.file(
        kind="area", 
        filetypes=[".csv", ".xlsx", ".xls"], 
        multiple=False
    )
    
    clean_btn = mo.ui.button(
        label="🧹 クレンジングを実行", 
        kind="success",
        on_click=lambda _: set_clean_clicks(lambda v: v + 1)
    )
    
    dedup_btn = mo.ui.button(
        label="🔄 名寄せを実行", 
        kind="warn",
        on_click=lambda _: set_dedup_clicks(lambda v: v + 1)
    )
    return clean_btn, dedup_btn, file_upload


@app.cell
def __(file_upload, io, pd):
    # ==========================================
    # 3. Data Ingestion
    # ==========================================
    df_raw = None
    if file_upload.value:
        file = file_upload.value[0]
        fname = file.name
        fcontent = file.contents
        if fname.lower().endswith('.csv'):
            try:
                decoded_text = fcontent.decode('utf-8')
            except UnicodeDecodeError:
                decoded_text = fcontent.decode('cp932')
            df_raw = pd.read_csv(io.StringIO(decoded_text))
        elif fname.lower().endswith(('.xlsx', '.xls')):
            df_raw = pd.read_excel(io.BytesIO(fcontent))
    return df_raw,


@app.cell
def __(df_raw, mo):
    # ==========================================
    # 4. Mappers Definition (スコープ保護済み・ラベル分離)
    # ==========================================
    mappers = None
    if df_raw is not None:
        opts = {"-- 対象なし --": ""}
        opts.update({str(c): str(c) for c in df_raw.columns})
        # Dropdownは入力要素なのでShadow DOM対策のためlabel引数を削除
        mappers = {
            "name": mo.ui.dropdown(options=opts),
            "phone": mo.ui.dropdown(options=opts),
            "email": mo.ui.dropdown(options=opts),
            "company": mo.ui.dropdown(options=opts)
        }
    return mappers,


@app.cell
def __(df_raw, get_clean_clicks, mappers, mo, pd, re, unicodedata):
    # ==========================================
    # 5. Cleansing Logic (状態トリガー駆動)
    # ==========================================
    df_cleaned = None
    clean_error = None
    
    if df_raw is not None and get_clean_clicks() > 0 and mappers is not None:
        with mo.status.spinner("データをクレンジング中..."):
            try:
                df_cleaned = df_raw.copy()
                c_name = str(mappers["name"].value)
                c_phone = str(mappers["phone"].value)
                c_email = str(mappers["email"].value)
                c_comp = str(mappers["company"].value)
                
                def clean_str(x):
                    if pd.isna(x): return x
                    return unicodedata.normalize('NFKC', str(x)).strip()
                    
                def clean_ph(x):
                    if pd.isna(x): return x
                    return re.sub(r'\D', '', unicodedata.normalize('NFKC', str(x)))
                    
                def clean_em(x):
                    if pd.isna(x): return x
                    return unicodedata.normalize('NFKC', str(x)).strip().lower()
                    
                if c_name and c_name != "-- 対象なし --" and c_name in df_cleaned.columns:
                    df_cleaned[c_name] = df_cleaned[c_name].apply(clean_str)
                if c_comp and c_comp != "-- 対象なし --" and c_comp in df_cleaned.columns:
                    df_cleaned[c_comp] = df_cleaned[c_comp].apply(clean_str)
                if c_phone and c_phone != "-- 対象なし --" and c_phone in df_cleaned.columns:
                    df_cleaned[c_phone] = df_cleaned[c_phone].apply(clean_ph)
                if c_email and c_email != "-- 対象なし --" and c_email in df_cleaned.columns:
                    df_cleaned[c_email] = df_cleaned[c_email].apply(clean_em)
                    
            except Exception as e:
                clean_error = str(e)
                df_cleaned = None
                
    return clean_error, df_cleaned


@app.cell
def __(df_cleaned, mo):
    # ==========================================
    # 6. Dedup Definition (スコープ保護済み・ラベル分離)
    # ==========================================
    dedup_key_dropdown = None
    if df_cleaned is not None:
        opts_dedup = {"-- 選択なし --": ""}
        opts_dedup.update({str(c): str(c) for c in df_cleaned.columns})
        dedup_key_dropdown = mo.ui.dropdown(options=opts_dedup)
    return dedup_key_dropdown,


@app.cell
def __(dedup_key_dropdown, df_cleaned, get_dedup_clicks, mo):
    # ==========================================
    # 7. Dedup Logic (状態トリガー駆動)
    # ==========================================
    df_final = None
    dedup_error = None
    
    if df_cleaned is not None and dedup_key_dropdown is not None:
        try:
            if get_dedup_clicks() > 0 and dedup_key_dropdown.value and dedup_key_dropdown.value != "-- 選択なし --":
                key_col = str(dedup_key_dropdown.value)
                with mo.status.spinner(f"「{key_col}」で重複を排除中..."):
                    df_final = df_cleaned.drop_duplicates(subset=[key_col], keep='first')
            else:
                df_final = df_cleaned.copy()
        except Exception as e:
            dedup_error = str(e)
            df_final = None
            
    return dedup_error, df_final


@app.cell
def __(
    alt,
    clean_btn,
    clean_error,
    dedup_btn,
    dedup_error,
    dedup_key_dropdown,
    df_cleaned,
    df_final,
    df_raw,
    file_upload,
    io,
    mappers,
    mo,
    pd,
):
    # ==========================================
    # 8. Unified Master Layout (レイアウト構築)
    # ==========================================
    sections = []
    sections.append(mo.md("# 🛡️ Zero-Leak Customer Data Cleanser").callout(kind="info"))
    sections.append(mo.md("### 1. データの読み込み"))
    
    # 💡 Light DOMへのラベル分離 (モバイル安全な vstack)
    sections.append(mo.vstack([
        mo.Html("<label style='font-weight: bold;'>📄 アップロードするファイルを選択（CSV / Excel）</label>"),
        file_upload
    ], gap=1))
    
    if df_raw is not None:
        sections.append(mo.md(f"✅ **読み込みデータ プレビュー (先頭10件) | 総データ件数: {len(df_raw)}件**").callout(kind="success"))
        sections.append(mo.ui.table(df_raw.head(10), selection=None))
        sections.append(mo.md("---"))
        
        if mappers is not None:
            sections.append(mo.md("### 2. クレンジング対象列のマッピング"))
            sections.append(mo.md("読み込んだデータのうち、どの列をクレンジングするか選択してください。"))
            
            # 💡 Dropdownのラベル分離
            name_ui = mo.vstack([mo.Html("<label style='font-weight: bold;'>氏名 (Name)</label>"), mappers["name"]], gap=1)
            phone_ui = mo.vstack([mo.Html("<label style='font-weight: bold;'>電話番号 (Phone)</label>"), mappers["phone"]], gap=1)
            email_ui = mo.vstack([mo.Html("<label style='font-weight: bold;'>メールアドレス (Email)</label>"), mappers["email"]], gap=1)
            company_ui = mo.vstack([mo.Html("<label style='font-weight: bold;'>会社名 (Company)</label>"), mappers["company"]], gap=1)
            
            sections.append(mo.hstack([name_ui, phone_ui], justify="start", gap=2))
            sections.append(mo.hstack([email_ui, company_ui], justify="start", gap=2))
            
            sections.append(mo.md("### 3. データクレンジングの実行"))
            # 💡 ボタンは説明ラベルと横並びにせず、そのまま配置 (モバイル崩れ防止)
            sections.append(clean_btn)
            
        if clean_error:
            sections.append(mo.md(f"❌ クレンジング中にエラーが発生しました: `{clean_error}`").callout(kind="danger"))
            
    if df_cleaned is not None:
        sections.append(mo.md("---"))
        sections.append(mo.md("### 4. 重複データの統合 (名寄せ)"))
        if dedup_key_dropdown is not None:
            dedup_dropdown_ui = mo.vstack([
                mo.Html("<label style='font-weight: bold;'>🔑 名寄せのキー列を選択</label>"),
                dedup_key_dropdown
            ], gap=1)
            
            # モバイル環境での安全性を考慮し、Dropdownとボタンをvstackで縦積み
            sections.append(mo.vstack([dedup_dropdown_ui, dedup_btn], justify="start", align="start", gap=2))
            
        if dedup_error:
            sections.append(mo.md(f"❌ 名寄せ中にエラーが発生しました: `{dedup_error}`").callout(kind="danger"))
            
    if df_final is not None:
        sections.append(mo.md("---"))
        sections.append(mo.md("### 5. 処理結果プレビュー & エクスポート"))
        
        orig_count = len(df_raw)
        fin_count = len(df_final)
        diff = orig_count - fin_count
        
        df_chart = pd.DataFrame({
            "ステータス": ["1_元データ", "2_処理後データ"],
            "件数": [orig_count, fin_count]
        })
        
        bar_chart = alt.Chart(df_chart).mark_bar(opacity=0.8, color="#4CAF50").encode(
            x=alt.X("ステータス:N", title="データ処理段階"),
            y=alt.Y("件数:Q", title="レコード数"),
            tooltip=["ステータス", "件数"]
        ).properties(width=300, height=250, title="データ削減件数の推移")
        
        csv_buf = io.StringIO()
        df_final.to_csv(csv_buf, index=False)
        csv_data = csv_buf.getvalue().encode('utf-8-sig')
        
        # 💡 ダウンロードボタンのlabel復活
        download_btn = mo.download(
            data=csv_data,
            filename="cleansed_data.csv",
            label="💾 クレンジング済みデータをダウンロード (CSV)",
            mimetype="text/csv"
        )
        
        # 💡 SSOT準拠: mo.stat の導入
        stat_orig = mo.stat(label="元レコード数", value=f"{orig_count}件")
        stat_fin = mo.stat(label="最終レコード数", value=f"{fin_count}件", caption=f"重複削除数: {diff}件")
        stats_ui = mo.hstack([stat_orig, stat_fin], justify="start", gap=4)
        
        sections.append(mo.hstack([
            mo.vstack([
                mo.md("**📉 サマリー**"),
                stats_ui,
                download_btn
            ], gap=2),
            mo.ui.altair_chart(bar_chart)
        ], justify="start", align="center", gap=4))
        
        sections.append(mo.md("**最終データプレビュー (先頭10件)**"))
        sections.append(mo.ui.table(df_final.head(10), selection=None))
        
    sections.append(mo.md("--- \n *Zero-Leak Customer Data Cleanser - Runs purely in your browser.*"))
    
    ui_layout = mo.vstack(sections, align="stretch")
    return ui_layout,


@app.cell
def __(ui_layout):
    # ==========================================
    # 9. Render (確実な描画)
    # ==========================================
    ui_layout
    return


if __name__ == "__main__":
    app.run()