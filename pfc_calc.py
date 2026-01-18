import marimo

__generated_with = "0.10.9"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    import altair as alt
    import pandas as pd
    from decimal import Decimal, ROUND_HALF_UP
    import math
    import os
    return Decimal, ROUND_HALF_UP, alt, math, mo, os, pd


@app.cell
def _(mo):
    # CSS注入: スマホ最適化とグラフの横スクロール対応
    mo.md(
        """
        <style>
        .marimo { width: 100% !important; max-width: 100% !important; padding: 1rem; }
        .chart-container { width: 100%; overflow-x: auto; padding-bottom: 20px; }
        .error-box { 
            background-color: #ffebee; color: #c62828; 
            padding: 10px; border-radius: 4px; border: 1px solid #ef9a9a; font-weight: bold; 
        }
        </style>
        """
    )
    return


@app.cell
def _(mo, os):
    # --- ヘッダー表示エリア ---
    # 画像パスを確認し、存在しない場合はテキストのみを表示する安全設計
    image_path = "assets/header_pfc.png"
    
    if os.path.exists(image_path):
        header_img = mo.image(src=image_path, alt="PFC Calculator Header", width="100%", rounded=True)
    else:
        # 画像がない場合のプレースホルダー
        header_img = mo.md(f"_{image_path} が見つかりません_")

    # 【修正1】ここを作成するだけでなく、変数に格納して return します
    header_section = mo.vstack([
        header_img,
        mo.md("# 💪 トレーニー専用 PFCバランス計算機 (Secured)"),
        mo.md("除脂肪体重(LBM)から算出した正確な基礎代謝をもとに、目的に合わせたPFCバランスを提案します。")
    ])
    
    return header_section,


@app.cell
def _(header_section):
    # ここで表示（marimoは最後の式を表示します）
    header_section
    return


@app.cell
def _(mo):
    # --- 入力フォーム ---
    
    # UI定義
    weight = mo.ui.number(label="体重 (kg)", start=30, stop=150, step=0.1, value=65.0, full_width=True)
    body_fat = mo.ui.number(label="体脂肪率 (%)", start=3, stop=50, step=0.1, value=15.0, full_width=True)

    activity_options = {
        "ほぼ運動しない (x1.2)": "1.2",
        "週1-3回の運動 (x1.375)": "1.375",
        "週3-5回の運動 (x1.55)": "1.55",
        "週6-7回の運動 (x1.725)": "1.725",
        "激しい運動/肉体労働 (x1.9)": "1.9"
    }
    activity = mo.ui.dropdown(options=activity_options, value="週1-3回の運動 (x1.375)", label="活動レベル", full_width=True)

    goal_options = {
        "減量 (-500kcal)": "-500",
        "維持 (±0kcal)": "0",
        "増量 (+500kcal)": "500"
    }
    goal = mo.ui.dropdown(options=goal_options, value="減量 (-500kcal)", label="目的", full_width=True)

    protein_ratio = mo.ui.slider(start=1.0, stop=4.0, step=0.1, value=2.5, label="タンパク質 (g/体重kg)", full_width=True)
    fat_pct = mo.ui.slider(start=10, stop=40, step=1, value=20, label="脂質摂取率 (%)", full_width=True)

    # フォームレイアウト
    input_form = mo.accordion({
        "📋 データの入力・調整": mo.vstack([
            mo.md("### 基本パラメーター"),
            weight, body_fat, activity, goal,
            mo.md("---"),
            mo.md("### PFCバランス微調整"),
            protein_ratio, fat_pct
        ])
    })
    
    return (
        activity, activity_options, body_fat, fat_pct, goal, goal_options, 
        input_form, protein_ratio, weight
    )


@app.cell
def _(input_form):
    # フォームの表示
    input_form
    return


