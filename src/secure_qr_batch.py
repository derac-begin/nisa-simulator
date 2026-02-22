import marimo

__generated_with = "0.19.0"
app = marimo.App(width="medium")


@app.cell
async def _():
    try:
        import micropip
        await micropip.install("segno")
    except ImportError:
        # ローカル環境（PC）で実行した場合は、すでにインストールされているためスキップ
        pass
    return
# ============================================================
# セル 1: ライブラリのインポート
# 【Quality Gate チェック済み】
#   - requests は一切使用しない (WASM制約)
#   - io.BytesIO / zipfile でインメモリ処理 (ローカルFS禁止)
#   - segno は Pure Python QR ライブラリ (WASM安定)
# ============================================================
@app.cell
def _imports():
    import marimo as mo
    import csv
    import io
    import zipfile
    import base64
    import segno
    return base64, csv, io, mo, segno, zipfile


# ============================================================
# セル 2: モバイル対応 CSS の注入
#
# 【根本原因の解析と修正方針】
#
# ❌ 失敗したアプローチ: mo.md() で <style> タグを返す
#   → marimo v0.19.0 のセキュリティサニタイザーが <style> タグを
#     除去するため、CSSは一切注入されない。
#
# ❌ 失敗の第2の原因: Shadow DOM による encapsulation
#   → marimo のウィジェット層は Shadow DOM で実装されており、
#     外部ドキュメントに定義された CSS は Shadow Boundary を
#     越えてコンポーネント内部に届かない。
#     したがって、たとえ <style> を注入できても効果はない。
#
# ✅ 採用した3層防御戦略:
#   Layer 1: mo.Html() で生の <style> タグを注入
#            mo.md() と違い mo.Html() はサニタイズをスキップする。
#            Shadow DOM の外側（ホストドキュメント側）に効果あり。
#   Layer 2: 各コンポーネントに .style() メソッドで inline style を付与
#            Shadow DOM 内部のコンポーネントに直接スタイルを適用できる
#            唯一の確実な手段。
#   Layer 3: mo.Html() で生成する要素に style 属性を直接埋め込む
#            ダウンロードボタンなどの生 HTML 要素に完全に制御可能。
# ============================================================
@app.cell
def _mobile_css(mo):
    # Layer 1: mo.Html() 経由でホストドキュメント側にグローバルCSSを注入。
    # mo.md() と異なり mo.Html() はサニタイズされないため <style> タグが生き残る。
    # !important + 高詳細度セレクタで marimo 自身の Tailwind CSS を上書きする。
    # 【重要】marimo では _ プレフィックスの変数はセルプライベート扱いになり
    # 他のセルから参照できない。mobile_css（プレフィックスなし）で公開変数として返す。
    mobile_css = mo.Html("""
    <style>
    /* ===== モバイル折り返し修正 (Secure QR Batch Maker) ===== */
    /* overflow-wrap: anywhere は word-break の最上位互換 — 強制折り返し */
    html, body, #root, .marimo, [data-testid], article, section, div, p, span, li, td, th, label, button {
        overflow-wrap: anywhere !important;
        word-break: break-word !important;
        white-space: normal !important;
        max-width: 100% !important;
    }
    /* 横スクロール抑止 */
    html, body {
        overflow-x: hidden !important;
        box-sizing: border-box !important;
    }
    /* marimo callout / markdown 要素 */
    .marimo-callout, .marimo-md, .marimo-text {
        overflow-wrap: anywhere !important;
        word-break: break-word !important;
        white-space: normal !important;
    }
    /* ボタン要素 */
    button, [role="button"], .marimo-button {
        white-space: normal !important;
        word-break: break-word !important;
        overflow-wrap: anywhere !important;
        height: auto !important;
        min-height: 2.5rem;
    }
    </style>
    """)
    return (mobile_css,)


