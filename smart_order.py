import marimo

__generated_with = "0.23.1"
app = marimo.App()

@app.cell
def __():
    # --- Cell 1: インポート & Scope Isolation 層 ---
    import marimo as mo
    import pandas as pd
    import numpy as np
    import altair as alt
    import io

    # The Scope Isolation Trap 防衛のため、必須モジュールを明示的にエクスポート
    return alt, io, mo, np, pd


@app.cell
def __(np, pd):
    # --- Cell 1.5: バックエンドロジック (The Core Logic) ---
    def cleanse_data(raw_df: pd.DataFrame) -> pd.DataFrame:
        df = raw_df.copy()
        
        col_map = {
            '日付': 'Date',
            '商品コード': 'ItemCode',
            '売上数': 'SalesQty'
        }
        df = df.rename(columns=col_map)
        
        df = df.replace(r'^\s*$', np.nan, regex=True)
        df = df.dropna(how='all')
        
        mask = df.isin(['小計']).any(axis=1)
        df = df[~mask]
        
        essential_cols = [c for c in ['ItemCode', 'Date', 'SalesQty'] if c in df.columns]
        if essential_cols:
            df = df.dropna(subset=essential_cols)
            
        if 'SalesQty' in df.columns:
            df['SalesQty'] = pd.to_numeric(df['SalesQty'], errors='coerce')
            df = df.dropna(subset=['SalesQty'])
            
        return df

    def calculate_rop(df: pd.DataFrame, lead_time: int, safety_stock: int) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame(columns=['ItemCode', 'ROP'])
            
        avg_sales = df.groupby('ItemCode')['SalesQty'].mean().reset_index()
        avg_sales = avg_sales.rename(columns={'SalesQty': 'AvgDailySales'})
        
        result_df = avg_sales.copy()
        result_df['ROP'] = (result_df['AvgDailySales'] * lead_time) + safety_stock
        
        # 端数処理の適用: np.ceil() で切り上げ、int 型にキャスト
        result_df['AvgDailySales'] = np.ceil(result_df['AvgDailySales']).astype(int)
        result_df['ROP'] = np.ceil(result_df['ROP']).astype(int)
        
        return result_df

    return calculate_rop, cleanse_data


@app.cell
def __(mo):
    # --- Cell 2: バックエンド状態管理層 (The Reactive Ghost Protocol) ---
    # ユーザーの入力値を一括で監視・カプセル化する「通信核」
    smart_order_inputs = mo.ui.dictionary({
        "file_upload": mo.ui.file(kind="button", filetypes=[".csv"]),
        "lead_time": mo.ui.number(start=1, stop=30, step=1, value=3),
        "safety_stock": mo.ui.number(start=0, stop=1000, step=1, value=10)
    })

    return smart_order_inputs,


@app.cell
def __(cleanse_data, io, mo, pd, smart_order_inputs):
    # --- Cell 3: ETL Phase (The Fail-Safe Protocol & Data Cleansing) ---
    _files = smart_order_inputs.value["file_upload"]
    
    cleaned_df = None
    etl_error_ui = None

    # ガード節 1: ファイル未アップロード時の防衛 (The Stealth Block Trap 回避)
    if not _files:
        etl_error_ui = mo.md("⚠️ 過去の販売データ（CSV）をアップロードしてください。").callout(kind="warn")
    else:
        try:
            # WASM環境でのバイトストリーム読み込みと初期パース
            _raw_bytes = _files[0].contents
            _raw_df = pd.read_csv(io.BytesIO(_raw_bytes), dtype=str).fillna("")
            
            # バックエンド関数へ委譲（ベクトル演算によるETL）
            cleaned_df = cleanse_data(_raw_df)
            
            # ガード節 3: クレンジング後データが0件の場合の防衛
            if cleaned_df.empty:
                etl_error_ui = mo.md("⚠️ データクレンジングの結果、有効なデータが0件になりました。フォーマットを確認してください。").callout(kind="warn")
                cleaned_df = None
                
        except Exception as _e:
            # ガード節 2: パース・クレンジング失敗時の防衛
            etl_error_ui = mo.md(f"🚨 データのパースまたはクレンジングに失敗しました。\nエラー詳細: {_e}").callout(kind="danger")
            cleaned_df = None

    return cleaned_df, etl_error_ui


