import marimo

__generated_with = "0.19.0"
app = marimo.App(width="full")

@app.cell
def _():
    import marimo as mo
    import numpy as np
    import pandas as pd # AltairのためにPandasが必要
    import altair as alt # Matplotlibの代わりにAltairを使用
    import math
    from decimal import Decimal, ROUND_HALF_UP
    
    # 以前の plt (Matplotlib) は削除
    return Decimal, ROUND_HALF_UP, alt, math, mo, np, pd

@app.cell
def _(mo):
    # --- Sidebar: Global Settings ---
    tax_rate_input = mo.ui.number(
        value=10, 
        label="消費税率 (%)", 
        step=1, 
        full_width=True
    )
    
    fee_rate_input = mo.ui.slider(
        start=0, 
        stop=10, 
        value=3.24, 
        label="決済手数料 (%)", 
        step=0.01, 
        full_width=True
    )

    sidebar = mo.sidebar(
        mo.vstack([
            mo.md("## ⚙️ アプリ共通設定"),
            mo.md("店舗の基礎数値を入力してください。"),
            tax_rate_input,
            fee_rate_input,
            mo.md("---"),
            mo.md("**Margin Architect v3.0**"),
            mo.md("Powered by Altair (No-Tofu)")
        ])
    )
    return fee_rate_input, sidebar, tax_rate_input

@app.cell
def _(mo):
    # --- Tab 1: Input UI ---
    t1_p_curr = mo.ui.number(value=1000, label="現在の客単価 (税込)", step=10, full_width=True)
    t1_v_curr = mo.ui.number(value=1000, label="現在の月間客数 (人)", step=10, full_width=True)
    t1_r_cost = mo.ui.slider(start=10, stop=90, value=30, label="原価率 (%)", step=0.5, full_width=True)
    t1_p_up = mo.ui.slider(start=0, stop=500, value=50, label="値上げ額 (税込 +円)", step=10, full_width=True)

    return t1_p_curr, t1_p_up, t1_r_cost, t1_v_curr

