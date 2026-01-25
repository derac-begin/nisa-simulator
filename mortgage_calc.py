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

    # 金融計算の精度
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
    # 下換性重視のCSS
    mo.md(
        """
        <style>
        .marimo { max-width: 1000px !important; margin: 0 auto; }
        .input-card-box {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .flex-row {
            display: flex;
            flex-wrap: wrap;
            gap: 16px;
            width: 100%;
        }
        .flex-item {
            flex: 1 1 200px;
            min-width: 200px;
        }
        .metric-container {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            margin: 20px 0;
        }
        .metric-card {
            flex: 1 1 280px;
            padding: 16px;
            border-radius: 12px;
            background: #f8fafc;
            border-left: 6px solid #3b82f6;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        }
        .metric-title { font-size: 0.85rem; color: #64748b; font-weight: 600; }
        .metric-value { font-size: 1.5rem; color: #1e293b; font-weight: 800; margin: 4px 0; }
        .metric-unit { font-size: 0.9rem; color: #94a3b8; margin-left: 4px; }
        .scrollable-wrapper {
            width: 100%;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
        }
        </style>
        """
    )
    return


@app.cell
def _(mo):
    # UI Components
    loan_amount_ui = mo.ui.number(label="借入金額 (万円)", start=100, stop=50000, value=3500, full_width=True)
    interest_rate_ui = mo.ui.number(label="年利 (%)", start=0.0, stop=20.0, step=0.001, value=0.525, full_width=True)
    years_ui = mo.ui.slider(label="返済期間 (年)", start=1, stop=50, value=35, full_width=True)
    method_ui = mo.ui.dropdown(
        label="返済方式",
        options={"元利均等返済": "元利均等返済", "元金均等返済": "元金均等返済"},
        value="元利均等返済",
        full_width=True
    )
    bonus_toggle_ui = mo.ui.switch(label="ボーナス払いを利用する", value=False)
    return bonus_toggle_ui, interest_rate_ui, loan_amount_ui, method_ui, years_ui


@app.cell
def _(bonus_toggle_ui, loan_amount_ui, mo):
    # Bonus Amount UI
    _max_b = int(loan_amount_ui.value * 0.5)
    bonus_amount_ui = mo.ui.number(label="ボーナス払い分 (万円)", start=0, stop=_max_b, step=10, value=0, full_width=True)
    
    bonus_area = mo.vstack([
        mo.md(f"**🎁 ボーナス設定** (上限: {_max_b}万円)"),
        bonus_amount_ui
    ]) if bonus_toggle_ui.value else None
    return bonus_amount_ui, bonus_area


