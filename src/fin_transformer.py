import marimo

__generated_with = "0.19.0"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import io
    # 外部通信(requests等)はSOPにより絶対禁止。標準ライブラリとpandasのみを使用。
    return io, mo, pd


@app.cell
def _(mo):
    # 【SOP v3.3】Mobile UX Composition Hack & CSS Injection
    css_injection = mo.Html("""
    <style>
    /* 1. 画面全体の横スクロールを物理的に封印 */
    body, html, marimo-app, .marimo {
        max-width: 100vw !important;
        overflow-x: hidden !important;
        box-sizing: border-box !important;
    }
    .marimo { width: 100% !important; padding: 1rem; }

    /* 2. UI要素がコンテナを突き破るのを防ぐ防波堤 */
    marimo-ui-element, select, input, marimo-multiselect {
        max-width: 100% !important;
    }
    select {
        text-overflow: ellipsis !important;
        white-space: nowrap !important;
    }

    /* 3. スマホ時の強制折り返し用マーカー */
    .res-layout-marker + marimo-hstack {
        flex-wrap: wrap; 
        justify-content: center;
        gap: 15px;
    }
    
    /* 4. 長いテキストの強制折り返し */
    .force-wrap {
        word-break: break-all !important;
        overflow-wrap: break-word !important;
    }
    
    /* 5. テーブルの横スクロール保護 */
    marimo-table {
        display: block !important;
        max-width: 100% !important;
        overflow-x: auto !important;
    }
    </style>
    """)
    return css_injection,


@app.cell
def _(mo):
    # 【SOP v3.3】State Hook Architecture (WASMイベント消失対策)
    get_load_clicks, set_load_clicks = mo.state(0)
    return get_load_clicks, set_load_clicks


@app.cell
def _(mo, set_load_clicks):
    # Task 1: 基礎UIレイアウトの構築
    uploader_label = mo.Html("<label><b>📁 1. 銀行CSVを選択 (Shift-JIS/UTF-8対応)</b></label>")
    
    csv_uploader = mo.ui.file(
        kind="button", 
        filetypes=[".csv"], 
        multiple=False
    )

    load_btn = mo.ui.button(
        label="🚀 データを読み込む",
        kind="success",
        on_click=lambda _: set_load_clicks(lambda v: v + 1)
    )

    ui_input_section = mo.vstack([
        uploader_label,
        csv_uploader,
        load_btn
    ], gap=1.0)
    
    return csv_uploader, load_btn, ui_input_section, uploader_label


@app.cell
def _(csv_uploader, get_load_clicks, io, mo, pd):
    # Task 2: ファイルアップロードとエンコーディングの堅牢な処理
    df_loaded = None
    error_msg = ""
    columns_dict = {}

    if get_load_clicks() > 0 and csv_uploader.value:
        with mo.status.spinner("🛡️ CSVデータをオフライン解析中..."):
            _file_info = csv_uploader.value[0]
            _file_bytes = _file_info.contents

            if len(_file_bytes) > 5 * 1024 * 1024:
                error_msg = "⚠️ ファイルサイズ制限（5MB）を超えています。"
            else:
                try:
                    df_loaded = pd.read_csv(io.BytesIO(_file_bytes), encoding="utf-8")
                except UnicodeDecodeError:
                    try:
                        df_loaded = pd.read_csv(io.BytesIO(_file_bytes), encoding="shift_jis")
                    except Exception as _e:
                        error_msg = f"読み込み失敗: {str(_e)}"
                except Exception as _e:
                    error_msg = f"予期せぬエラー: {str(_e)}"

                if df_loaded is not None:
                    df_loaded.columns = [str(_c).strip() for _c in df_loaded.columns]
                    columns_dict = {str(_c): str(_c) for _c in df_loaded.columns}

    return columns_dict, df_loaded, error_msg


@app.cell
def _(columns_dict, df_loaded, error_msg, mo):
    # CSV読み込み結果のビュー構築
    result_view = mo.md("")

    if error_msg:
        result_view = mo.callout(error_msg, kind="danger")
    elif df_loaded is not None:
        result_view = mo.vstack([
            mo.callout("✅ 読み込み成功", kind="success"),
            mo.Html(f"<div class='force-wrap' style='font-size: 0.85rem; color: #666;'><b>総行数:</b> {len(df_loaded)}行<br><b>検出カラム:</b> {', '.join(columns_dict.keys())}</div>"),
            mo.ui.table(df_loaded.head(5), selection=None, pagination=False)
        ], gap=1.0)
        
    return result_view,


@app.cell
def _(mo):
    # 【SOP v3.3】Task 3 State Hook 
    get_transform_clicks, set_transform_clicks = mo.state(0)
    return get_transform_clicks, set_transform_clicks


