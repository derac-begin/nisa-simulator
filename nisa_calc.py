import marimo

__generated_with = "0.10.9"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import altair as alt
    import pandas as pd
    from typing import Dict, List, Union, Tuple, Optional
    import math
    from decimal import Decimal, ROUND_HALF_UP, Context

    # Altairのグラフメニュー（右上の...）を非表示にする設定
    alt.renderers.enable('default', embed_options={'actions': False})
    
    # --- 設定・定数 ---
    APP_TITLE = "積立NISAシミュレーター | 堅牢・精密版"
    THEME_COLOR_PRIMARY = "#0056b3"  # 信頼の青
    THEME_COLOR_GROWTH = "#28a745"   # 成長の緑
    HEADER_IMAGE_PATH = "assets/header.png"
    
    # 財務的な制限値
    MAX_INVESTMENT = 1_000_000_000  # 上限10億円
    MAX_YEARS = 100
    MAX_RATE = 100.0  # 最大利回り100%

    return (
        APP_TITLE,
        Context,
        Decimal,
        Dict,
        HEADER_IMAGE_PATH,
        List,
        MAX_INVESTMENT,
        MAX_RATE,
        MAX_YEARS,
        Optional,
        ROUND_HALF_UP,
        THEME_COLOR_GROWTH,
        THEME_COLOR_PRIMARY,
        Tuple,
        Union,
        alt,
        math,
        mo,
        pd,
    )


@app.cell
def _(mo):
    mo.md(
        """
        # 📈 積立NISA スマートシミュレーター
        
        将来の資産推移を**精密な財務計算**でシミュレーションします。

        ※ グラフ右上の「...」から画像を保存できます（メニューは英語表記です）
        """
    )
    return


@app.cell
def _(HEADER_IMAGE_PATH, mo):
    # ヘッダー画像
    # styleで高さを制限し、object-fitでトリミング調整
    header_img = mo.image(
        src=HEADER_IMAGE_PATH, 
        rounded=True, 
        alt="将来の資産形成イメージグラフ",
        width="100%",
        style={"max-height": "300px", "object-fit": "cover"} 
    )
    return header_img,


@app.cell
def _(
    Decimal,
    Dict,
    List,
    MAX_INVESTMENT,
    MAX_RATE,
    MAX_YEARS,
    ROUND_HALF_UP,
    Tuple,
    Union,
    math,
    pd,
):
    def validate_input(
        monthly_amount: Union[int, float], years: int, rate_percent: Union[int, float]
    ) -> Tuple[bool, str]:
        """
        Strictly validates user inputs.
        Checks for types, ranges, and special floating point values (NaN, Inf).
        """
        try:
            # Check 1: Type Safety & NaN/Inf Check
            if not isinstance(monthly_amount, (int, float)):
                return False, "Investment amount must be a number."
            if math.isnan(monthly_amount) or math.isinf(monthly_amount):
                return False, "Invalid investment amount value."
            
            if not isinstance(years, (int, float)): # Slider might return float
                 return False, "Years must be a number."
            if math.isnan(years) or math.isinf(years):
                 return False, "Invalid years value."
            
            if not isinstance(rate_percent, (int, float)):
                return False, "Rate must be a number."
            if math.isnan(rate_percent) or math.isinf(rate_percent):
                return False, "Invalid rate value."

            # Check 2: Range Logic
            if monthly_amount < 0:
                return False, "Investment amount cannot be negative."
            if monthly_amount > MAX_INVESTMENT:
                return False, f"Investment amount exceeds limit (¥{MAX_INVESTMENT:,})."

            if years < 0 or years > MAX_YEARS:
                return False, f"Years must be between 0 and {MAX_YEARS}."

            if rate_percent < 0 or rate_percent > MAX_RATE:
                return False, "Rate is invalid (0-100%)."

            return True, ""

        except Exception as e:
            # Fail safe for any unexpected validation errors
            return False, f"Validation error: {str(e)}"

    def calculate_compound_interest(
        monthly_amount: float, years: int, rate_percent: float
    ) -> pd.DataFrame:
        """
        Calculates yearly asset progression using Decimal for financial precision.
        """
        # 1. Validation
        is_valid, err = validate_input(monthly_amount, years, rate_percent)
        if not is_valid:
            # Return empty DF. The UI handles the error message display.
            return pd.DataFrame({"Year": [], "Principal": [], "Interest": [], "Total": []})

        try:
            # 2. Convert to Decimal for precise calculation
            # Use string conversion to avoid float artifacting before Decimal conversion
            d_monthly = Decimal(str(monthly_amount))
            d_rate_annual = Decimal(str(rate_percent)) / Decimal("100")
            d_rate_monthly = d_rate_annual / Decimal("12")
            
            months = int(years * 12)
            
            data: List[Dict[str, Union[int, float]]] = []
            
            current_principal = Decimal("0")
            current_total = Decimal("0")

            # 3. Calculation Loop
            for m in range(1, months + 1):
                current_principal += d_monthly
                # Monthly compounding formula: (Previous + MonthlyInput) * (1 + MonthlyRate)
                # Assumes investment at start of month or simply adds to pot before interest
                # Simple model: Add money, then apply interest
                current_total = (current_total + d_monthly) * (Decimal("1") + d_rate_monthly)

                # Record at year end
                if m % 12 == 0:
                    year = m // 12
                    interest = current_total - current_principal
                    
                    # Rounding down/half-up to integer for display (Yen has no cents)
                    # Quantize ensures consistent rounding strategy
                    data.append({
                        "Year": int(year),
                        "Principal": int(current_principal.quantize(Decimal("1."), rounding=ROUND_HALF_UP)),
                        "Interest": int(interest.quantize(Decimal("1."), rounding=ROUND_HALF_UP)),
                        "Total": int(current_total.quantize(Decimal("1."), rounding=ROUND_HALF_UP))
                    })

            # Handle Year 0
            if years == 0:
                data.append({"Year": 0, "Principal": 0, "Interest": 0, "Total": 0})
            elif data and data[0]["Year"] != 0:
                data.insert(0, {"Year": 0, "Principal": 0, "Interest": 0, "Total": 0})

            return pd.DataFrame(data)

        except Exception as e:
            # Catch-all for calculation errors (e.g. Overflow) to prevent crash
            print(f"Calculation Error: {e}")
            return pd.DataFrame()

    return calculate_compound_interest, validate_input


