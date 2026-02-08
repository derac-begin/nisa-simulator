import marimo

__generated_with = "0.18.4"
app = marimo.App()

@app.cell
def _():
    import marimo as mo
    import matplotlib.pyplot as plt
    import japanize_matplotlib
    return mo, plt, japanize_matplotlib

@app.cell
def _(mo):
    mo.md("""
    # 💪 ボディメイク・シミュレーター

    現在の **身長**、**体重**、**体脂肪率** を入力してください。
    BMIや除脂肪体重（LBM）、FFMI（マッチョ指数）を可視化します。
    """)
    return


@app.cell
def _(mo):
    # 身長：140cm〜220cmまで
    height_slider = mo.ui.slider(
        start=140, stop=220, step=1.0, value=170.0, label="身長 (cm)"
    )
    # 体重：40kg〜120kgまで
    weight_slider = mo.ui.slider(
        start=40, stop=120, step=0.1, value=65.0, label="体重 (kg)"
    )
    # 体脂肪率：3%〜50%まで
    fat_slider = mo.ui.slider(
        start=3, stop=50, step=0.5, value=15.0, label="体脂肪率 (%)"
    )

    mo.hstack([height_slider, weight_slider, fat_slider], justify="start")
    return fat_slider, height_slider, weight_slider


@app.cell
def _(fat_slider, height_slider, mo, plt, weight_slider):
    # 値の取得
    h_cm = height_slider.value
    w = weight_slider.value
    f_rate = fat_slider.value

    # 基本計算
    h_m = h_cm / 100.0
    bmi = w / (h_m * h_m)
    fat_mass = w * (f_rate / 100)       # 体脂肪量
    lbm = w - fat_mass                  # 除脂肪体重 (Lean Body Mass)
    ffmi = lbm / (h_m * h_m)            # 除脂肪体重指数

    # BMI 判定
    if bmi < 18.5:
        bmi_comment = "低体重 (痩せ型)"
    elif bmi < 25.0:
        bmi_comment = "普通体重"
    elif bmi < 30.0:
        bmi_comment = "肥満 (1度)"
    else:
        bmi_comment = "肥満 (2度以上)"

    # FFMI 判定
    if ffmi < 18.5:
        ffmi_comment = "標準 (痩せ型〜普通)"
    elif ffmi < 20.0:
        ffmi_comment = "標準 (ガッチリ)"
    elif ffmi < 22.0:
        ffmi_comment = "アスリート級"
    else:
        ffmi_comment = "ボディビルダー級"

    # 円グラフの作成
    plt.figure(figsize=(5, 5))
    colors = ['#4CAF50', '#FF5722'] # Green, Deep Orange
    labels = ['除脂肪体重 (LBM)', '体脂肪量']

    plt.pie(
        [lbm, fat_mass], 
        labels=labels, 
        colors=colors, 
        autopct='%1.1f%%', 
        startangle=90,
        counterclock=False,
        wedgeprops={'edgecolor': 'white'}
    )
    plt.title(f"体重 {w}kg (BMI: {bmi:.1f})")

    # 結果の表示
    mo.vstack([
        plt.gca(),
        mo.md(
            f"""
            ### 📊 診断結果

            * **BMI**: `{bmi:.2f}` —— **{bmi_comment}**
            * **体脂肪量**: `{fat_mass:.2f} kg`
            * **除脂肪体重 (LBM)**: `{lbm:.2f} kg`
            * **FFMI (除脂肪量指数)**: `{ffmi:.2f}` —— **{ffmi_comment}**
            """
        )
    ])
    return


if __name__ == "__main__":
    app.run()