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


@app.cell
def _(mo):
    # スマホ最適化CSS（レスポンシブ対応）の注入
    mobile_css = mo.md("""
    <style>
    /* 画面の横揺れ・はみ出しを防止 */
    body, html, .marimo {
        max-width: 100vw !important;
        overflow-x: hidden !important;
        box-sizing: border-box !important;
    }

    /* 長いテキストやCallout（ヒント枠）の折り返しを強制 */
    p, span, div, blockquote, .marimo-callout, strong, b, h1, h2, h3, h4, h5, h6 {
        white-space: normal !important;
        overflow-wrap: break-word !important;
        word-wrap: break-word !important;
        max-width: 100% !important;
    }

    /* ボタン内のテキストを折り返し、高さを自動調整 */
    button {
        white-space: normal !important;
        height: auto !important;
        min-height: 44px !important;
        line-height: 1.4 !important;
        padding: 10px !important;
    }

    /* テーブル（CSVプレビュー）が横に長い場合はスクロールさせる */
    table {
        display: block !important;
        overflow-x: auto !important;
        white-space: nowrap !important;
        max-width: 100% !important;
    }
    </style>
    """)
    return mobile_css,


@app.cell
def _imports():
    import marimo as mo
    import csv
    import io
    import zipfile
    import base64
    import segno
    return base64, csv, io, mo, segno, zipfile


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
    # 重複ラベルが連番サフィックスで区別されている
    assert "店舗A.png" in _names, "1件目のラベルファイルが存在しない"
    assert "店舗A_001.png" in _names, "重複ラベルに連番が付与されていない"
    assert "店舗B.png" in _names, "店舗Bのファイルが存在しない"

    print("✅ generate_qr_png_bytes / build_zip: 全テスト通過")
    return


@app.cell
def _ui(mo):
    # ヘッダー
    _header = mo.md("""
    # 🔒 Secure QR Batch Maker
    **完全ブラウザ処理 — あなたのデータはサーバーに一切送信されません**

    ---
    ### 📋 CSVフォーマット
    | 列1（ラベル） | 列2（QR化するURL） |
    |---|---|
    | 店舗A | https://example.com/A |
    | 店舗B | https://example.com/B |

    > **ヒント:** ヘッダー行は自動的にスキップされます。
    > 列が1列だけの場合、その列をURLとして使用し、行番号をファイル名とします。
    """)

    # CSVアップロードウィジェット
    csv_uploader = mo.ui.file(
        filetypes=[".csv"],
        label="① CSVファイルを選択してください",
    )

    # QR生成実行ボタン
    run_button = mo.ui.run_button(
        label="② QRコードを一括生成してZIPをダウンロード ▶",
        full_width=True,
    )

    mo.vstack([
        _header,
        csv_uploader,
        run_button,
    ])
    return csv_uploader, run_button


@app.cell
def _result(
    build_zip,
    csv_uploader,
    mo,
    parse_csv,
    run_button,
    zip_to_data_uri,
):
    # ボタンが押されていない場合は何も表示しない
    mo.stop(not run_button.value)

    # ファイルが未選択の場合はエラー表示
    if not csv_uploader.value or len(csv_uploader.value) == 0:
        result_area = mo.callout(
            mo.md("⚠️ **CSVファイルが選択されていません。** ファイルをアップロードしてから実行してください。"),
            kind="warn",
        )
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
                        mo.md("⚠️ **有効なデータ行が見つかりませんでした。** CSVのフォーマットを確認してください。"),
                        kind="warn",
                    )
                else:
                    # QR一括生成 & ZIP化
                    _zip_bytes = build_zip(_rows)
                    _data_uri  = zip_to_data_uri(_zip_bytes)
                    _zip_size_kb = len(_zip_bytes) / 1024

                    # ダウンロードリンクを生成
                    _download_link = f'<a href="{_data_uri}" download="qr_codes.zip" style="display:inline-block;padding:12px 24px;background:#2563eb;color:#fff;border-radius:8px;text-decoration:none;font-weight:bold;font-size:1rem;">📦 ZIP をダウンロード ({_zip_size_kb:.1f} KB)</a>'

                    result_area = mo.vstack([
                        mo.callout(
                            mo.md(f"✅ **{len(_rows)} 件**のQRコードを生成しました。"),
                            kind="success",
                        ),
                        mo.Html(_download_link),
                    ])

            except Exception as e:
                result_area = mo.callout(
                    mo.md(f"❌ **エラーが発生しました:** `{e}`\n\nCSVのエンコーディング（UTF-8）やフォーマットを確認してください。"),
                    kind="danger",
                )

    result_area
    return


if __name__ == "__main__":
    app.run()