@app.cell
def _(
    Decimal,
    alt,
    fee_rate_input,
    mo,
    np,
    pd,
    t1_p_curr,
    t1_p_up,
    t1_r_cost,
    t1_v_curr,
    tax_rate_input,
):
    # --- Tab 1: Logic & Visualization (Altair Ver.) ---
    
    # 2. Logic (計算ロジックは変更なし)
    def calculate_churn_limit(p_curr_inc, p_up_inc, v_curr, r_cost_percent, tax_rate_percent, fee_rate_percent):
        p_curr = Decimal(str(max(0, p_curr_inc)))
        p_up = Decimal(str(max(0, p_up_inc)))
        r_cost = Decimal(str(max(0, r_cost_percent))) / Decimal('100')
        tax_rate = Decimal(str(max(0, tax_rate_percent))) / Decimal('100')
        fee_rate = Decimal(str(max(0, fee_rate_percent))) / Decimal('100')

        tax_mult = Decimal('1') + tax_rate
        p_net_curr = p_curr / tax_mult
        p_net_new = (p_curr + p_up) / tax_mult
        
        margin_curr = p_net_curr - (p_net_curr * r_cost) - (p_curr * fee_rate)
        margin_new = p_net_new - (p_net_curr * r_cost) - ((p_curr + p_up) * fee_rate)

        if margin_new <= Decimal('0'):
            return float(0), float(margin_curr), float(margin_new)
        
        x = Decimal('1') - (margin_curr / margin_new)
        x_safe = max(Decimal('0'), x)
        return float(x_safe), float(margin_curr), float(margin_new)

    # Calculation Execution
    with mo.status.spinner("利益防衛ラインを計算中..."):
        churn_limit, m_curr, m_new = calculate_churn_limit(
            t1_p_curr.value, 
            t1_p_up.value, 
            t1_v_curr.value, 
            t1_r_cost.value, 
            tax_rate_input.value, 
            fee_rate_input.value
        )

        # 3. Visualization (Altair: Browser-Native Rendering)
        # Matplotlibを捨て、データフレームを作成してAltairで描画する
        
        v_curr_val = float(max(0, t1_v_curr.value))
        
        # データ作成: 0%〜30%の客離れ率ごとの利益推移
        x_vals = np.linspace(0, 0.30, 100)
        profit_curr_vals = [float(m_curr * v_curr_val)] * len(x_vals)
        profit_new_vals = [float(m_new * v_curr_val * (1 - x)) for x in x_vals]
        
        # DataFrame化
        df_chart = pd.DataFrame({
            'churn_rate': x_vals,
            'current_profit': profit_curr_vals,
            'new_profit': profit_new_vals
        })
        
        # Base Chart
        base = alt.Chart(df_chart).encode(
            x=alt.X('churn_rate', axis=alt.Axis(format='%', title='客離れ率')),
        )
        
        # Line 1: 現在の利益 (点線)
        line_curr = base.mark_line(strokeDash=[5, 5], color='gray').encode(
            y=alt.Y('current_profit', title='営業利益 (円)'),
            tooltip=[alt.Tooltip('current_profit', format=',.0f', title='現在の利益')]
        )
        
        # Line 2: 新しい利益 (実線・青)
        line_new = base.mark_line(color='blue').encode(
            y='new_profit',
            tooltip=[alt.Tooltip('churn_rate', format='.1%', title='客離れ率'), 
                     alt.Tooltip('new_profit', format=',.0f', title='新利益')]
        )
        
        # Area: 利益が増えるゾーン (Green)
        # Altairで fill_between を表現するのは少し工夫がいるが、今回はシンプルに
        # 「新利益」のラインの下を薄く塗る表現にする（交差塗り分けは複雑なため）
        area_new = base.mark_area(opacity=0.1, color='blue').encode(
            y='new_profit'
        )
        
        # Rule: 損益分岐点 (赤線)
        rule = alt.Chart(pd.DataFrame({'x': [churn_limit]})).mark_rule(color='red', strokeDash=[2,2]).encode(
            x='x'
        )
        
        # Text: 分岐点のラベル
        text = alt.Chart(pd.DataFrame({'x': [churn_limit], 'y': [float(m_curr * v_curr_val)], 'label': [f'分岐点: {churn_limit:.1%}']})).mark_text(
            align='left', dx=5, dy=-10, color='red'
        ).encode(
            x='x', y='y', text='label'
        )

        # Combine
        final_chart = (area_new + line_curr + line_new + rule + text).properties(
            title="利益の防衛ライン分析",
            width="container",
            height=300
        )
        
        chart_output = mo.ui.altair_chart(final_chart)

    # Layout
    tab1_content = mo.vstack([
        mo.md("### 🟢 値上げシミュレーター"),
        mo.md("値上げをしても「利益総額」が減らない客離れの限界ラインを算出します。"),
        mo.hstack([
            mo.vstack([t1_p_curr, t1_v_curr]),
            mo.vstack([t1_r_cost, t1_p_up])
        ], gap=2, wrap=True),
        mo.md("---"),
        mo.hstack([
            mo.stat(
                label="現在の一人当たり利益",
                value=f"{int(m_curr)}円",
                caption="税抜・手数料引後"
            ),
             mo.stat(
                label="値上げ後の一人当たり利益",
                value=f"{int(m_new)}円",
                caption=f"+{int(m_new - m_curr)}円 UP"
            ),
             mo.stat(
                label="許容できる客離れ率",
                value=f"{churn_limit * 100:.1f}%",
                caption="これ以上減ると赤字"
            ),
        ], gap=2, wrap=True, justify="center"),
        chart_output
    ])
    return (
        calculate_churn_limit,
        chart_output,
        churn_limit,
        m_curr,
        m_new,
        tab1_content,
        v_curr_val,
    )

@app.cell
def _(mo):
    # --- Tab 2: Input UI ---
    t2_cost_amount = mo.ui.number(value=300, label="原価額 (円)", step=10, full_width=True)
    t2_target_rate = mo.ui.slider(start=10, stop=90, value=30, label="目標原価率 (%)", step=1, full_width=True)
    return t2_cost_amount, t2_target_rate

@app.cell
def _(Decimal, ROUND_HALF_UP, fee_rate_input, mo, t2_cost_amount, t2_target_rate, tax_rate_input):
    # --- Tab 2: Logic ---
    def calculate_target_price(cost, target_rate_percent, tax_rate_percent):
        c = Decimal(str(max(0, cost)))
        t_rate = Decimal(str(max(0, target_rate_percent))) / Decimal('100')
        tax_pct = Decimal(str(max(0, tax_rate_percent))) / Decimal('100')

        if t_rate <= Decimal('0'): 
            return 0
        
        tax_mult = Decimal('1') + tax_pct
        
        net_price = c / t_rate
        gross_price = net_price * tax_mult
        
        return int(gross_price.quantize(Decimal('1'), rounding=ROUND_HALF_UP))

    with mo.status.spinner("適正価格をシミュレーション中..."):
        calc_price = calculate_target_price(t2_cost_amount.value, t2_target_rate.value, tax_rate_input.value)
        p_matsu = calculate_target_price(t2_cost_amount.value, 25, tax_rate_input.value)
        p_take = calculate_target_price(t2_cost_amount.value, 30, tax_rate_input.value)
        p_ume = calculate_target_price(t2_cost_amount.value, 35, tax_rate_input.value)

    tab2_content = mo.vstack([
        mo.md("### 🔵 適正価格メーカー"),
        mo.md("原価額から、目標原価率を達成するための「税込売価」を逆算します。"),
        mo.hstack([t2_cost_amount, t2_target_rate], gap=2, wrap=True),
        mo.md("#### 🎯 推奨設定価格 (税込)"),
        mo.callout(
            mo.md(f"# {calc_price:,} 円"),
            kind="info"
        ),
        mo.md("#### 📊 原価率別パターン (松・竹・梅)"),
        mo.hstack([
            mo.stat(label="松 (原価25%)", value=f"{p_matsu:,}円", caption="高付加価値"),
            mo.stat(label="竹 (原価30%)", value=f"{p_take:,}円", caption="バランス"),
            mo.stat(label="梅 (原価35%)", value=f"{p_ume:,}円", caption="集客重視"),
        ], gap=1, wrap=True, justify="center")
    ])
    return (
        calc_price,
        calculate_target_price,
        p_matsu,
        p_take,
        p_ume,
        tab2_content,
    )