@app.cell
def _(
    bonus_area,
    bonus_toggle_ui,
    interest_rate_ui,
    loan_amount_ui,
    method_ui,
    mo,
    years_ui,
):
    # 入力エリアの構築（古いバージョンでも動くよう、手動でFlexbox divを作成）
    input_ui = mo.vstack([
        mo.md("### ⚙️ ローン設定"),
        mo.Html(f'''
            <div class="input-card-box">
                <div class="flex-row">
                    <div class="flex-item">{loan_amount_ui.cache_id}</div>
                    <div class="flex-item">{interest_rate_ui.cache_id}</div>
                    <div class="flex-item">{years_ui.cache_id}</div>
                    <div class="flex-item">{method_ui.cache_id}</div>
                </div>
                <div style="margin-top: 15px;">{bonus_toggle_ui.cache_id}</div>
            </div>
        ''').batch(
            loan_amount_ui=loan_amount_ui,
            interest_rate_ui=interest_rate_ui,
            years_ui=years_ui,
            method_ui=method_ui,
            bonus_toggle_ui=bonus_toggle_ui
        ),
        bonus_area if bonus_area else mo.md("")
    ])
    input_ui
    return (input_ui,)


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
    # 計算ロジック
    def calc_loan():
        P_all = Decimal(str(loan_amount_ui.value)) * Decimal("10000")
        rate_y = Decimal(str(interest_rate_ui.value)) / Decimal("100")
        rate_m = rate_y / Decimal("12")
        months = int(years_ui.value) * 12
        
        P_bonus = Decimal(str(bonus_amount_ui.value)) * Decimal("10000") if bonus_toggle_ui.value else Decimal("0")
        P_normal = P_all - P_bonus
        
        def get_pmt(p, r, n):
            if r == 0: return p / n
            return p * (r * (1 + r)**n) / ((1 + r)**n - 1)

        m_pmt_fixed = get_pmt(P_normal, rate_m, months).quantize(Decimal("1"), ROUND_HALF_UP)
        b_pmt_fixed = get_pmt(P_bonus, rate_y / 2, int(years_ui.value) * 2).quantize(Decimal("1"), ROUND_HALF_UP) if bonus_toggle_ui.value else 0

        res = []
        rem_n = P_normal
        rem_b = P_bonus
        total_int = Decimal("0")

        for i in range(1, months + 1):
            is_b = (i % 6 == 0) and bonus_toggle_ui.value
            
            # Normal
            i_n = (rem_n * rate_m).quantize(Decimal("1"), ROUND_FLOOR)
            if method_ui.value == "元利均等返済":
                p_n = (m_pmt_fixed - i_n) if i < months else rem_n
            else:
                p_n = (P_normal / months).quantize(Decimal("1"), ROUND_FLOOR) if i < months else rem_n
            p_n = min(p_n, rem_n)
            rem_n -= p_n
            
            # Bonus
            p_b, i_b = Decimal("0"), Decimal("0")
            if is_b:
                i_b = (rem_b * (rate_y / 2)).quantize(Decimal("1"), ROUND_FLOOR)
                if method_ui.value == "元利均等返済":
                    p_b = (b_pmt_fixed - i_b) if i < months else rem_b
                else:
                    p_b = (P_bonus / (int(years_ui.value) * 2)).quantize(Decimal("1"), ROUND_FLOOR) if i < months else rem_b
                p_b = min(p_b, rem_b)
                rem_b -= p_b
            
            total_int += (i_n + i_b)
            res.append({
                "月": i,
                "年": (i-1)//12 + 1,
                "支払額": int(p_n + i_n + p_b + i_b),
                "残高": int(rem_n + rem_b),
                "利息": int(i_n + i_b)
            })
        return res, int(P_all + total_int), int(total_int)

    data, t_pay, t_int = calc_loan()
    return data, t_int, t_pay


@app.cell
def _(bonus_toggle_ui, data, mo, t_int, t_pay):
    # KPI表示（AttributeErrorを避けるため、静的HTMLとして構築）
    m_val = data[0]["支払額"]
    b_val = (data[5]["支払額"] - data[4]["支払額"]) if (len(data) >= 6 and bonus_toggle_ui.value) else 0

    def card(title, val, sub, color):
        return f'''
        <div class="metric-card" style="border-left-color: {color};">
            <div class="metric-title">{title}</div>
            <div class="metric-value">{val:,}<span class="metric-unit">円</span></div>
            <div class="metric-title" style="margin-top:8px;">{sub}</div>
        </div>
        '''

    cards_html = f'''
    <div class="metric-container">
        {card("毎月の返済額", m_val, f"初回支払: {m_val:,}円", "#10b981")}
        {card("ボーナス時加算", b_val, "年2回加算", "#f59e0b") if bonus_toggle_ui.value else ""}
        {card("総支払額", t_pay, f"利息合計: {t_int:,}円", "#3b82f6")}
    </div>
    '''
    mo.Html(cards_html)
    return b_val, card, cards_html, m_val


@app.cell
def _(alt, data, mo, pd):
    # グラフとテーブル
    df = pd.DataFrame(data)
    df_y = df[df['月'] % 12 == 0].copy()
    
    _chart = alt.Chart(df_y).mark_area(
        line={'color':'#3b82f6'},
        color=alt.Gradient(
            gradient='linear',
            stops=[alt.GradientStop(color='#3b82f6', offset=0), alt.GradientStop(color='white', offset=1)],
            x1=1, x2=1, y1=1, y2=0
        )
    ).encode(
        x=alt.X("年:Q", title="経過年数"),
        y=alt.Y("残高:Q", title="残高 (円)"),
        tooltip=["年", "残高"]
    ).properties(height=300, width="container")

    mo.vstack([
        mo.md("### 📉 残高推移"),
        mo.Html('<div class="scrollable-wrapper">').append(_chart).append('</div>'),
        mo.md("### 📅 返済予定表 (抜粋)"),
        mo.Html('<div class="scrollable-wrapper">').append(mo.ui.table(df.head(24))).append('</div>')
    ])
    return df, df_y


if __name__ == "__main__":
    app.run()