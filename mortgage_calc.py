import marimo

__generated_with = "0.10.9"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import altair as alt
    from decimal import Decimal, ROUND_HALF_UP, ROUND_FLOOR
    import decimal

    # 金融計算のための精度設定
    decimal.getcontext().prec = 60
    return Decimal, ROUND_FLOOR, ROUND_HALF_UP, alt, decimal, mo, pd


@app.cell
def _(mo):
    mo.md(
        """
        # 🏠 住宅ローン返済シミュレーター
        ---
        """
    )
    return


@app.cell
def _(mo):
    # グローバルCSSの注入
    mo.md(
        """
        <style>
        .marimo { max-width: 1000px !important; margin: 0 auto; }
        .input-card-box {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 16px;
            width: 100%;
        }
        .metric-card {
            min-width: 280px;
            padding: 16px;
            border-radius: 12px;
            background: #f8fafc;
            border-left: 6px solid #3b82f6;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        }
        .metric-title { font-size: 0.9rem; color: #64748b; font-weight: 600; }
        .metric-value { font-size: 1.5rem; color: #1e293b; font-weight: 800; margin: 4px 0; }
        .metric-unit { font-size: 0.85rem; color: #94a3b8; margin-left: 4px; }
        .scrollable-wrapper {
            width: 100%;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            margin-top: 10px;
        }
        </style>
        """
    )
    return


@app.cell
def _(mo):
    # ---------------------------------------------------------
    # 入力UIコンポーネント
    # ---------------------------------------------------------
    loan_amount_ui = mo.ui.number(
        label="借入金額 (万円)", start=100, stop=50000, step=10, value=3500, full_width=True
    )
    interest_rate_ui = mo.ui.number(
        label="年利 (%)", start=0.0, stop=20.0, step=0.001, value=0.525, full_width=True
    )
    years_ui = mo.ui.slider(
        label="返済期間 (年)", start=1, stop=50, step=1, value=35, full_width=True
    )
    method_ui = mo.ui.dropdown(
        label="返済方式",
        options={
            "元利均等返済": "元利均等返済 (毎月一定額)",
            "元金均等返済": "元金均等返済 (元金が一定)"
        },
        value="元利均等返済",
        full_width=True
    )
    bonus_toggle_ui = mo.ui.switch(label="ボーナス払いを利用する", value=False)
    
    return bonus_toggle_ui, interest_rate_ui, loan_amount_ui, method_ui, years_ui


@app.cell
def _(bonus_toggle_ui, loan_amount_ui, mo):
    # ボーナス設定の動的表示
    _max_bonus = int(loan_amount_ui.value * 0.5)
    bonus_amount_ui = mo.ui.number(
        label="ボーナス払い合計額 (万円)", 
        start=0, 
        stop=_max_bonus, 
        step=10, 
        value=0,
        full_width=True
    )
    
    bonus_section = mo.vstack([
        mo.md(f"**🎁 ボーナス設定** (上限: {_max_bonus}万円)"),
        bonus_amount_ui
    ]) if bonus_toggle_ui.value else None
    
    return bonus_amount_ui, bonus_section


@app.cell
def _(
    bonus_section,
    bonus_toggle_ui,
    interest_rate_ui,
    loan_amount_ui,
    method_ui,
    mo,
    years_ui,
):
    # メイン画面上部の入力エリア設定
    # f-string内でのUI展開を避け、mo.flex / mo.vstackで構築
    input_fields = mo.flex(
        [
            mo.vstack([loan_amount_ui], width="100%"),
            mo.vstack([interest_rate_ui], width="100%"),
            mo.vstack([years_ui], width="100%"),
            mo.vstack([method_ui], width="100%"),
        ],
        wrap=True,
        gap=1,
        justify="start"
    )

    mo.vstack([
        mo.md("### ⚙️ ローン設定"),
        mo.Html(f'<div class="input-card-box">').append(
            mo.vstack([
                input_fields,
                mo.flex([bonus_toggle_ui], justify="start"),
                bonus_section if bonus_section else mo.md("")
            ], gap=1.5)
        ).append('</div>')
    ])
    return (input_fields,)