@app.cell
def _(mo):
    # UIコンポーネント
    investment_input = mo.ui.slider(
        start=1000, stop=300000, step=1000, value=30000, 
        label="毎月の積立額 (円)", full_width=True
    )

    years_input = mo.ui.slider(
        start=1, stop=40, step=1, value=20, 
        label="積立期間 (年)", full_width=True
    )

    rate_input = mo.ui.slider(
        start=0.1, stop=15.0, step=0.1, value=5.0, 
        label="想定利回り (年率 %)", full_width=True
    )
    return investment_input, rate_input, years_input


@app.cell
def _(
    calculate_compound_interest,
    investment_input,
    mo,
    rate_input,
    validate_input,
    years_input,
):
    # Logic Controller
    inv_amount = investment_input.value
    inv_years = years_input.value
    inv_rate = rate_input.value

    # Validate specifically for UI Feedback
    _is_valid, _err_msg = validate_input(inv_amount, inv_years, inv_rate)

    if not _is_valid:
        # Display specific error message securely
        error_callout = mo.callout(_err_msg, kind="danger")
        results_df = None
    else:
        error_callout = None
        results_df = calculate_compound_interest(inv_amount, inv_years, inv_rate)
    
    return error_callout, inv_amount, inv_rate, inv_years, results_df


@app.cell
def _(
    THEME_COLOR_GROWTH,
    THEME_COLOR_PRIMARY,
    alt,
    mo,
    results_df,
):
    # Visualization Logic
    if results_df is None or results_df.empty:
        chart_viz = mo.md(
            """
            <div style="padding: 20px; text-align: center; color: gray;">
             数値を入力してシミュレーションを開始してください...
            </div>
            """
        )
        summary_stats = mo.md("")
    else:
        # 1. 日本語用にカラム名を変更（リネーム）
        df_jp = results_df.rename(columns={
            'Year': '経過年数',
            'Principal': '元本',
            'Interest': '運用益',
            'Total': '総資産'
        })

        # 2. グラフ用にデータを整形 (Melt)
        try:
            df_melted = df_jp.melt(
                id_vars=['経過年数'], 
                value_vars=['元本', '運用益'], 
                var_name='内訳', 
                value_name='金額'
            )
            
            # 3. グラフ定義 (日本語カラムを使用)
            base = alt.Chart(df_melted).encode(
                x=alt.X('経過年数', axis=alt.Axis(title='経過年数 (年)')),
                y=alt.Y('金額', axis=alt.Axis(format='~s', title='金額 (円)')),
                color=alt.Color(
                    '内訳', 
                    scale=alt.Scale(
                        domain=['元本', '運用益'], 
                        range=[THEME_COLOR_PRIMARY, THEME_COLOR_GROWTH]
                    )
                ),
                tooltip=['経過年数', '内訳', alt.Tooltip('金額', format=',.0f')]
            ).properties(height=400)
            
            chart_viz = base.mark_area(opacity=0.8).interactive()
            
            # Summary Metrics (ここはそのままでOKです)
            last_row = results_df.iloc[-1]
            total_principal = last_row['Principal']
            total_profit = last_row['Interest']
            total_asset = last_row['Total']
            
            summary_stats = mo.hstack([
                mo.stat(value=f"¥{total_asset:,.0f}", label="総資産", bordered=True),
                mo.stat(value=f"¥{total_principal:,.0f}", label="総元金", bordered=True),
                mo.stat(value=f"+¥{total_profit:,.0f}", label="総運用益", bordered=True),
            ], gap=2)
            
        except Exception as e:
            chart_viz = mo.callout(f"Visualization Error: {e}", kind="danger")
            summary_stats = mo.md("")

    return (
        base,
        chart_viz,
        df_melted,
        last_row,
        summary_stats,
        total_asset,
        total_principal,
        total_profit,
    )


@app.cell
def _(
    app_layout,
    chart_viz,
    error_callout,
    header_img,
    investment_input,
    mo,
    rate_input,
    summary_stats,
    years_input,
):
    # App Layout
    app_layout = mo.vstack([
        header_img,
        mo.md("## パラメーター"),
        mo.hstack([investment_input, years_input, rate_input], gap=2),
        error_callout if error_callout else mo.md(""),
        mo.md("## シミュレーション結果"),
        summary_stats,
        chart_viz
    ])
    return app_layout,


@app.cell
def _(app_layout):
    app_layout
    return


if __name__ == "__main__":
    app.run()