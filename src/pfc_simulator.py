import marimo

__generated_with = "0.19.0"
app = marimo.App(width="full")

@app.cell
def imports():
    import marimo as mo
    import pandas as pd
    import altair as alt
    import numpy as np
    from decimal import Decimal, ROUND_HALF_UP
    return Decimal, ROUND_HALF_UP, alt, mo, pd, np

@app.cell
def ui_inputs(Decimal, mo):
    def wrap_input(label_text, ui_comp):
        lbl = mo.Html(f"<label style='font-size:0.85em; font-weight:bold; color:#4a5568;'>{label_text}</label>")
        return mo.vstack([lbl, ui_comp])

    # --- Task 1 & 2 & 3 Inputs (Mapping Protocol applied) ---
    _activity_options = {
        "低活動 (1.2)": Decimal("1.2"),
        "軽度 (1.375)": Decimal("1.375"),
        "中等度 (1.55)": Decimal("1.55"),
        "高強度 (1.725)": Decimal("1.725"),
        "超高強度 (1.9)": Decimal("1.9")
    }

    # Specification Update: Expanded goal options (10% increments)
    _goal_options = {
        "極限減量 (-30%)": Decimal("0.7"),
        "強めの減量 (-20%)": Decimal("0.8"),
        "緩やかな減量 (-10%)": Decimal("0.9"),
        "維持 (±0%)": Decimal("1.0"),
        "緩やかな増量 (+10%)": Decimal("1.1"),
        "強めの増量 (+20%)": Decimal("1.2"),
        "積極的増量 (+30%)": Decimal("1.3")
    }

    input_weight = mo.ui.number(start=30.0, stop=200.0, step=0.1, value=70.0)
    input_bfp = mo.ui.number(start=1.0, stop=60.0, step=0.1, value=15.0)
    input_activity = mo.ui.dropdown(options=_activity_options, value="中等度 (1.55)")
    input_goal = mo.ui.dropdown(options=_goal_options, value="維持 (±0%)")

    input_p_ratio = mo.ui.number(start=1.0, stop=4.0, step=0.1, value=2.0)
    input_f_ratio = mo.ui.number(start=10.0, stop=50.0, step=1.0, value=25.0)

    input_eaten_p = mo.ui.number(start=0.0, stop=500.0, step=1.0, value=0.0)
    input_eaten_f = mo.ui.number(start=0.0, stop=500.0, step=1.0, value=0.0)
    input_eaten_c = mo.ui.number(start=0.0, stop=1000.0, step=1.0, value=0.0)

    _meal_count_options = {"3食": 3, "4食": 4, "5食": 5}
    _timing_options = ["朝", "昼", "夜", "オフ（筋トレなし）"]
    
    input_meal_count = mo.ui.dropdown(options=_meal_count_options, value="4食")
    input_timing = mo.ui.dropdown(options=_timing_options, value="夜")

    # Task 4 Inputs
    input_duration = mo.ui.number(start=30, stop=365, step=1, value=90)

    # Unified Sidebar-style Layout
    input_panel = mo.vstack([
        mo.md("### 👤 Profile"),
        wrap_input("体重 (kg)", input_weight),
        wrap_input("体脂肪率 (%)", input_bfp),
        wrap_input("活動レベル", input_activity),
        wrap_input("目的", input_goal),
        mo.md("### 🎯 Macros"),
        wrap_input("目標タンパク質 (g/kg)", input_p_ratio),
        wrap_input("目標脂質割合 (%)", input_f_ratio),
        mo.md("### 🍽️ Tracking"),
        wrap_input("摂取済 P (g)", input_eaten_p),
        wrap_input("摂取済 F (g)", input_eaten_f),
        wrap_input("摂取済 C (g)", input_eaten_c),
        mo.md("### ⚙️ Simulator Settings"),
        wrap_input("食事回数", input_meal_count),
        wrap_input("トレ・タイミング", input_timing),
        wrap_input("予測期間 (日)", input_duration)
    ])

    return (
        input_activity, input_bfp, input_duration, input_eaten_c,
        input_eaten_f, input_eaten_p, input_f_ratio, input_goal,
        input_meal_count, input_p_ratio, input_panel, input_timing,
        input_weight, wrap_input
    )