@app.cell
def _(mo):
    # --- Tab 3: Input UI ---
    t3_fixed_cost = mo.ui.number(value=500000, label="月間固定費 (円)", step=10000, full_width=True)
    t3_days = mo.ui.slider(start=1, stop=31, value=25, label="月間営業日数 (日)", step=1, full_width=True)
    t3_avg_spend = mo.ui.number(value=1200, label="平均客単価 (税込)", step=10, full_width=True)
    t3_avg_cost_rate = mo.ui.slider(start=10, stop=90, value=32, label="平均原価率 (%)", step=0.5, full_width=True)
    return t3_avg_cost_rate, t3_avg_spend, t3_days, t3_fixed_cost

@app.cell
def _(Decimal, ROUND_HALF_UP, fee_rate_input, mo, t3_avg_cost_rate, t3_avg_spend, t3_days, t3_fixed_cost, tab1_content, tab2_content, tax_rate_input):
    # --- Tab 3: Logic ---
    def calculate_daily_bep(fixed_cost, days, avg_spend, avg_cost_rate_pct, fee_rate_pct):
        fc = Decimal(str(max(0, fixed_cost)))
        d = Decimal(str(max(1, days)))
        spend = Decimal(str(max(0, avg_spend)))
        r_cost = Decimal(str(max(0, avg_cost_rate_pct))) / Decimal('100')
        r_fee = Decimal(str(max(0, fee_rate_pct))) / Decimal('100')
        
        denom = Decimal('1') - r_cost - r_fee
        if denom <= Decimal('0'): 
            return 0, 0, 0

        req_sales_month = fc / denom
        daily_target_sales = req_sales_month / d
        
        if spend <= Decimal('0'):
            daily_target_customers = Decimal('0')
        else:
            daily_target_customers = daily_target_sales / spend
            
        return (
            int(req_sales_month.quantize(Decimal('1'), rounding=ROUND_HALF_UP)),
            int(daily_target_sales.quantize(Decimal('1'), rounding=ROUND_HALF_UP)),
            int(daily_target_customers.quantize(Decimal('1'), rounding=ROUND_HALF_UP))
        )

    with mo.status.spinner("リアルタイム損益分岐点を計算中..."):
        req_month, daily_sales, daily_customers = calculate_daily_bep(
            t3_fixed_cost.value,
            t3_days.value,
            t3_avg_spend.value,
            t3_avg_cost_rate.value,
            fee_rate_input.value
        )

    tab3_content = mo.vstack([
        mo.md("### 🟠 リアルタイム損益分岐点"),
        mo.md("固定費を回収するために、今日一日で最低限必要な売上と客数を計算します。"),
        mo.hstack([
            mo.vstack([t3_fixed_cost, t3_days]),
            mo.vstack([t3_avg_spend, t3_avg_cost_rate])
        ], gap=2, wrap=True),
        mo.md("---"),
        mo.md("#### 📅 今日の目標ライン"),
        mo.hstack([
            mo.stat(
                label="目標来店客数",
                value=f"{daily_customers:,} 人",
                caption="Today's Target"
            ),
            mo.stat(
                label="目標日販 (税込)",
                value=f"¥ {daily_sales:,}",
                caption="Minimum Sales"
            )
        ], gap=2, wrap=True, justify="center"),
        mo.callout(
            mo.md(f"※月間必要損益分岐点売上: ¥ {req_month:,}"),
            kind="neutral"
        )
    ])

    main_tabs = mo.ui.tabs({
        "📈 値上げ": tab1_content,
        "🏷️ 値付け": tab2_content,
        "⚖️ 分岐点": tab3_content
    })
    
    return (
        calculate_daily_bep,
        daily_customers,
        daily_sales,
        main_tabs,
        req_month,
        tab3_content,
    )

@app.cell
def _(main_tabs, sidebar):
    sidebar 
    main_tabs
    return

if __name__ == "__main__":
    app.run()