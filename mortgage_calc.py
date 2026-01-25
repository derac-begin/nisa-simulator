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

    # 金融計算の精度設定
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
    # 全バージョン共通で動作するCSS
    mo.md(
        """
        <style>
        .marimo { max-width: 900px !important; margin: 0 auto; }
        /* 入力エリアをカード風にする */
        .input-section {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 20px;
        }
        /* KPIカードのレイアウト */
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
        /* スクロール対応 */
        .scroll-container { width: 100%; overflow-x: auto; }
        </style>
        """
    )
    return


@app.cell
def _(mo):
    # UIコンポーネントの定義 (最も標準的な作り)
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
    # ボーナス設定の出し分け
    _limit = int(loan_amount_ui.value * 0.5)
    bonus_amount_ui = mo.ui.number(label="ボーナス分合計 (万円)", start=0, stop=_limit, step=10, value=0, full_width=True)
    
    bonus_box = mo.vstack([
        mo.md(f"**🎁 ボーナス払い設定** (上限:{_limit}万)"),
        bonus_amount_ui
    ]) if bonus_toggle_ui.value else mo.md("")
    return bonus_amount_ui, bonus_box


@app.cell
def _(
    bonus_box,
    bonus_toggle_ui,
    interest_rate_ui,
    loan_amount_ui,
    method_ui,
    mo,
    years_ui,
):
    # 【最重要】設定エリアの表示
    # エラーの元になる .batch() や .flex() を排除し、最も安全な vstack で構築
    mo.vstack([
        mo.md("### ⚙️ ローン設定"),
        mo.vstack([
            loan_amount_ui,
            interest_rate_ui,
            years_ui,
            method_ui,
            bonus_toggle_ui,
            bonus_box
        ], gap=1)
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
    # 計算エンジン
    def run_calc():
        P_all = Decimal(str(loan_amount_ui.value)) * Decimal("10000")
        r_y = Decimal(str(interest_rate_ui.value)) / Decimal("100")
        r_m = r_y / Decimal("12")
        total_m = int(years_ui.value) * 12
        
        P_b = Decimal(str(bonus_amount_ui.value)) * Decimal("10000") if bonus_toggle_ui.value else Decimal("0")
        P_n = P_all - P_b
        
        def get_pmt(p, r, n):
            if r == 0: return p / n
            return p * (r * (1 + r)**n) / ((1 + r)**n - 1)

        m_fixed = get_pmt(P_n, r_m, total_m).quantize(Decimal("1"), ROUND_HALF_UP)
        b_fixed = get_pmt(P_b, r_y / 2, int(years_ui.value) * 2).quantize(Decimal("1"), ROUND_HALF_UP) if bonus_toggle_ui.value else 0

        schedule = []
        rem_n, rem_b = P_n, P_b
        total_int = Decimal("0")

        for i in range(1, total_m + 1):
            is_b_month = (i % 6 == 0) and bonus_toggle_ui.value
            
            # 通常分
            i_n = (rem_n * r_m).quantize(Decimal("1"), ROUND_FLOOR)
            if method_ui.value == "元利均等返済":
                p_n = (m_fixed - i_n) if i < total_m else rem_n
            else:
                p_n = (P_n / total_m).quantize(Decimal("1"), ROUND_FLOOR) if i < total_m else rem_n
            p_n = min(p_n, rem_n)
            rem_n -= p_n
            
            # ボーナス分
            p_b, i_b = Decimal("0"), Decimal("0")
            if is_b_month:
                i_b = (rem_b * (r_y / 2)).quantize(Decimal("1"), ROUND_FLOOR)
                if method_ui.value == "元利均等返済":
                    p_b = (b_fixed - i_b) if i < total_m else rem_b
                else:
                    p_b = (P_b / (int(years_ui.value) * 2)).quantize(Decimal("1"), ROUND_FLOOR) if i < total_m else rem_b
                p_b = min(p_b, rem_b)
                rem_b -= p_b
            
            total_int += (i_n + i_b)
            schedule.append({
                "月": i,
                "年": (i-1)//12 + 1,
                "支払額": int(p_n + i_n + p_b + i_b),
                "残高": int(rem_n + rem_b),
                "利息": int(i_n + i_b)
            })
        return schedule, int(P_all + total_int), int(total_int)

    sim_data, total_pay, total_int_val = run_calc()
    return run_calc, sim_data, total_int_val, total_pay


@app.cell
def _(bonus_toggle_ui, mo, sim_data, total_int_val, total_pay):
    # KPI表示 (画像で成功が確認できている手法を採用)
    m_pay = sim_data[0]["支払額"]
    b_add = (sim_data[5]["支払額"] - sim_data[4]["支払額"]) if (len(sim_data) >= 6 and bonus_toggle_ui.value) else 0

    def make_card(title, val, info, color):
        return f'''
        <div class="metric-card" style="border-left-color: {color};">
            <div class="metric-title">{title}</div>
            <div class="metric-value">{int(val):,}<span class="metric-unit">円</span></div>
            <div class="metric-title" style="margin-top:8px;">{info}</div>
        </div>
        '''

    html_content = f'''
    <div class="metric-container">
        {make_card("毎月の返済額", m_pay, f"初回返済額: {m_pay:,}円", "#10b981")}
        {make_card("ボーナス加算額", b_add, "年2回(6ヶ月毎)", "#f59e0b") if bonus_toggle_ui.value else ""}
        {make_card("総支払額", total_pay, f"利息合計: {total_int_val:,}円", "#3b82f6")}
    </div>
    '''
    mo.Html(html_content)
    return b_add, html_content, m_pay, make_card


@app.cell
def _(alt, mo, pd, sim_data):
    # グラフとテーブル (エラーの元になる .append() を排除)
    _df = pd.DataFrame(sim_data)
    _df_y = _df[_df['月'] % 12 == 0].copy()
    
    # Altairチャート
    _chart = alt.Chart(_df_y).mark_area(
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

    # 全ての要素を単一のリストとして vstack に渡す（最も安全な方法）
    mo.vstack([
        mo.md("### 📉 返済推移グラフ"),
        _chart,
        mo.md("### 📅 返済予定表 (抜粋)"),
        mo.ui.table(_df.head(24))
    ])
    return


if __name__ == "__main__":
    app.run()