@app.cell
def _(columns_dict, df_loaded, mo, set_transform_clicks):
    # Task 3 & 4: マッピング UI ＆ マスキング UI の構築
    mapping_ui_array = None
    std_columns = ["日付", "摘要", "入金額", "出金額", "残高"]
    mask_label = None
    masking_selector = None
    transform_btn = None
    task3_ui = mo.md("")

    def _truncate(col_name: str, max_len: int = 15) -> str:
        return col_name if len(col_name) <= max_len else col_name[:max_len] + "…"

    if df_loaded is not None and columns_dict:
        mapping_label = mo.Html("<label><b>🔄 2. 列マッピング (必須項目)</b></label>")
        
        _dropdown_opts = {"(未選択)": "(未選択)"}
        _dropdown_opts.update({_truncate(_col): _col for _col in columns_dict.keys()})
        
        _multiselect_opts = {_truncate(_col): _col for _col in columns_dict.keys()}
        
        mapping_ui_array = mo.ui.array([
            mo.ui.dropdown(options=_dropdown_opts, value="(未選択)")
            for _ in std_columns
        ])

        _mapping_view_items = []
        for _i, _std_col in enumerate(std_columns):
            _mapping_view_items.append(
                mo.vstack([
                    mo.Html(f"<div style='font-size: 0.9rem; font-weight: bold; color: #444; margin-bottom: 2px;'>📌 {_std_col}</div>"),
                    mapping_ui_array[_i]
                ], gap=0)
            )
        _mapping_ui_view = mo.vstack(_mapping_view_items, gap=0.8)

        mask_label = mo.Html("<label><b>🛡️ 3. マスキング対象を選択</b></label>")
        
        masking_selector = mo.ui.multiselect(
            options=_multiselect_opts,
        )
        
        transform_btn = mo.ui.button(
            label="⚙️ 変換を実行する",
            kind="warn",
            on_click=lambda _: set_transform_clicks(lambda v: v + 1)
        )
        
        task3_ui = mo.vstack([
            mapping_label,
            _mapping_ui_view,
            mo.Html("<hr style='border: 1px solid #ddd; margin: 15px 0;'>"),
            mask_label, 
            masking_selector, 
            transform_btn
        ], gap=1.0)

    return mapping_label, mapping_ui_array, mask_label, masking_selector, std_columns, task3_ui, transform_btn


@app.cell
def _(
    df_loaded,
    get_transform_clicks,
    mapping_ui_array,
    masking_selector,
    mo,
    std_columns,
):
    # Task 3, 4 & 5: データ変換・カスタムマッピング・マスキング実行ロジック
    df_transformed = None
    download_btn = None
    transform_msg = ""
    csv_bytes = None
    stat_board = mo.md("")

    if get_transform_clicks() > 0 and df_loaded is not None and mapping_ui_array is not None and masking_selector is not None:
        with mo.status.spinner("🔄 実行中..."):
            _selected_mapping_list = mapping_ui_array.value
            _selected_mask_cols = masking_selector.value

            _valid_mapping = {}
            for _i, _orig_col in enumerate(_selected_mapping_list):
                if _orig_col != "(未選択)":
                    _valid_mapping[std_columns[_i]] = _orig_col
            
            if not _valid_mapping:
                transform_msg = "⚠️ 少なくとも1つの列を紐付けてください。"
            else:
                _cols_to_extract = list(_valid_mapping.values())
                for _m_col in _selected_mask_cols:
                    if _m_col not in _cols_to_extract and _m_col in df_loaded.columns:
                        _cols_to_extract.append(_m_col)

                df_transformed = df_loaded[_cols_to_extract].copy()

                _mask_count = 0
                for _m_col in _selected_mask_cols:
                    if _m_col in df_transformed.columns:
                        df_transformed[_m_col] = "***"
                        _mask_count += 1

                _rename_map = {_orig_col: _new_col for _new_col, _orig_col in _valid_mapping.items()}
                df_transformed = df_transformed.rename(columns=_rename_map)

                _new_cols_order = list(_valid_mapping.keys())
                _extra_mask_cols = [_c for _c in _selected_mask_cols if _c not in _valid_mapping.values()]
                df_transformed = df_transformed[_new_cols_order + _extra_mask_cols]

                csv_bytes = df_transformed.to_csv(index=False).encode("utf-8-sig")
                
                download_btn = mo.download(
                    data=csv_bytes,
                    filename="transformed_fin_data.csv",
                    label="📥 CSVを保存する"
                )
                transform_msg = "✅ 完了しました。"

                stat_board = mo.hstack([
                    mo.stat(label="処理済", value=f"{len(df_transformed)}件"),
                    mo.stat(label="変換列", value=f"{len(df_transformed.columns)}列"),
                    mo.stat(label="匿名化", value=f"{_mask_count}列")
                ], justify="start", gap=2.0, wrap=True)

    return csv_bytes, df_transformed, download_btn, stat_board, transform_msg


@app.cell
def _(
    css_injection,
    df_loaded,
    df_transformed,
    download_btn,
    mo,
    result_view,
    stat_board,
    task3_ui,
    transform_msg,
    ui_input_section,
):
    # 【統合アセンブリ】
    transform_view = mo.md("")

    if df_transformed is not None and download_btn is not None:
        transform_view = mo.vstack([
            mo.Html("<hr style='border: 2px dashed #4caf50; margin: 25px 0;'>"),
            mo.callout(transform_msg, kind="success" if "✅" in transform_msg else "danger"),
            mo.md("### 📊 結果サマリー"),
            stat_board,
            
            # 【修正】ボタンと注釈テキストを「縦（vstack）」に配置して溢れを完全に防止
            mo.vstack([
                download_btn,
                mo.Html("<div style='font-size: 0.8rem; color: #666; margin-top: 4px;'>※Excel対応形式 (BOM付UTF-8) で出力されます</div>")
            ], gap=0.0),
            
            mo.md("**【データプレビュー】**"),
            mo.ui.table(df_transformed.head(10), selection=None, pagination=False)
        ], gap=1.0)

    main_view = mo.vstack([
        css_injection,
        mo.md("# 🏦 WASM-FinCSV Transformer"),
        mo.md("> 維持費0円・情報漏洩ゼロ。ブラウザ完結型の金融データ変換・匿名化ツール"),
        mo.md("---"),
        ui_input_section,
        mo.md("---"),
        result_view,
        mo.md("---") if df_loaded is not None else mo.md(""),
        task3_ui,
        transform_view
    ], gap=1.5)
    
    return main_view, transform_view


@app.cell
def _(main_view):
    # 【SOP v3.3】The Invisible Render バグ対策
    main_view
    return


if __name__ == "__main__":
    app.run()