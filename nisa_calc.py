import marimo

__generated_with = "0.10.9"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import altair as alt
    import pandas as pd
    from decimal import Decimal, ROUND_HALF_UP

    # --- 設定・定数 ---
    APP_TITLE = "積立NISAシミュレーター"
    HEADER_IMAGE = "assets/header.png"
    
    # Altair設定
    alt.renderers.enable('default', embed_options={'actions': False})
    
    # カラーパレット
    COLOR_PRINCIPAL = "#0056b3"
    COLOR_PROFIT = "#28a745"
    
    return (
        APP_TITLE,
        COLOR_PRINCIPAL,
        COLOR_PROFIT,
        Decimal,
        HEADER_IMAGE,
        ROUND_HALF_UP,
        alt,
        mo,
        pd,
    )


@app.cell
def _(Decimal, ROUND_HALF_UP, pd):
    # --- 計算ロジック ---
    def calculate_asset_growth(monthly_yen: int, years: int, rate_pct: float) -> pd.DataFrame:
        if years <= 0:
            return pd.DataFrame()

        # 高精度計算
        d_monthly = Decimal(str(monthly_yen))
        d_rate_annual = Decimal(str(rate_pct)) / Decimal("100")
        d_rate_monthly = d_rate_annual / Decimal("12")
        
        months = int(years * 12)
        data = []
        
        current_principal = Decimal("0")
        current_total = Decimal("0")

        # 0年目
        data.append({"Year": 0, "Principal": 0, "Profit": 0, "Total": 0})

        for m in range(1, months + 1):
            current_principal += d_monthly
            current_total = (current_total + d_monthly) * (Decimal("1") + d_rate_monthly)

            if m % 12 == 0:
                year = m // 12
                principal_int = int(current_principal.quantize(Decimal("1."), rounding=ROUND_HALF_UP))
                total_int = int(current_total.quantize(Decimal("1."), rounding=ROUND_HALF_UP))
                profit_int = total_int - principal_int
                
                data.append({
                    "Year": year,
                    "Principal": principal_int,
                    "Profit": profit_int,
                    "Total": total_int
                })
                
        return pd.DataFrame(data)
    return calculate_asset_growth,


@app.cell
def _(APP_TITLE, HEADER_IMAGE, mo):
    # --- UI: ヘッダーエリア ---
    try:
        header_visual = mo.image(
            src=HEADER_IMAGE,
            alt="Header",
            width="100%",
            style={"max-height": "250px", "object-fit": "cover", "border-radius": "8px"}
        )
    except:
        header_visual = mo.md("")

    # テキスト周りのスタイル定義（改行強制）
    text_style = "width: 100%; overflow-wrap: break-word; line-height: 1.6; color: #444;"

    description = mo.md(
        f"""
        <div style="display: flex; flex-direction: column; gap: 10px;">
            <h2 style="margin: 0; font-size: 1.6rem; line-height: 1.3;">📈 {APP_TITLE}</h2>
            <div style="{text_style}">
                毎月の積立額と期間、利回りを入力すると、将来の資産推移をシミュレーションします。
            </div>
        </div>
        """
    )

    header_section = mo.vstack([
        header_visual,
        description
    ], gap=1)
    return header_section, header_visual


@app.cell
def _(mo):
    # --- UI: 入力フォーム ---
    input_monthly = mo.ui.slider(
        start=1000, stop=300000, step=1000, value=30000, 
        label="毎月の積立額 (円)", 
        full_width=True
    )
    input_years = mo.ui.slider(
        start=1, stop=50, step=1, value=20, 
        label="積立期間 (年)", 
        full_width=True
    )
    input_rate = mo.ui.slider(
        start=0.1, stop=15.0, step=0.1, value=5.0, 
        label="想定利回り (%)", 
        full_width=True
    )

    input_section = mo.md("### 🛠 パラメーター設定")
    return input_monthly, input_rate, input_section, input_years


@app.cell
def _(calculate_asset_growth, input_monthly, input_rate, input_years):
    # --- データ処理 ---
    df_result = calculate_asset_growth(
        input_monthly.value,
        input_years.value,
        input_rate.value
    )
    
    if not df_result.empty:
        last_rec = df_result.iloc[-1]
        final_total = last_rec["Total"]
        final_principal = last_rec["Principal"]
        final_profit = last_rec["Profit"]
    else:
        final_total = final_principal = final_profit = 0
    return df_result, final_principal, final_profit, final_total, last_rec


