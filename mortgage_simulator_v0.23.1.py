import marimo

__generated_with = "0.23.1"
app = marimo.App(width="medium")

@app.cell
def __():
    import marimo as mo
    import pandas as pd
    import altair as alt
    from decimal import Decimal, getcontext
    import math
    return Decimal, alt, getcontext, math, mo, pd


@app.cell
def __(mo):
    # --- Task 1: UI の構築 (The Reactive Ghost Protocol) ---
    _rows_mapping = {
        "plan_a": "プランA",
        "plan_b": "プランB",
        "plan_c": "プランC"
    }

    _initial_values = {
        "plan_a": [3000, 35, 0.5, 0],
        "plan_b": [3000, 35, 0.5, 100],
        "plan_c": [3000, 35, 1.5, 0]
    }

    # 💡 バックエンド: mo.ui.dictionary で状態管理を復活させ、DAG の通信ケーブルを繋ぐ
    scenario_inputs = mo.ui.dictionary({
        _key: mo.ui.dictionary({
            "amount": mo.ui.number(start=100, step=100, value=_vals[0]),
            "years": mo.ui.number(start=1, step=1, value=_vals[1]),
            "rate": mo.ui.number(start=0.1, step=0.1, value=_vals[2]),
            "prepayment": mo.ui.number(start=0, step=10, value=_vals[3])
        })
        for _key, _vals in _initial_values.items()
    })

    # 💡 フロントエンド: dictionary 全体を描画するのではなく、個別の要素を vstack に抽出して縦積み
    _vertical_blocks = []
    for _key, _label in _rows_mapping.items():
        _vertical_blocks.extend([
            mo.md(f"#### {_label}"),
            mo.Html("<small><b>借入額 (万)</b></small>"), scenario_inputs[_key]["amount"],
            mo.Html("<small><b>期間 (年)</b></small>"), scenario_inputs[_key]["years"],
            mo.Html("<small><b>年利 (%)</b></small>"), scenario_inputs[_key]["rate"],
            mo.Html("<small><b>繰上 (万)</b></small>"), scenario_inputs[_key]["prepayment"],
            mo.md("---")
        ])
        
    input_panel = mo.vstack(_vertical_blocks)
    return input_panel, scenario_inputs


@app.cell
def __(input_panel, mo, scenario_inputs):
    # --- Task 2: Validation & Error UI Binding ---
    # mo.ui.dictionary の .value から直接全プランの値を一括取得（リアクティビティの発火点）
    _matrix_val = scenario_inputs.value
    
    _error_msg = None
    valid_scenario_data = None

    if any(v["amount"] is None for v in _matrix_val.values()):
        _error_msg = mo.md("**プランが未入力（空欄）です。<br/>数値を入力してください。**").callout(kind="danger")
    else:
        _is_invalid = any(
            (plan["amount"] is None or plan["amount"] <= 0) or
            (plan["years"] is None or plan["years"] <= 0) or
            (plan["rate"] is None or plan["rate"] <= 0) or
            (plan["prepayment"] is None or plan["prepayment"] < 0)
            for plan in _matrix_val.values()
        )
        if _is_invalid:
            _error_msg = mo.md("**不正な入力値が検出されました。**<br/>金額・期間・年利には<br/>0より大きい数値を入力してください。").callout(kind="danger")
        else:
            valid_scenario_data = _matrix_val

    header_ui = mo.vstack([
        mo.md("# 🏡 Mortgage Simulator v4.0"),
        mo.md("維持費0円・情報漏洩ゼロ。WASM環境で動作する高精度な住宅ローン比較シミュレーター。<br/>設定を変更すると、瞬時にシナリオ別の推移が再計算されます。"),
        mo.md("---"),
        mo.md("### 📊 1. シナリオ設定"),
        input_panel,
        _error_msg if _error_msg else mo.md("")
    ])
    
    return header_ui, valid_scenario_data


@app.cell
def __(header_ui):
    # --- 描画層 1: ヘッダーと入力パネル ---
    header_ui
    return


