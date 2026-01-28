import marimo

__generated_with = "0.19.0"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    import altair as alt
    import pandas as pd
    from decimal import Decimal, ROUND_HALF_UP

    # 設定・定数
    COLOR_PRINCIPAL = "#0056b3"
    COLOR_PROFIT = "#28a745"
    
    return Decimal, ROUND_HALF_UP, alt, mo, pd, COLOR_PRINCIPAL, COLOR_PROFIT


@app.cell
def _(mo):
    # ヘッダーエリア
    mo.vstack([
        mo.md("# 📈 積立NISAシミュレーター"),
        mo.md("毎月の積立額と期間、利回りを入力すると、将来の資産推移をシミュレーションします。")
    ])
    return


@app.cell
def _(mo):
    # 入力フォーム
    # 【修正】stepを1000から100に変更し、細かい金額設定に対応
    input_monthly = mo.ui.slider(
        start=1000, stop=300000, step=100, value=30000, 
        label="毎月の積立額 (円)", full_width=True
    )
    input_years = mo.ui.slider(
        start=1, stop=50, step=1, value=20, 
        label="積立期間 (年)", full_width=True
    )
    input_rate = mo.ui.slider(
        start=0.1, stop=15.0, step=0.1, value=5.0, 
        label="想定利回り (%)", full_width=True
    )

    input_section = mo.vstack([
        mo.md("### 🛠 パラメーター設定"),
        mo.flex([input_monthly, input_years, input_rate], wrap=True, gap=1)
    ])
    return input_monthly, input_rate, input_section, input_years


@app.cell
def _(Decimal, ROUND_HALF_UP, input_monthly, input_rate, input_years, mo, pd):
    # --- 計算ロジック ---
    # 【修正】mo.status で計算中であることを明示
    with mo.status("資産推移をシミュレーション中..."):
        monthly_yen = input_monthly.value
        years = input_years.value
        rate_pct = input_rate.value

        if years <= 0:
            df_result = pd.DataFrame()
            final_total = final_principal = final_profit = 0
        else:
            d_monthly = Decimal(str(monthly_yen))
            d_rate_annual = Decimal(str(rate_pct)) / Decimal("100")
            d_rate_monthly = d_rate_annual / Decimal("12")
            
            months = int(years * 12)
            data = []
            current_principal = Decimal("0")
            current_total = Decimal("0")

            data.append({"Year": 0, "Principal": 0, "Profit": 0, "Total": 0})

            for m in range(1, months + 1):
                current_principal += d_monthly
                current_total = (current_total + d_monthly) * (Decimal("1") + d_rate_monthly)

                if m % 12 == 0:
                    year = m // 12
                    principal_int = int(current_principal.quantize(Decimal("1."), rounding=ROUND_HALF_UP))
                    total_int = int(current_total.quantize(Decimal("1."), rounding=ROUND_HALF_UP))
                    data.append({
                        "Year": year,
                        "Principal": principal_int,
                        "Profit": total_int - principal_int,
                        "Total": total_int
                    })
            
            df_result = pd.DataFrame(data)
            last_rec = df_result.iloc[-1]
            final_total = last_rec["Total"]
            final_principal = last_rec["Principal"]
            final_profit = last_rec["Profit"]

    return df_result, final_principal, final_profit, final_total


@app.cell
def _(final_principal, final_profit, final_total, mo):
    # --- KPI表示 (Modern Style) ---
    kpi_section = mo.vstack([
        mo.md("### 📊 シミュレーション結果"),
        mo.flex([
            mo.stat(
                value=f"¥{final_total:,.0f}", 
                label="総資産", 
                caption="積立総額 + 運用益",
                bordered=True
            ),
            mo.stat(
                value=f"¥{final_principal:,.0f}", 
                label="元本", 
                bordered=True
            ),
            mo.stat(
                value=f"¥{final_profit:,.0f}", 
                label="運用益", 
                direction="increase" if final_profit >= 0 else "decrease",
                bordered=True
            )
        ], wrap=True, gap=1, justify="start")
    ])
    return kpi_section


@app.cell
def _(COLOR_PRINCIPAL, COLOR_PROFIT, alt, df_result, mo):
    # --- グラフ描画 (Responsive) ---
    if df_result.empty:
        chart_ui = mo.md("データがありません")
    else:
        df_melt = df_result.melt(
            id_vars=["Year"], value_vars=["Principal", "Profit"],
            var_name="Type", value_name="Amount"
        )
        
        # width="container" でレスポンシブ対応
        base_chart = alt.Chart(df_melt).mark_area(opacity=0.85).encode(
            x=alt.X("Year", title="経過年数"),
            y=alt.Y("Amount", title="金額", stack=True),
            color=alt.Color("Type", scale=alt.Scale(domain=["Principal", "Profit"], range=[COLOR_PRINCIPAL, COLOR_PROFIT]), legend=alt.Legend(title="内訳")),
            tooltip=["Year", "Type", alt.Tooltip("Amount", format=",", title="金額")]
        ).properties(
            width="container",
            height=300
        )

        chart_ui = mo.ui.altair_chart(base_chart)

    return chart_ui


@app.cell
def _(chart_ui, input_section, kpi_section, mo):
    # 最終レイアウト
    mo.vstack([
        input_section,
        kpi_section,
        chart_ui
    ], gap=1.5)
    return


if __name__ == "__main__":
    app.run()