@app.cell
def _(
    COLOR_PRINCIPAL,
    COLOR_PROFIT,
    alt,
    df_result,
    final_principal,
    final_profit,
    final_total,
    mo,
):
    # --- ビジュアライゼーション ---

    # 1. 統計カード (Flexboxレスポンシブ)
    card_style = (
        "flex: 1 1 140px; "
        "padding: 10px; "
        "border: 1px solid #e0e0e0; "
        "border-radius: 8px; "
        "background: #fff; "
        "text-align: center; "
        "box-shadow: 0 2px 4px rgba(0,0,0,0.05);"
    )
    
    label_style = "font-size: 0.8rem; color: #666; margin-bottom: 4px;"
    value_style = "font-size: 1.1rem; font-weight: bold; color: #333;"
    sub_style = "font-size: 0.7rem; color: #888; margin-top: 4px;"

    stats_html = f"""
    <div style="display: flex; flex-wrap: wrap; gap: 8px; width: 100%;">
        <div style="{card_style} border-left: 4px solid {COLOR_PRINCIPAL};">
            <div style="{label_style}">総資産</div>
            <div style="{value_style}">¥{final_total:,.0f}</div>
            <div style="{sub_style}">積立総額</div>
        </div>
        <div style="{card_style}">
            <div style="{label_style}">元本</div>
            <div style="{value_style}">¥{final_principal:,.0f}</div>
        </div>
        <div style="{card_style}">
            <div style="{label_style}">収益</div>
            <div style="{value_style} color: {COLOR_PROFIT};">+¥{final_profit:,.0f}</div>
        </div>
    </div>
    """
    stats_section = mo.md(stats_html)

    # 2. グラフ描画（横スクロール対応）
    if df_result.empty:
        chart = mo.md("データがありません")
    else:
        df_melt = df_result.melt(
            id_vars=["Year"], value_vars=["Principal", "Profit"],
            var_name="Type", value_name="Amount"
        )
        label_map = {"Principal": "元本", "Profit": "運用益"}
        df_melt["Label"] = df_melt["Type"].map(label_map)

        # ベースとなるグラフ
        base_chart = alt.Chart(df_melt).mark_area(opacity=0.85).encode(
            x=alt.X("Year", axis=alt.Axis(title="経過年数")),
            y=alt.Y("Amount", axis=alt.Axis(format="~s", title="円"), stack=True),
            color=alt.Color("Type", scale=alt.Scale(domain=["Principal", "Profit"], range=[COLOR_PRINCIPAL, COLOR_PROFIT]), legend=None),
            tooltip=["Year", "Label", alt.Tooltip("Amount", format=",")]
        ).properties(
            width=350,  # 固定幅
            height=300
        )

        # コンポーネント化（スクロールラッパー）
        chart_obj = mo.ui.altair_chart(base_chart)
        
        # 【重要】変数名を chart に統一して返す
        chart = mo.vstack([
            mo.md("※ グラフは横にスクロールできます"),
            mo.md(
                """
                <div style="width: 100%; overflow-x: auto; padding-bottom: 10px; -webkit-overflow-scrolling: touch;">
                """
            ),
            chart_obj,
            mo.md("</div>")
        ], gap=0)

    return chart, df_melt, label_map, stats_section


@app.cell
def _(
    chart,
    header_section,
    input_monthly,
    input_rate,
    input_section,
    input_years,
    mo,
    stats_section,
):
    # --- 最終レイアウト組立 ---
    app_layout = mo.vstack([
        header_section,
        mo.md("---"),
        input_section,
        mo.vstack([
            input_monthly,
            input_years,
            input_rate
        ], gap=1),
        mo.md("### 📊 シミュレーション結果"),
        stats_section,
        chart
    ], gap=1.5)

    app_layout
    return app_layout,


@app.cell
def _(mo):
    # 【CSS注入】スマホ完全対応版
    mo.md(
        """
        <style>
        /* 1. アプリ全体の横幅を画面幅に強制固定し、全体スクロールを防ぐ */
        html, body, #root, .marimo {
            max-width: 100vw !important;
            overflow-x: hidden !important;
            margin: 0 !important;
            padding: 5px !important;
        }

        /* 2. Flexboxの「縮まない」問題を解決するリセット */
        * {
            min-width: 0 !important;
            box-sizing: border-box !important;
        }

        /* 3. テキストの強制折り返し */
        p, h1, h2, h3, div, span, label {
            overflow-wrap: break-word !important;
            word-wrap: break-word !important;
            white-space: normal !important;
            max-width: 100% !important;
        }

        /* 4. Canvas/画像のリサイズ */
        canvas, img, svg {
            max-width: 100% !important;
            height: auto !important;
        }
        
        /* 5. marimoのUI要素 */
        .marimo-ui-element {
            max-width: 100% !important;
        }
        </style>
        """
    )
    return


if __name__ == "__main__":
    app.run()