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

    # 精度設定
    decimal.getcontext().prec = 50
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
    # CSS注入: UI/UXの美観とスマホ対応
    mo.md(
        """
        <style>
        .marimo { max-width: 1200px !important; margin: 0 auto; }
        .input-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .flex-container {
            display: flex;
            flex-wrap: wrap;
            gap: 16px;
            width: 100%;
        }
        .flex-item {
            flex: 1 1 300px;
            min-width: 280px;
        }
        .metric-grid {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            margin: 20px 0;
        }
        .metric-card {
            flex: 1 1 calc(33.333% - 12px);
            min-width: 280px;
            padding: 20px;
            border-radius: 12px;
            background: #f8fafc;
            border-left: 6px solid #3b82f6;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        .metric-title { font-size: 0.85rem; color: #64748b; font-weight: 600; }
        .metric-value { font-size: 1.6rem; color: #1e293b; font-weight: 800; margin: 4px 0; }
        .metric-unit { font-size: 0.9rem; color: #94a3b8; }
        .scrollable-container {
            width: 100%;
            overflow-x: auto;
            border-radius: 8px;
            border: 1px solid #e2e8f0;
            background: white;
            padding: 10px;
        }
        </style>
        """
    )
    return


@app.cell
def _(mo):
    # ---------------------------------------------------------
    # UI Components (Input Section)
    # ---------------------------------------------------------
    loan_amount_ui = mo.ui.number(
        label="借入金額 (万円)", start=100, stop=30000, step=10, value=3500, full_width=True
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
            "annuity": "元利均等返済 (毎月一定額)",
            "linear": "元金均等返済 (元金を一定額)"
        },
        value="annuity",
        full_width=True
    )
    bonus_toggle_ui = mo.ui.switch(label="ボーナス払いを利用する", value=False)
    
    return bonus_toggle_ui, interest_rate_ui, loan_amount_ui, method_ui, years_ui


@app.cell
def _(bonus_toggle_ui, loan_amount_ui, mo):
    # ボーナス設定の動的表示
    _max_bonus = int(loan_amount_ui.value * 0.5)
    bonus_amount_ui = mo.ui.number(
        label="ボーナス払い元金合計 (万円)", 
        start=0, 
        stop=_max_bonus, 
        step=10, 
        value=0,
        full_width=True
    )
    
    bonus_section = mo.vstack([
        mo.md(f"### 🎁 ボーナス設定 (最大借入額の50%: {_max_bonus}万円)"),
        bonus_amount_ui
    ]) if bonus_toggle_ui.value else mo.md("")
    
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
    # メイン画面上部の設定エリア（Sidebarは不使用）
    mo.vstack([
        mo.md("### ⚙️ 基本設定"),
        mo.Html(f"""
        <div class="input-card">
            <div class="flex-container">
                <div class="flex-item">{loan_amount_ui}</div>
                <div class="flex-item">{interest_rate_ui}</div>
                <div class="flex-item">{years_ui}</div>
                <div class="flex-item">{method_ui}</div>
            </div>
            <div style="margin-top: 15px;">{bonus_toggle_ui}</div>
            <div style="margin-top: 10px;">{bonus_section}</div>
        </div>
        """)
    ])
    return


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
    # Core Engine (Calculation Logic)
    # ---------------------------------------------------------
    def run_simulation():
        P_total = Decimal(str(loan_amount_ui.value)) * Decimal("10000")
        annual_rate = Decimal(str(interest_rate_ui.value)) / Decimal("100")
        monthly_rate = annual_rate / Decimal("12")
        total_months = int(years_ui.value) * 12
        method = method_ui.value
        
        P_bonus_total = Decimal(str(bonus_amount_ui.value)) * Decimal("10000") if bonus_toggle_ui.value else Decimal("0")
        P_monthly_total = P_total - P_bonus_total
        
        schedule = []
        cum_principal = Decimal("0")
        cum_interest = Decimal("0")
        
        def get_pmt(principal, rate, n):
            if rate == 0: return principal / n
            return principal * (rate * (1 + rate)**n) / ((1 + rate)**n - 1)

        fixed_m_pmt = get_pmt(P_monthly_total, monthly_rate, total_months).quantize(Decimal("1"), ROUND_HALF_UP)
        # ボーナスは年2回計算
        fixed_b_pmt = get_pmt(P_bonus_total, annual_rate / Decimal("2"), int(years_ui.value) * 2).quantize(Decimal("1"), ROUND_HALF_UP) if bonus_toggle_ui.value else Decimal("0")

        rem_p_monthly = P_monthly_total
        rem_p_bonus = P_bonus_total

        for m in range(1, total_months + 1):
            is_bonus_month = (m % 6 == 0) and bonus_toggle_ui.value
            
            # 通常月次計算
            int_m = (rem_p_monthly * monthly_rate).quantize(Decimal("1"), ROUND_FLOOR)
            if method == "annuity":
                pri_m = (fixed_m_pmt - int_m) if m < total_months else rem_p_monthly
            else:
                pri_m = (P_monthly_total / total_months).quantize(Decimal("1"), ROUND_FLOOR) if m < total_months else rem_p_monthly
            
            # ボーナス計算
            pri_b = Decimal("0")
            int_b = Decimal("0")
            if is_bonus_month:
                int_b = (rem_p_bonus * (annual_rate / Decimal("2"))).quantize(Decimal("1"), ROUND_FLOOR)
                if method == "annuity":
                    pri_b = (fixed_b_pmt - int_b) if m < total_months else rem_p_bonus
                else:
                    pri_b = (P_bonus_total / (int(years_ui.value) * 2)).quantize(Decimal("1"), ROUND_FLOOR) if m < total_months else rem_p_bonus

            pri_m = min(pri_m, rem_p_monthly)
            pri_b = min(pri_b, rem_p_bonus)
            
            rem_p_monthly -= pri_m
            rem_p_bonus -= pri_b
            
            pay_total = pri_m + int_m + pri_b + int_b
            cum_principal += (pri_m + pri_b)
            cum_interest += (int_m + int_b)
            
            schedule.append({
                "month": m,
                "year": (m-1)//12 + 1,
                "payment": int(pay_total),
                "principal": int(pri_m + pri_b),
                "interest": int(int_m + int_b),
                "balance": int(rem_p_monthly + rem_p_bonus),
                "type": "通常+ボーナス" if is_bonus_month else "通常"
            })

        return schedule, int(cum_principal + cum_interest), int(cum_interest)

    sim_schedule, sim_total_pay, sim_total_int = run_simulation()
    return run_simulation, sim_schedule, sim_total_int, sim_total_pay