@app.cell
def __(calculate_rop, cleaned_df, mo, smart_order_inputs):
    # --- Cell 4: Simulation & Alert Phase ---
    result_df = None
    alert_ui = None

    if cleaned_df is not None:
        _lead_time = smart_order_inputs.value["lead_time"]
        _safety_stock = smart_order_inputs.value["safety_stock"]
    
        # バックエンドの ROP (発注点) 計算エンジンを実行
        result_df = calculate_rop(cleaned_df, _lead_time, _safety_stock)
    
        # ROP割れ（欠品リスク）をシミュレートするための現行在庫モックアップ適用
        if 'CurrentStock' not in result_df.columns:
            result_df['CurrentStock'] = 20  
    
        # 欠品リスク（現行在庫 <= ROP）のベクトル判定
        _stockout_items = result_df[result_df['CurrentStock'] <= result_df['ROP']]
    
        # 動的アラートUIバインディング
        if not _stockout_items.empty:
            _alert_msg = f"🚨 警告: 発注点（ROP）を下回っている商品が **{len(_stockout_items)}件** 存在します！至急発注を確認してください。"
            alert_ui = mo.md(_alert_msg).callout(kind="danger")
        else:
            alert_ui = mo.md("✅ 全商品の在庫は発注点（ROP）以上の安全水準を保っています。").callout(kind="success")

    return alert_ui, result_df


@app.cell
def __(alt, mo, result_df):
    # --- Cell 5: Visualization & Data Assembly Phase ---
    chart_ui = None
    order_editor = None

    if result_df is not None:
        # Altair Width Fix 適用済みの推移可視化チャート
        chart_ui = alt.Chart(result_df).mark_bar().encode(
            x=alt.X("ItemCode:N", title="商品コード"),
            y=alt.Y("ROP:Q", title="推奨発注点 (ROP)"),
            color=alt.condition(
                alt.datum.CurrentStock <= alt.datum.ROP,
                alt.value("#d62728"),  # ROP割れ時は警告の赤
                alt.value("#1f77b4")   # 正常時は安全の青
            ),
            tooltip="ItemCode:N"
        ).properties(
            width="container", # 【厳命】レスポンシブ対応
            height=300,
            title="アイテム別 発注点 (ROP) & 在庫ステータス"
        )
    
        # mo.ui.data_editor への置換
        order_editor = mo.ui.data_editor(result_df)

    return chart_ui, order_editor


@app.cell
def __(alert_ui, chart_ui, etl_error_ui, mo, order_editor, smart_order_inputs):
    # --- Cell 6: Final Layout Assembly (The Pure Vertical Stream) ---
    _header = mo.md(
        """
        # 📦 SmartOrder (The ETL & Decumulation Pipeline)
        維持費0円・情報漏洩ゼロ。WASM環境下での高速なデータクレンジングと発注点（ROP）シミュレーション。
        """
    )

    _input_panel = mo.vstack([
        mo.md("### 📥 1. 実績データアップロード (CSV)"),
        smart_order_inputs["file_upload"],
        mo.md("### ⚙️ 2. 発注シミュレーション・パラメータ"),
        mo.md("**リードタイム (日)**: 発注から納品までの所要日数"),
        smart_order_inputs["lead_time"],
        mo.md("**安全在庫 (個)**: 需要ブレを吸収するためのバッファ"),
        smart_order_inputs["safety_stock"]
    ])

    if etl_error_ui is not None:
        _results_panel = mo.vstack([
            mo.md("### 📊 3. 解析結果 & アラートステータス"),
            etl_error_ui
        ])
    else:
        # エディタの変更内容をCSVとしてダウンロードできるボタンを追加
        _download_btn = mo.download(
            order_editor.value.to_csv(index=False).encode('utf-8'),
            filename="order_plan.csv",
            label="📥 発注リストをダウンロード"
        )
        
        _results_panel = mo.vstack([
            mo.md("### 📊 3. 解析結果 & アラートステータス"),
            alert_ui,
            chart_ui,
            mo.md("### 📋 4. 発注推奨サマリー (Data Editor 適用)"),
            order_editor,
            _download_btn
        ])

    final_assembly_ui = mo.vstack([
        _header,
        mo.md("---"),
        _input_panel,
        mo.md("---"),
        _results_panel
    ])

    final_assembly_ui
    return final_assembly_ui,


if __name__ == "__main__":
    app.run()