# ============================================================
# セル 3: ロジック関数の定義
# 【UIとロジックの完全分離 — Reactive Loop 防止】
# ============================================================
@app.cell
def _logic(base64, csv, io, segno, zipfile):

    def parse_csv(file_bytes: bytes) -> list[dict[str, str]]:
        """
        CSVバイト列を解析して、辞書のリストを返す。
        1列目をラベル（ファイル名用）、2列目をQRコード化するURLとして扱う。
        - 1列だけのCSVの場合は、その列をURLとして使用し、行番号をラベルとする。
        """
        text = file_bytes.decode("utf-8-sig")  # BOM付きUTF-8にも対応
        reader = csv.DictReader(io.StringIO(text))
        rows: list[dict[str, str]] = []
        headers = reader.fieldnames or []

        for i, row in enumerate(reader):
            if len(headers) >= 2:
                label = str(row[headers[0]]).strip()
                url   = str(row[headers[1]]).strip()
            elif len(headers) == 1:
                label = f"row_{i + 1:04d}"
                url   = str(row[headers[0]]).strip()
            else:
                continue

            if url:  # 空行はスキップ
                rows.append({"label": label, "url": url})

        return rows


    def generate_qr_png_bytes(url: str, scale: int = 5) -> bytes:
        """
        指定されたURLのQRコードをPNG形式のバイト列として返す。
        segno を使用し、インメモリ (io.BytesIO) に書き出す。
        外部通信は一切行わない。
        """
        buf = io.BytesIO()
        qr = segno.make_qr(url)
        qr.save(buf, kind="png", scale=scale, border=2)
        buf.seek(0)
        return buf.read()


    def build_zip(rows: list[dict[str, str]]) -> bytes:
        """
        QRコードPNGを一括生成し、インメモリZIPファイルとして返す。
        ローカルファイルシステムへの書き込みは行わない。
        重複ラベルは連番サフィックスで一意性を保証する。
        """
        zip_buf = io.BytesIO()
        used_names: dict[str, int] = {}

        with zipfile.ZipFile(zip_buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for row in rows:
                # ファイル名の重複を避けるため連番を付与
                base_name = row["label"].replace("/", "_").replace("\\", "_")
                if base_name in used_names:
                    used_names[base_name] += 1
                    file_name = f"{base_name}_{used_names[base_name]:03d}.png"
                else:
                    used_names[base_name] = 0
                    file_name = f"{base_name}.png"

                png_bytes = generate_qr_png_bytes(row["url"])
                zf.writestr(file_name, png_bytes)

        zip_buf.seek(0)
        return zip_buf.read()


    def zip_to_data_uri(zip_bytes: bytes) -> str:
        """ZIP バイト列をブラウザダウンロード用の data URI に変換する。"""
        b64 = base64.b64encode(zip_bytes).decode("ascii")
        return f"data:application/zip;base64,{b64}"

    return build_zip, generate_qr_png_bytes, parse_csv, zip_to_data_uri


# ============================================================
# セル 4: 単体テスト — parse_csv
# 【Quality Gate 要件: assert 文による動的検証】
# ============================================================
@app.cell
def _test_parse_csv(parse_csv):
    # テスト1: 2列 CSV（ラベル＋URL）
    _csv_2col = "name,url\n店舗A,https://example.com/a\n店舗B,https://example.com/b\n".encode("utf-8")
    _result_2col = parse_csv(_csv_2col)
    assert len(_result_2col) == 2, f"2列CSV: 行数が2であるべき。実際: {len(_result_2col)}"
    assert _result_2col[0]["label"] == "店舗A", "1行目のラベルが正しくない"
    assert _result_2col[0]["url"] == "https://example.com/a", "1行目のURLが正しくない"
    assert _result_2col[1]["label"] == "店舗B", "2行目のラベルが正しくない"

    # テスト2: 1列 CSV（URL のみ）
    _csv_1col = "url\nhttps://example.com/c\nhttps://example.com/d\n".encode("utf-8")
    _result_1col = parse_csv(_csv_1col)
    assert len(_result_1col) == 2, f"1列CSV: 行数が2であるべき。実際: {len(_result_1col)}"
    assert _result_1col[0]["label"] == "row_0001", "1列CSVのラベルが連番になっていない"

    # テスト3: 空行はスキップされる
    _csv_empty = "name,url\n有効行,https://example.com/valid\n,,\n".encode("utf-8")
    _result_empty = parse_csv(_csv_empty)
    assert len(_result_empty) == 1, f"空行スキップ: 有効行が1件のはず。実際: {len(_result_empty)}"

    # テスト4: BOM付き UTF-8 も正常に解析できる
    _bom_csv = "\ufeffname,url\nBOM店舗,https://bom.example.com/\n".encode("utf-8-sig")
    _result_bom = parse_csv(_bom_csv)
    assert len(_result_bom) == 1, "BOM付きCSVが正常に解析されていない"

    print("✅ parse_csv: 全テスト通過")
    return


# ============================================================
# セル 5: 単体テスト — generate_qr_png_bytes / build_zip
# 【Quality Gate 要件: assert 文による動的検証】
# ============================================================
@app.cell
def _test_generate_and_zip(build_zip, generate_qr_png_bytes, io, zipfile):
    # テスト5: QRコード PNG バイト列が PNG ヘッダーで始まる
    _png = generate_qr_png_bytes("https://example.com/test")
    _PNG_HEADER = b"\x89PNG\r\n\x1a\n"
    assert _png[:8] == _PNG_HEADER, "QRコードが有効なPNGではない"
    assert len(_png) > 100, "PNGバイト列が異常に短い"

    # テスト6: ZIPが正常に生成され、指定件数のエントリが含まれる
    _test_rows = [
        {"label": "店舗A", "url": "https://example.com/a"},
        {"label": "店舗B", "url": "https://example.com/b"},
        {"label": "店舗A", "url": "https://example.com/a_dup"},  # 重複ラベルのテスト
    ]
    _zip_bytes = build_zip(_test_rows)
    _zf = zipfile.ZipFile(io.BytesIO(_zip_bytes))
    _names = _zf.namelist()
    assert len(_names) == 3, f"ZIPエントリが3件であるべき。実際: {len(_names)}"
    assert "店舗A.png" in _names, "1件目のラベルファイルが存在しない"
    assert "店舗A_001.png" in _names, "重複ラベルに連番が付与されていない"
    assert "店舗B.png" in _names, "店舗Bのファイルが存在しない"

    print("✅ generate_qr_png_bytes / build_zip: 全テスト通過")
    return


# ============================================================
# セル 6: UIの定義 — ファイルアップロード & 実行ボタン
#
# 【モバイル対応: Layer 2 — .style() メソッドで inline style を付与】
# Shadow DOM のコンポーネントに直接スタイルを適用できる唯一の手段。
# ============================================================
@app.cell
def _ui(mobile_css, mo):
    # CSS 注入セルを依存関係に取り込み（セル2を先に評価させる）
    _ = mobile_css

    # ========================================================
    # 【根本修正】mo.md() → mo.Html() に完全置き換え
    #
    # 失敗の詳細:
    #   mo.md() はマークダウンを HTML に変換するが、
    #   <strong>, <blockquote> などのインライン・ブロック要素に
    #   overflow-wrap が CSS カスケードで届かない。
    #   .style() はラッパー div にしか適用されないため、
    #   内部の <strong> や <blockquote> の横幅制御ができない。
    #
    # 解決策:
    #   mo.Html() で全要素を直接記述し、各タグに style 属性を
    #   直接埋め込むことで Shadow DOM / CSS カスケードの影響を完全に回避。
    #   blockquote は mo.callout() で代替（これは .style() が内部まで届く）。
    # ========================================================

    # 共通インラインスタイル（全要素に適用する折り返しルール）
    _S = (
        "overflow-wrap:anywhere;"
        "word-break:break-word;"
        "white-space:normal;"
        "max-width:100%;"
        "box-sizing:border-box;"
    )

    # ヘッダーを mo.Html() で直接構築し、各タグに style を打ち込む
    _header = mo.Html(f"""
    <div style="width:100%;max-width:100%;overflow-x:hidden;box-sizing:border-box;">
      <h1 style="{_S}font-size:clamp(1.4rem,5vw,2rem);margin:0 0 8px;">
        🔒 Secure QR Batch Maker
      </h1>
      <p style="{_S}font-weight:bold;margin:0 0 12px;">
        完全ブラウザ処理 — あなたのデータはサーバーに一切送信されません
      </p>
      <hr style="margin:12px 0;"/>
      <h3 style="{_S}margin:8px 0;">📋 CSVフォーマット</h3>
      <table style="width:100%;border-collapse:collapse;table-layout:fixed;{_S}">
        <thead>
          <tr>
            <th style="text-align:left;padding:6px 8px;border:1px solid #ccc;{_S}">列1（ラベル）</th>
            <th style="text-align:left;padding:6px 8px;border:1px solid #ccc;{_S}">列2（QRコード化するURL）</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td style="padding:6px 8px;border:1px solid #ccc;{_S}">店舗A</td>
            <td style="padding:6px 8px;border:1px solid #ccc;{_S}">https://example.com/A</td>
          </tr>
          <tr>
            <td style="padding:6px 8px;border:1px solid #ccc;{_S}">店舗B</td>
            <td style="padding:6px 8px;border:1px solid #ccc;{_S}">https://example.com/B</td>
          </tr>
        </tbody>
      </table>
    </div>
    """)

    # ヒント: blockquote の代わりに mo.callout() を使用
    # mo.callout() は .style() が内部テキストまで正しく届く
    _hint = mo.callout(
        mo.md(
            "**ヒント:** ヘッダー行は自動的にスキップされます。"
            "列が1列だけの場合、その列をURLとして使用し、行番号をファイル名とします。"
        ),
        kind="info",
    ).style({
        "overflow-wrap": "anywhere",
        "word-break": "break-word",
        "white-space": "normal",
        "max-width": "100%",
        "box-sizing": "border-box",
    })

    # CSVアップロードウィジェット
    csv_uploader = mo.ui.file(
        filetypes=[".csv"],
        label="① CSVファイルを選択してください",
    )

    # QR生成実行ボタン
    run_button = mo.ui.run_button(
        label="② QRコードを一括生成して ZIP ダウンロード ▶",
        full_width=True,
    )

    mo.vstack(
        [_header, _hint, csv_uploader, run_button],
        gap=1,
    ).style({
        "max-width": "100%",
        "overflow-x": "hidden",
        "box-sizing": "border-box",
    })

    return csv_uploader, run_button


# ============================================================
# セル 7: 結果表示 — ボタン押下時のみ処理を実行
#
# 【モバイル対応: Layer 2 + Layer 3 の組み合わせ】
# mo.callout にも .style() を適用し、
# ダウンロードリンク（生 HTML）には style 属性を直接埋め込む。
# ============================================================
@app.cell
def _result(build_zip, csv_uploader, mo, parse_csv, run_button, zip_to_data_uri):
    # ボタンが押されていない場合は何も表示しない
    mo.stop(not run_button.value)

    # 共通 inline style 文字列（Layer 3: 生 HTML 要素への直接埋め込み用）
    _wrap_style = (
        "overflow-wrap:anywhere;"
        "word-break:break-word;"
        "white-space:normal;"
        "max-width:100%;"
        "box-sizing:border-box;"
    )

    # ファイルが未選択の場合はエラー表示
    if not csv_uploader.value or len(csv_uploader.value) == 0:
        result_area = mo.callout(
            mo.md("⚠️ **CSVファイルが選択されていません。**\nファイルをアップロードしてから実行してください。"),
            kind="warn",
        ).style({
            "overflow-wrap": "anywhere",
            "word-break": "break-word",
            "white-space": "normal",
            "max-width": "100%",
        })
    else:
        # --- メイン処理 ---
        _file_data = csv_uploader.value[0]
        _file_bytes: bytes = _file_data.contents

        with mo.status.spinner(title="QRコードを生成中…"):
            try:
                # CSV解析
                _rows = parse_csv(_file_bytes)

                if len(_rows) == 0:
                    result_area = mo.callout(
                        mo.md("⚠️ **有効なデータ行が見つかりませんでした。**\nCSVのフォーマットを確認してください。"),
                        kind="warn",
                    ).style({
                        "overflow-wrap": "anywhere",
                        "word-break": "break-word",
                        "white-space": "normal",
                        "max-width": "100%",
                    })
                else:
                    # QR一括生成 & ZIP化
                    _zip_bytes = build_zip(_rows)
                    _data_uri  = zip_to_data_uri(_zip_bytes)
                    _zip_size_kb = len(_zip_bytes) / 1024

                    # Layer 3: ダウンロードリンクに style 属性を直接埋め込む
                    # word-break:break-all でボタンラベルの強制折り返しを保証する
                    _download_link = (
                        f'<div style="{_wrap_style}">'
                        f'<a href="{_data_uri}" download="qr_codes.zip" '
                        f'style="display:block;padding:12px 16px;'
                        f'background:#2563eb;color:#fff;border-radius:8px;'
                        f'text-decoration:none;font-weight:bold;font-size:1rem;'
                        f'text-align:center;{_wrap_style}">'
                        f'📦 ZIP をダウンロード ({_zip_size_kb:.1f} KB)'
                        f'</a>'
                        f'</div>'
                    )

                    result_area = mo.vstack([
                        mo.callout(
                            mo.md(f"✅ **{len(_rows)} 件**のQRコードを生成しました。"),
                            kind="success",
                        ).style({
                            "overflow-wrap": "anywhere",
                            "word-break": "break-word",
                            "white-space": "normal",
                            "max-width": "100%",
                        }),
                        mo.Html(_download_link),
                    ]).style({
                        "max-width": "100%",
                        "overflow-x": "hidden",
                        "box-sizing": "border-box",
                    })

            except Exception as e:
                result_area = mo.callout(
                    mo.md(f"❌ **エラーが発生しました:**\n`{e}`\n\nCSVのエンコーディング（UTF-8）やフォーマットを確認してください。"),
                    kind="danger",
                ).style({
                    "overflow-wrap": "anywhere",
                    "word-break": "break-word",
                    "white-space": "normal",
                    "max-width": "100%",
                })

    result_area
    return (result_area,)


if __name__ == "__main__":
    app.run()