@app.cell
def _(
    Decimal,
    ROUND_FLOOR,
    ROUND_HALF_UP,
    bonus_amount_ui,
    bonus_toggle_ui,
    interest_rate_ui,
    loan_amount_ui,
    method_ui,
    years_ui,
):
    # ---------------------------------------------------------
    # 計算エンジン (シミュレーション実行)
    # ---------------------------------------------------------
    def calculate():
        P_total = Decimal(str(loan_amount_ui.value)) * Decimal("10000")
        annual_rate = Decimal(str(interest_rate_ui.value)) / Decimal("100")
        monthly_rate = annual_rate / Decimal("12")
        total_months = int(years_ui.value) * 12
        method = method_ui.value
        
        P_bonus_total = Decimal(str(bonus_amount_ui.value)) * Decimal("10000") if bonus_toggle_ui.value else Decimal("0")
        P_monthly_total = P_total - P_bonus_total
        
        schedule = []
        rem_p_monthly = P_monthly_total
        rem_p_bonus = P_bonus_total
        
        def get_annuity_pmt(principal, rate, n):
            if rate == 0: return principal / n
            return principal * (rate * (1 + rate)**n) / ((1 + rate)**n - 1)

        # 毎月の返済（元利均等）
        fixed_m_pmt = get_annuity_pmt(P_monthly_total, monthly_rate, total_months).quantize(Decimal("1"), ROUND_HALF_UP)
        # ボーナス返済（年2回、元利均等）
        fixed_b_pmt = get_annuity_pmt(P_bonus_total, annual_rate / Decimal("2"), int(years_ui.value) * 2).quantize(Decimal("1"), ROUND_HALF_UP) if bonus_toggle_ui.value else Decimal("0")

        cum_interest = Decimal("0")

        for m in range(1, total_months + 1):
            is_bonus_month = (m % 6 == 0) and bonus_toggle_ui.value
            
            # 1. 毎月の支払い計算
            int_m = (rem_p_monthly * monthly_rate).quantize(Decimal("1"), ROUND_FLOOR)
            if method == "元利均等返済":
                pri_m = (fixed_m_pmt - int_m) if m < total_months else rem_p_monthly
            else: # 元金均等
                pri_m = (P_monthly_total / total_months).quantize(Decimal("1"), ROUND_FLOOR) if m < total_months else rem_p_monthly
            
            pri_m = min(pri_m, rem_p_monthly)
            rem_p_monthly -= pri_m
            
            # 2. ボーナス支払い計算
            pri_b = Decimal("0")
            int_b = Decimal("0")
            if is_bonus_month:
                int_b = (rem_p_bonus * (annual_rate / Decimal("2"))).quantize(Decimal("1"), ROUND_FLOOR)
                if method == "元利均等返済":
                    pri_b = (fixed_b_pmt - int_b) if m < total_months else rem_p_bonus
                else: # 元金均等
                    pri_b = (P_bonus_total / (int(years_ui.value) * 2)).quantize(Decimal("1"), ROUND_FLOOR) if m < total_months else rem_p_bonus
                
                pri_b = min(pri_b, rem_p_bonus)
                rem_p_bonus -= pri_b

            pay_total = pri_m + int_m + pri_b + int_b
            cum_interest += (int_m + int_b)
            
            schedule.append({
                "月": m,
                "経過年": (m-1)//12 + 1,
                "支払額": int(pay_total),
                "元金充当": int(pri_m + pri_b),
                "利息分": int(int_m + int_b),
                "ローン残高": int(rem_p_monthly + rem_p_bonus),
                "区分": "通常+ボーナス" if is_bonus_month else "通常"
            })

        return schedule, int(P_total + cum_interest), int(cum_interest)

    sim_schedule, sim_total_pay, sim_total_int = calculate()
    return calculate, sim_schedule, sim_total_int, sim_total_pay


