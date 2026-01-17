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
    
    # Altair設定: メニューを隠し、コンテナ幅に合わせる
    alt.renderers.enable('default', embed_options={'actions': False})
    
    # カラーパレット
    COLOR_PRINCIPAL = "#0056b3"  # 元本（青）
    COLOR_PROFIT = "#28a745"     # 利益（緑）
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
    # --- 計算ロジック (純粋な関数として定義) ---
    
    def calculate_asset_growth(monthly_yen: int, years: int, rate_pct: float) -> pd.DataFrame:
        """
        積立シミュレーションを行い、年ごとの推移をDataFrameで返す
        """
        if years <= 0:
            return pd.DataFrame()

        # 高精度計算のためのDecimal変換
        d_monthly = Decimal(str(monthly_yen))
        d_rate_annual = Decimal(str(rate_pct)) / Decimal("100")
        d_rate_monthly = d_rate_annual / Decimal("12")
        
        months = int(years * 12)
        data = []
        
        current_principal = Decimal("0")
        current_total = Decimal("0")

        # 0年目の初期状態
        data.append({"Year": 0, "Principal": 0, "Profit": 0, "Total": 0})

        for m in range(1, months + 1):
            # 月初に積立 → 月末に利息がつくと仮定
            current_principal += d_monthly
            current_total = (current_total + d_monthly) * (Decimal("1") + d_rate_monthly)

            # 1年ごとに記録
            if m % 12 == 0:
                year = m // 12
                # 表示用に整数丸め
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
    
    # 画像があれば表示、なければタイトルのみ
    # width="100%" と object-fit でレスポンシブ対応を確実に
    try:
        header_visual = mo.image(
            src=HEADER_IMAGE,
            alt="Header",
            width="100%",
            style={"max-height": "250px", "object-fit": "cover", "border-radius": "8px"}
        )
    except:
        header_visual = mo.md("")

    header_section = mo.vstack([
        header_visual,
        mo.md(f"# 📈 {APP_TITLE}"),
        mo.md("毎月の積立額と期間、利回りを入力すると、将来の資産推移をシミュレーションします。")
    ], gap=1)
    return header_section, header_visual


@app.cell
def _(mo):
    # --- UI: 入力フォーム ---
    # スマホ対応: hstackではなく、PCでもスマホでも使いやすいvstackベースにするか
    # 幅に余裕がある場合のみ横並びになるような設計が望ましいが、
    # スライダーは横幅を食うため、ここでは安全に「縦積み」を採用する。
    
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

    # 入力エリアのレイアウト
    input_section = mo.md(
        """
        ### 🛠 パラメーター設定
        """
    )
    return input_monthly, input_rate, input_section, input_years


@app.cell
def _(calculate_asset_growth, input_monthly, input_rate, input_years):
    # --- データ処理 ---
    # UIの値をリアルタイムに取得して計算
    df_result = calculate_asset_growth(
        input_monthly.value,
        input_years.value,
        input_rate.value
    )
    
    # 最終結果の抽出（統計表示用）
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

    # 1. 統計カード (marimo.stat を使用してクリーンに)
    stats_section = mo.hstack([
        mo.stat(
            label="総資産",
            value=f"{final_total:,.0f}円",
            caption="積み立てた結果の総額",
            kind="neutral" # 色付けなし
        ),
        mo.stat(
            label="元本総額",
            value=f"{final_principal:,.0f}円",
            caption="あなたが積み立てた金額"
        ),
        mo.stat(
            label="運用収益",
            value=f"+{final_profit:,.0f}円",
            caption="増えた金額",
            kind="success" # 緑色
        )
    ], gap=1, widths="equal") # widths="equal" でスマホでも綺麗に折り返されることが多い

    # 2. グラフ描画
    if df_result.empty:
        chart = mo.md("データがありません")
    else:
        # Altair用にデータを変形 (Wide -> Long)
        df_melt = df_result.melt(
            id_vars=["Year"], 
            value_vars=["Principal", "Profit"],
            var_name="Type", 
            value_name="Amount"
        )
        
        # 日本語ラベルへの置換マップ
        label_map = {"Principal": "元本", "Profit": "運用益"}
        color_map = {"Principal": COLOR_PRINCIPAL, "Profit": COLOR_PROFIT}
        
        df_melt["Label"] = df_melt["Type"].map(label_map)

        # チャート定義
        chart = alt.Chart(df_melt).mark_area(opacity=0.85).encode(
            x=alt.X("Year", axis=alt.Axis(title="経過年数 (年)")),
            y=alt.Y("Amount", axis=alt.Axis(format="~s", title="金額 (円)"), stack=True),
            color=alt.Color(
                "Type",
                scale=alt.Scale(domain=["Principal", "Profit"], range=[COLOR_PRINCIPAL, COLOR_PROFIT]),
                legend=alt.Legend(title=None, labelExpr=f"datum.value == 'Principal' ? '元本' : '運用益'"),
            ),
            tooltip=[
                alt.Tooltip("Year", title="年数"),
                alt.Tooltip("Label", title="内訳"),
                alt.Tooltip("Amount", format=",.0f", title="金額(円)")
            ]
        ).properties(
            # ★重要: width='container' で親要素に合わせて伸縮させる
            width="container",
            height=350
        )

    return chart, color_map, df_melt, label_map, stats_section


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
        mo.md("---"), # 区切り線
        
        input_section,
        # vstackを使用することで、スマホでも無理なく表示できる
        mo.vstack([
            input_monthly,
            input_years,
            input_rate
        ], gap=1),
        
        mo.md("### 📊 シミュレーション結果"),
        stats_section,
        
        # チャートを配置（mo.ui.altair_chartは不要、直接オブジェクトを置く）
        chart
        
    ], gap=1.5) # 要素間の余白を統一

    app_layout
    return app_layout,


if __name__ == "__main__":
    app.run()