@app.cell
def logic_and_view(
    Decimal, alt, input_activity, input_bfp, input_duration,
    input_eaten_c, input_eaten_f, input_eaten_p, input_f_ratio,
    input_goal, input_meal_count, input_p_ratio, input_panel,
    input_timing, input_weight, mo, pd, np
):
    # --- Engine Part 1: Static Macro Calculation ---
    _w_init = Decimal(str(input_weight.value))
    _bfp_init = Decimal(str(input_bfp.value))
    _act = input_activity.value
    _goal = input_goal.value

    _lbm_init = _w_init * (Decimal("1") - (_bfp_init / Decimal("100")))
    _bmr_base = Decimal("370") + (Decimal("21.6") * _lbm_init)
    _tdee_init = _bmr_base * _act
    _target_kcal = _tdee_init * _goal

    _target_p = _w_init * Decimal(str(input_p_ratio.value))
    _target_f = (_target_kcal * (Decimal(str(input_f_ratio.value)) / Decimal("100"))) / Decimal("9")
    _target_c = (_target_kcal - (_target_p * Decimal("4") + _target_f * Decimal("9"))) / Decimal("4")

    # --- View Part 1: Reverse Tracking ---
    _e_p, _e_f, _e_c = Decimal(str(input_eaten_p.value)), Decimal(str(input_eaten_f.value)), Decimal(str(input_eaten_c.value))
    _df_rev = pd.DataFrame([
        {"Macro": "Protein", "Type": "1. Eaten", "Amount": float(_e_p)},
        {"Macro": "Protein", "Type": "2. Remaining", "Amount": float(max(0, _target_p - _e_p))},
        {"Macro": "Fat", "Type": "1. Eaten", "Amount": float(_e_f)},
        {"Macro": "Fat", "Type": "2. Remaining", "Amount": float(max(0, _target_f - _e_f))},
        {"Macro": "Carbs", "Type": "1. Eaten", "Amount": float(_e_c)},
        {"Macro": "Carbs", "Type": "2. Remaining", "Amount": float(max(0, _target_c - _e_c))},
    ])
    _chart_rev = alt.Chart(_df_rev).mark_bar().encode(
        y=alt.Y("Macro:N", title=None, sort=["Protein", "Fat", "Carbs"]),
        x=alt.X("Amount:Q", title="Grams (g)"),
        color=alt.Color("Type:N", scale=alt.Scale(range=["#ed8936", "#4299e1"])),
        order=alt.Order("Type:N", sort="ascending")
    ).properties(width="container", height=180)

    # --- Engine Part 2: Meal Partitioning ---
    _n = input_meal_count.value
    _t = input_timing.value
    _p_idx = 0 if _t == "朝" else (1 if _t == "昼" else (2 if _t == "夜" and _n >= 3 else (1 if _t == "夜" else -1)))
    _pre_idx = _p_idx - 1 if _p_idx > 0 else -1

    def _get_meal_stats(i):
        _p = _target_p / Decimal(str(_n))
        _c = (_target_c * Decimal("0.4")) if i == _p_idx else ((_target_c * Decimal("0.6")) / Decimal(str(_n - 1)) if _p_idx != -1 else _target_c / Decimal(str(_n)))
        _is_f_low = (i == _p_idx or i == _pre_idx) and _p_idx != -1
        if _p_idx == -1: _f = _target_f / Decimal(str(_n))
        else:
            if _is_f_low: _f = _target_f * Decimal("0.1")
            else: _f = (_target_f * (Decimal("1.0") - (Decimal("0.1") * (2 if _pre_idx != -1 else 1)))) / Decimal(str(_n - (2 if _pre_idx != -1 else 1)))
        return {"食事": f"第{i+1}食" + (" (トレ後)" if i == _p_idx else ""), "P(g)": float(_p.quantize(Decimal("0.1"))), "F(g)": float(_f.quantize(Decimal("0.1"))), "C(g)": float(_mc := _c.quantize(Decimal("0.1"))), "kcal": float((_p*4 + _f*9 + _c*4).quantize(Decimal("1")))}

    _df_meals = pd.DataFrame([_get_meal_stats(_i) for _i in range(_n)])

    # --- Engine Part 3: Body Projection (Euler Method) ---
    _days = int(input_duration.value)
    _curr_w = float(_w_init)
    _curr_lbm = float(_lbm_init)
    _curr_fm = _curr_w - _curr_lbm
    _target_k = float(_target_kcal)
    
    _proj_data = []
    for _d in range(_days + 1):
        _bfp_current = (_curr_fm / _curr_w) * 100
        _proj_data.append({"Day": _d, "Weight": _curr_w, "LBM": _curr_lbm, "BF%": _bfp_current})
        
        # Forbes ratio calculation: p = C / (C + FM) where C = 10.4
        _forbes_p = 10.4 / (10.4 + _curr_fm)
        _tdee_adapt = float(_tdee_init) - (_curr_w - float(_w_init)) * -25.0
        _gap = _target_k - _tdee_adapt
        
        # Energy density: Fat ~9400 kcal/kg, Lean ~1800 kcal/kg
        _ed_avg = (_forbes_p * 1800) + ((1 - _forbes_p) * 9400)
        _delta_w = _gap / _ed_avg
        
        _curr_w += _delta_w
        _curr_lbm += _delta_w * _forbes_p
        _curr_fm = _curr_w - _curr_lbm

    _df_proj = pd.DataFrame(_proj_data).melt("Day", var_name="Metric", value_name="Value")

    # Specification Update: 3-line visualization with fixed colors
    _chart_proj = alt.Chart(_df_proj).mark_line(interpolate='monotone').encode(
        x=alt.X("Day:Q", title="経過日数"),
        y=alt.Y("Value:Q", title="重量(kg) / 割合(%)", scale=alt.Scale(zero=False)),
        color=alt.Color("Metric:N", scale=alt.Scale(domain=["Weight", "LBM", "BF%"], range=["#e53e3e", "#3182ce", "#38a169"]))
    ).properties(width="container", height=250, title="Body Composition Projection")

    # --- View Composition ---
    pfc_tab = mo.vstack([
        input_panel, mo.md("---"),
        mo.md(f"**BMR:** {_bmr_base.quantize(Decimal('1'))} kcal | **TDEE:** {_tdee_init.quantize(Decimal('1'))} kcal"),
        mo.md(f"### 🎯 Target: {_target_kcal.quantize(Decimal('1'))} kcal"),
        mo.ui.altair_chart(_chart_rev)
    ]).style({"padding": "10px"})

    partition_tab = mo.vstack([
        mo.md("## 🍽️ Optimal Meal Partitioning"),
        mo.ui.table(_df_meals, selection=None),
        mo.md(f"**Verification:** P:{_df_meals['P(g)'].sum():.1f}g, F:{_df_meals['F(g)'].sum():.1f}g, C:{_df_meals['C(g)'].sum():.1f}g")
    ]).style({"padding": "10px"})

    projection_tab = mo.vstack([
        mo.md("## 📈 Body Projection Simulator"),
        mo.md("エネルギーバランスの動的変化と Forbes モデルによる体組成推移の予測です。"),
        mo.ui.altair_chart(_chart_proj),
        mo.md(f"""
        **{_days}日後の予測:**
        - **体重:** {pd.DataFrame(_proj_data)['Weight'].iloc[-1]:.1f} kg
        - **LBM (除脂肪体重):** {pd.DataFrame(_proj_data)['LBM'].iloc[-1]:.1f} kg
        - **予測体脂肪率:** {pd.DataFrame(_proj_data)['BF%'].iloc[-1]:.1f} %
        """)
    ]).style({"padding": "10px"})

    main_ui = mo.vstack([
        mo.md("# 🧬 WASM-PFC Simulator (The Body Projection)"),
        mo.ui.tabs({
            "🎯 Simulator": pfc_tab,
            "🍽️ Partition": partition_tab,
            "📈 Predict": projection_tab
        })
    ])

    return main_ui,

@app.cell
def display_main(main_ui):
    main_ui
    return

if __name__ == "__main__":
    app.run()