@app.cell
def __(Decimal, getcontext, math, mo, pd, valid_scenario_data):
    # --- Task 3: Decimal Calculation Engine ---
    if valid_scenario_data is None:
        mo.stop(True)

    getcontext().prec = 28
    _scenario_labels = {"plan_a": "プランA", "plan_b": "プランB", "plan_c": "プランC"}

    def _calculate_scenario(plan_key: str, plan_data: dict) -> pd.DataFrame:
        _amount = Decimal(str(plan_data["amount"])) * Decimal("10000")
        _years = int(plan_data["years"])
        _rate_pct = Decimal(str(plan_data["rate"]))
        _prepayment = Decimal(str(plan_data.get("prepayment", 0))) * Decimal("10000")
        _months = _years * 12
        _label = _scenario_labels.get(plan_key, plan_key)

        if _rate_pct == Decimal("0"):
            _monthly_rate = Decimal("0")
            _monthly_payment = _amount / Decimal(str(_months))
        else:
            _monthly_rate = _rate_pct / Decimal("100") / Decimal("12")
            _factor = (_monthly_rate + Decimal("1")) ** _months
            _monthly_payment = _amount * (_monthly_rate * _factor) / (_factor - Decimal("1"))

        _monthly_payment = _monthly_payment.quantize(Decimal("1"))
        _balance = _amount
        _records = []

        for _m in range(1, _months + 1):
            if _balance <= Decimal("0"): break
            _interest = (_balance * _monthly_rate).quantize(Decimal("1"))
            _principal = _monthly_payment - _interest
            _extra = _prepayment if _m % 12 == 0 else Decimal("0")
            _total_principal_payment = _principal + _extra

            if _balance < _total_principal_payment:
                _total_principal_payment = _balance
                _principal = _balance - _extra if _balance > _extra else _balance
                if _principal < Decimal("0"):
                    _principal = _balance
                    _extra = Decimal("0")

            _balance -= _total_principal_payment

            _records.append({
                "プラン": _label, "Month": _m, "Year": math.ceil(_m / 12),
                "Interest": float(_interest), "Principal": float(_principal),
                "Extra_Payment": float(_extra), "Balance": float(_balance),
                "Total_Payment": float(_interest + _total_principal_payment)
            })
        return pd.DataFrame(_records)

    _all_scenarios_dfs = [_calculate_scenario(_key, _data) for _key, _data in valid_scenario_data.items()]
    df_mortgage_scenarios = pd.concat(_all_scenarios_dfs, ignore_index=True)
    return df_mortgage_scenarios,


@app.cell
def __(alt, df_mortgage_scenarios, math, mo, pd):
    # --- Task 4: Visualization & Assembly ---
    if df_mortgage_scenarios is None or df_mortgage_scenarios.empty:
        mo.stop(True)

    # 1. サマリー表示項目の「極限圧縮」
    _summary_records = [
        {
            "プラン": _scenario,
            "利息(万)": round(df_mortgage_scenarios[df_mortgage_scenarios["プラン"] == _scenario]["Interest"].sum() / 10000, 1),
            "総支払(万)": round(df_mortgage_scenarios[df_mortgage_scenarios["プラン"] == _scenario]["Total_Payment"].sum() / 10000, 1),
            "完済(年)": math.ceil(df_mortgage_scenarios[df_mortgage_scenarios['プラン'] == _scenario]['Month'].max() / 12)
        }
        for _scenario in df_mortgage_scenarios["プラン"].unique()
    ]
    df_summary = pd.DataFrame(_summary_records)
    
    # 💡 The Zero-Index Protocol: mo.ui.table を完全廃止し、index=False で純粋な HTML テーブルを生成
    _table_html = df_summary.to_html(index=False, classes='pure-table', border=0)
    
    # 💡 Fluid HTML レンダリング: 余分なDOMを一切介在させず、CSSで親の幅(100%)に順応させる
    _style = """
    <style>
        .pure-table { width: 100%; border-collapse: collapse; font-size: 0.9em; }
        .pure-table th, .pure-table td { border-bottom: 1px solid #ddd; padding: 8px; text-align: left; }
    </style>
    """
    summary_table = mo.Html(f"{_style}<div style='overflow-x: auto; width: 100%;'>{_table_html}</div>")

    # 2. Altairチャート
    line_chart = alt.Chart(df_mortgage_scenarios).mark_line(size=3).encode(
        x=alt.X("Month:Q", title="経過月数"),
        y=alt.Y("Balance:Q", title="ローン残高 (円)"),
        color=alt.Color("プラン:N", legend=alt.Legend(title="プラン", orient="bottom")),
        tooltip=["プラン", "Year", "Month", "Balance"]
    ).properties(width="container", height=350, title="残高推移")

    bar_chart = alt.Chart(df_summary).mark_bar().encode(
        x=alt.X("総支払(万):Q", title="総支払額 (万円)"),
        y=alt.Y("プラン:N", title=None, sort="-x"),
        color=alt.Color("プラン:N", legend=None),
        tooltip=["プラン", "利息(万)", "総支払(万)"]
    ).properties(width="container", height=150, title="総支払コスト比較")

    charts_ui = mo.vstack([line_chart, bar_chart])

    results_ui = mo.vstack([
        mo.md("### 📝 2. 返済サマリー"),
        summary_table,
        mo.md("---"),
        mo.md("### 📈 3. シミュレーション結果"),
        charts_ui
    ])
    return bar_chart, charts_ui, df_summary, line_chart, results_ui, summary_table


@app.cell
def __(results_ui):
    # --- 描画層 2: サマリーとグラフ ---
    results_ui
    return


if __name__ == "__main__":
    app.run()