@app.cell
def _(
    Decimal, ROUND_HALF_UP, activity, activity_options, body_fat, 
    fat_pct, goal, goal_options, math, mo, protein_ratio, weight
):
    # --- 計算 & バリデーションロジック ---

    # 1. 入力値取得
    w_val = weight.value
    bf_val = body_fat.value
    act_val = activity.value
    goal_val = goal.value
    p_ratio_val = protein_ratio.value
    f_pct_val = fat_pct.value

    # 2. バリデーション (mo.stopを使用)
    # 値がNoneまたは不正な数値の場合、ここで処理を停止しメッセージを表示する
    is_invalid_input = any(x is None for x in [w_val, bf_val, p_ratio_val, f_pct_val])
    mo.stop(is_invalid_input, mo.md('<div class="error-box">⚠️ 数値を入力してください</div>'))

    is_negative = (w_val <= 0 or bf_val < 0)
    mo.stop(is_negative, mo.md('<div class="error-box">⚠️ 体重や体脂肪率は正の値を入力してください</div>'))

    # セキュリティ: 選択肢改ざんチェック
    if act_val not in activity_options.values() or goal_val not in goal_options.values():
        mo.stop(True, mo.md('<div class="error-box">⚠️ 不正なパラメータが検出されました</div>'))

    # 3. 計算実行
    try:
        # Decimal変換
        w_d = Decimal(str(w_val))
        bf_d = Decimal(str(bf_val))
        act_d = Decimal(str(act_val))
        goal_d = Decimal(str(goal_val))
        p_ratio_d = Decimal(str(p_ratio_val))
        f_pct_d = Decimal(str(f_pct_val))

        # 基礎計算 (Katch-McArdle Formula)
        lbm = w_d * (Decimal("1") - (bf_d / Decimal("100")))
        bmr = Decimal("370") + (Decimal("21.6") * lbm)
        tdee = bmr * act_d
        target_cal = tdee + goal_d

        # PFC計算
        p_g = w_d * p_ratio_d
        p_cal = p_g * Decimal("4")
        
        f_cal = target_cal * (f_pct_d / Decimal("100"))
        f_g = f_cal / Decimal("9")
        
        c_cal = target_cal - p_cal - f_cal
        if c_cal < 0: c_cal = Decimal("0")
        c_g = c_cal / Decimal("4")

        results = {
            "LBM": lbm, "BMR": bmr, "TDEE": tdee, "Target": target_cal,
            "P_g": p_g, "P_cal": p_cal, "F_g": f_g, "F_cal": f_cal, "C_g": c_g, "C_cal": c_cal
        }
        
    except Exception as e:
        # 計算エラー時は停止
        mo.stop(True, mo.md(f'<div class="error-box">⚠️ 計算エラー: {str(e)}</div>'))
        results = None

    return results,


@app.cell
def _(alt, mo, pd, results):
    # --- 結果表示 & グラフ描画 ---
    
    # mo.stopを使っているので、ここに来る時点で results は正常値であることが保証されます
    
    def fmt(d):
        return f"{int(d.to_integral_value())}"

    # 1. サマリー表示
    summary_section = mo.vstack([
        mo.md("## 📊 診断結果"),
        mo.stat(
            value=f"{fmt(results['Target'])} kcal",
            label="1日の目標摂取カロリー",
            caption=f"基礎代謝: {fmt(results['BMR'])} / 消費カロリー: {fmt(results['TDEE'])}"
        ),
        mo.md("---")
    ])

    # 2. グラフデータ作成
    df = pd.DataFrame([
        {"Nutrient": "タンパク質 (P)", "Calories": float(results['P_cal']), "Grams": float(results['P_g']), "Color": "#4c78a8"},
        {"Nutrient": "脂質 (F)", "Calories": float(results['F_cal']), "Grams": float(results['F_g']), "Color": "#e45756"},
        {"Nutrient": "炭水化物 (C)", "Calories": float(results['C_cal']), "Grams": float(results['C_g']), "Color": "#f58518"}
    ])

    # 3. ドーナツチャート作成
    base = alt.Chart(df).encode(theta=alt.Theta("Calories", stack=True))
    
    pie = base.mark_arc(outerRadius=120, innerRadius=80).encode(
        color=alt.Color("Nutrient", scale=alt.Scale(domain=df["Nutrient"], range=df["Color"]), legend=alt.Legend(title="栄養素", orient="bottom")),
        order=alt.Order("Calories", sort="descending"),
        tooltip=[alt.Tooltip("Nutrient", title="栄養素"), alt.Tooltip("Calories", format=".0f", title="kcal"), alt.Tooltip("Grams", format=".1f", title="g")]
    )
    
    text = base.mark_text(radius=140).encode(
        text=alt.Text("Calories", format=".0f"),
        order=alt.Order("Calories", sort="descending"),
        color=alt.value("black")
    )
    
    chart = (pie + text).properties(title="PFCカロリーバランス")

    # 4. 詳細テーブル
    pfc_table = [
        {"栄養素": "タンパク質 (P)", "グラム": f"{fmt(results['P_g'])}g", "カロリー": f"{fmt(results['P_cal'])}kcal"},
        {"栄養素": "脂質 (F)", "グラム": f"{fmt(results['F_g'])}g", "カロリー": f"{fmt(results['F_cal'])}kcal"},
        {"栄養素": "炭水化物 (C)", "グラム": f"{fmt(results['C_g'])}g", "カロリー": f"{fmt(results['C_cal'])}kcal"},
    ]

    # 【修正2】すべての要素をvstackでまとめて、この変数をreturnします
    result_view = mo.vstack([
        summary_section,
        mo.md('<div class="chart-container">'),
        mo.ui.altair_chart(chart, chart_selection=False),
        mo.md('</div>'),
        mo.ui.table(pfc_table, selection=None)
    ])

    return result_view,


@app.cell
def _(result_view):
    # 最終的な結果を表示
    result_view
    return


if __name__ == "__main__":
    app.run()