@app.cell
def _(bonus_toggle_ui, mo, sim_schedule, sim_total_int, sim_total_pay):
    # ---------------------------------------------------------
    # 結果表示 (KPIカード)
    # ---------------------------------------------------------
    def fmt(v):
        return f"{int(v):,}"

    m_pay = sim_schedule[0]["支払額"]
    
    # 毎月の返済額カード
    card_monthly = mo.Html(f"""
        <div class="metric-card" style="border-left-color: #10b981;">
            <div class="metric-title">毎月の返済額 (目安)</div>
            <div class="metric-value">{fmt(m_pay)}<span class="metric-unit">円</span></div>
            <div class="metric-title" style="margin-top:8px;">初回支払額: {fmt(m_pay)} 円</div>
        </div>
    """)

    # 総支払額カード
    card_total = mo.Html(f"""
        <div class="metric-card" style="border-left-color: #3b82f6;">
            <div class="metric-title">総支払額</div>
            <div class="metric-value">{fmt(sim_total_pay)}<span class="metric-unit">円</span></div>
            <div class="metric-title" style="margin-top:8px;">利息合計: {fmt(sim_total_int)} 円</div>
        </div>
    """)

    # ボーナス加算カード (条件付き)
    card_bonus = None
    if bonus_toggle_ui.value and len(sim_schedule) >= 6:
        b_extra = sim_schedule[5]["支払額"] - sim_schedule[4]["支払額"]
        card_bonus = mo.Html(f"""
            <div class="metric-card" style="border-left-color: #f59e0b;">
                <div class="metric-title">ボーナス月 加算額</div>
                <div class="metric-value">{fmt(b_extra)}<span class="metric-unit">円</span></div>
                <div class="metric-title" style="margin-top:8px;">年2回 (6ヶ月毎)</div>
            </div>
        """)

    mo.flex([card_monthly, card_bonus, card_total] if card_bonus else [card_monthly, card_total], 
            wrap=True, gap=1, justify="start")
    
    return b_extra, card_bonus, card_monthly, card_total, fmt, m_pay


@app.cell
def _(alt, mo, pd, sim_schedule):
    # ---------------------------------------------------------
    # グラフとテーブル (レスポンシブ対応)
    # ---------------------------------------------------------
    df = pd.DataFrame(sim_schedule)
    df_yearly = df[df['月'] % 12 == 0].copy()
    
    # Altairチャートの定義 (width="container" で親要素に追従)
    chart = (
        alt.Chart(df_yearly)
        .mark_area(
            line={'color':'#3b82f6'},
            color=alt.Gradient(
                gradient='linear',
                stops=[alt.GradientStop(color='#3b82f6', offset=0),
                       alt.GradientStop(color='rgba(59, 130, 246, 0.1)', offset=1)],
                x1=1, x2=1, y1=1, y2=0
            )
        )
        .encode(
            x=alt.X("経過年:Q", title="経過年数"),
            y=alt.Y("ローン残高:Q", title="ローン残高 (円)"),
            tooltip=[alt.Tooltip("経過年", title="年"), alt.Tooltip("ローン残高", title="残高", format=",")]
        )
        .properties(height=320, width="container")
    )

    # UIの組み立て
    mo.vstack([
        mo.md("### 📉 返済推移グラフ"),
        mo.Html('<div class="scrollable-wrapper">').append(chart).append('</div>'),
        
        mo.md("### 📅 返済予定表 (最初の2年分)"),
        mo.Html('<div class="scrollable-wrapper">').append(mo.ui.table(df.head(24), pagination=False)).append('</div>'),
        
        mo.md("--- \n <p style='font-size: 0.8rem; color: #94a3b8;'>※ 本シミュレーションは概算です。実際の返済額は金融機関により端数処理が異なる場合があります。</p>")
    ])
    return chart, df, df_yearly


if __name__ == "__main__":
    app.run()