@app.cell
def _(bonus_toggle_ui, mo, sim_schedule, sim_total_int, sim_total_pay):
    # ---------------------------------------------------------
    # Result Visualization (KPI Cards) - Error Fixed Version
    # ---------------------------------------------------------
    def fmt(v):
        return f"{v:,}"

    m_pay = sim_schedule[0]["payment"]
    
    # ボーナスカードのHTMLを事前に生成（f-string内でのバックスラッシュを回避）
    bonus_card_html = ""
    if bonus_toggle_ui.value and len(sim_schedule) >= 6:
        b_extra = sim_schedule[5]["payment"] - sim_schedule[4]["payment"]
        bonus_card_html = f"""
        <div class="metric-card" style="border-left-color: #f59e0b;">
            <div class="metric-title">ボーナス月 加算額</div>
            <div class="metric-value">{fmt(b_extra)} <span class="metric-unit">円</span></div>
            <div class="metric-title" style="margin-top:8px;">年2回加算</div>
        </div>
        """

    # メインKPIの組み立て
    main_kpis = f"""
    <div class="metric-grid">
        <div class="metric-card" style="border-left-color: #10b981;">
            <div class="metric-title">毎月の返済額 (目安)</div>
            <div class="metric-value">{fmt(m_pay)} <span class="metric-unit">円</span></div>
            <div class="metric-title" style="margin-top:8px;">初回支払額</div>
        </div>
        {bonus_card_html}
        <div class="metric-card" style="border-left-color: #3b82f6;">
            <div class="metric-title">総支払額</div>
            <div class="metric-value">{fmt(sim_total_pay)} <span class="metric-unit">円</span></div>
            <div class="metric-title" style="margin-top:8px;">利息合計: {fmt(sim_total_int)} 円</div>
        </div>
    </div>
    """
    mo.md(main_kpis)
    return bonus_card_html, fmt, m_pay, main_kpis


@app.cell
def _(alt, mo, pd, sim_schedule):
    # ---------------------------------------------------------
    # Charts & Tables
    # ---------------------------------------------------------
    _df = pd.DataFrame(sim_schedule)
    _df_yearly = _df[_df['month'] % 12 == 0].copy()
    
    _chart = (
        alt.Chart(_df_yearly)
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
            x=alt.X("year:Q", title="経過年数"),
            y=alt.Y("balance:Q", title="ローン残高 (円)"),
            tooltip=[alt.Tooltip("year", title="年"), alt.Tooltip("balance", title="残高", format=",")]
        )
        .properties(height=300, width="container")
    )

    _table_html = _df.head(24).to_html(index=False, classes="table", border=0)

    mo.vstack([
        mo.md("### 📉 返済推移シミュレーション"),
        mo.Html(f'<div class="scrollable-container">{mo.ui.altair_chart(_chart)}</div>'),
        mo.md("### 📅 返済予定表 (抜粋: 24ヶ月分)"),
        mo.Html(f'<div class="scrollable-container">{_table_html}</div>'),
        mo.md("--- \n *※ 本シミュレーションは概算です。実際の契約時には金融機関の計算詳細を確認してください。*")
    ])
    return


if __name__ == "__main__":
    app.run()