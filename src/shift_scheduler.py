import marimo

__generated_with = "0.19.0"
# アプリ設定
app = marimo.App(width="full", app_title="AI Shift Scheduler v1.1")

@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import altair as alt
    import random
    from datetime import datetime, timedelta
    
    # timeモジュールはWASMフリーズ回避のため削除
    return alt, datetime, mo, pd, random, timedelta

@app.cell
def _(mo):
    # --- CSS Styling Section ---
    mo.md(
        """
        <style>
        body {
            font-family: "Helvetica Neue", Arial, "Hiragino Kaku Gothic ProN", "Hiragino Sans", Meiryo, sans-serif;
            background-color: #f8f9fa;
        }
        .app-header {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            padding: 2.5rem;
            border-radius: 16px;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }
        .app-title {
            font-size: 2.2rem;
            font-weight: 800;
            margin: 0;
            text-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .app-subtitle {
            font-size: 1.1rem;
            opacity: 0.95;
            margin-top: 0.5rem;
            font-weight: 500;
        }
        .form-container {
            border: 1px solid #e9ecef;
            padding: 2rem;
            border-radius: 12px;
            background-color: #ffffff;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        }
        </style>
        """
    )
    return

@app.cell
def _(mo):
    # --- Header Section ---
    header = mo.Html(
        """
        <div class="app-header">
            <div class="app-title">📅 AI Shift Scheduler</div>
            <div class="app-subtitle">公平・高速・サーバーレス | 自動シフト作成エンジン v1.1</div>
        </div>
        """
    )
    return header,

@app.cell
def _(mo):
    # --- Input UI Section ---
    
    # UI Components
    staff_count = mo.ui.slider(3, 20, value=7, label="スタッフ人数")
    days_count = mo.ui.slider(7, 31, value=14, label="作成期間（日）")
    req_staff = mo.ui.slider(1, 10, value=3, label="1日の必要人数")
    max_conse = mo.ui.slider(2, 7, value=4, label="最大連勤数（制限）")

    # Form Definition (Safe Array Pattern)
    shift_form = mo.ui.form(
        element=mo.ui.array([
            staff_count, 
            days_count, 
            req_staff, 
            max_conse
        ]),
        label="🚀 条件を確定してシフトを作成", 
        bordered=False
    )
    
    # Control Panel Layout
    control_panel = mo.vstack([
        mo.md("### 🛠️ 条件設定"),
        mo.md("以下の条件を入力し、「Submit」ボタンを押してください。"),
        mo.Html('<div class="form-container">'),
        shift_form,
        mo.Html('</div>'),
    ])
    
    return (
        control_panel,
        days_count,
        max_conse,
        req_staff,
        shift_form,
        staff_count,
    )

@app.cell
def _(
    alt,
    control_panel,
    datetime,
    header,
    mo,
    pd,
    random,
    shift_form,
    timedelta,
):
    # --- Main Logic & Visualization Section ---
    
    # 停止条件1: フォーム未送信時
    mo.stop(
        shift_form.value is None,
        mo.vstack([header, control_panel])
    )

    # パラメータ取得
    vals = shift_form.value
    p_staff_count = vals[0]
    p_days_count = vals[1]
    p_req_staff = vals[2]
    p_max_conse = vals[3]

    # 停止条件2: 入力バリデーション (修正: マークダウン・HTMLタグを除去)
    # 必要人数がスタッフ総数を超えている場合、計算させない
    if p_req_staff > p_staff_count:
        error_view = mo.vstack([
            header,
            control_panel,
            mo.md("---"),
            mo.callout(
                f"⚠️ 設定エラー : 1日の必要人数 ({p_req_staff}人) がスタッフ総数 ({p_staff_count}人) を超えています。条件を見直してください。",
                kind="danger"
            )
        ])
        mo.stop(True, error_view)


    # 計算処理
    with mo.status.spinner("AIが最適なシフトパズルを解いています..."):

        # 1. ロジック実行
        staff_list = [f"Staff_{i+1}" for i in range(p_staff_count)]
        dates = [datetime.now().date() + timedelta(days=i) for i in range(p_days_count)]
        
        schedule = {date: [] for date in dates}
        staff_stats = {s: {"consecutive": 0, "total_shifts": 0} for s in staff_list}
        
        # 詰み判定用のリスト
        failed_dates = []

        for d in dates:
            # 公平化ロジック
            candidates = sorted(
                staff_list, 
                key=lambda s: (staff_stats[s]["total_shifts"], random.random())
            )
            
            assigned_today = 0
            for s in candidates:
                if assigned_today >= p_req_staff:
                    break
                
                # 制約チェック: 最大連勤数
                if staff_stats[s]["consecutive"] < p_max_conse:
                    schedule[d].append(s)
                    staff_stats[s]["consecutive"] += 1
                    staff_stats[s]["total_shifts"] += 1
                    assigned_today += 1
            
            # 欠員発生チェック
            if assigned_today < p_req_staff:
                failed_dates.append(d.strftime("%m/%d"))

            # 連勤カウンタのリセット
            todays_workers = schedule[d]
            for s in staff_list:
                if s not in todays_workers:
                    staff_stats[s]["consecutive"] = 0

        # 2. データフレーム生成
        calendar_rows = []
        for d, workers in schedule.items():
            row = {"Date": d.strftime("%Y-%m-%d (%a)")}
            for s in staff_list:
                # 視認性向上: 空欄より "-" の方が表崩れしにくい
                row[s] = "🟢" if s in workers else "-" 
            calendar_rows.append(row)
        df_calendar = pd.DataFrame(calendar_rows)

        # 統計形式
        stats_rows = [
            {"Staff": s, "Shifts": data["total_shifts"]} 
            for s, data in staff_stats.items()
        ]
        df_stats = pd.DataFrame(stats_rows)

        # 3. グラフ描画 (Altair)
        # cornerRadiusTopLeft などを使用せず、シンプルな mark_bar() を採用
        chart = alt.Chart(df_stats).mark_bar().encode(
            x=alt.X('Staff', sort=None, title="スタッフ名"),
            y=alt.Y('Shifts', title='出勤回数'),
            color=alt.Color('Shifts', legend=None, scale=alt.Scale(scheme='tealblues')),
            tooltip=['Staff', 'Shifts']
        ).properties(
            title="📊 スタッフ別 出勤回数バランス",
            width="container", # スマホ対応
            height=300
        )
        
        chart_ui = mo.ui.altair_chart(chart)

        # 4. 結果通知エリア (成功/警告)
        if failed_dates:
            status_alert = mo.callout(
                f"⚠️ 注意 : 以下の日程で必要人数を確保できませんでした（連勤制限のため）。欠員日 : {', '.join(failed_dates)} ⇒ スタッフを増やすか、連勤制限を緩和してください。",
                kind="warn"
            )
        else:
            status_alert = mo.callout(
                "✅ 成功 : 全日程で必要人数を確保しました！",
                kind="success"
            )

        # 5. 最終レイアウト構築
        dashboard = mo.vstack([
            header,
            control_panel,
            mo.md("---"),
            status_alert,
            mo.md("### 📈 分析レポート"),
            chart_ui,
            mo.md("### 📅 確定シフト表"),
            mo.md("右下の「Download」からCSVでダウンロードできます ↓"),
            mo.ui.table(df_calendar, pagination=True, page_size=10, selection=None),
            mo.md("---"),
            mo.md(f"<small>Generated by AI Shift Scheduler v1.1 | {datetime.now().strftime('%Y-%m-%d')}</small>")
        ], gap=1.5)

    return (
        assigned_today,
        calendar_rows,
        candidates,
        chart,
        chart_ui,
        d,
        dashboard,
        dates,
        df_calendar,
        df_stats,
        error_view,
        failed_dates,
        p_days_count,
        p_max_conse,
        p_req_staff,
        p_staff_count,
        schedule,
        staff_list,
        staff_stats,
        stats_rows,
        status_alert,
        todays_workers,
        vals,
        workers,
    )

@app.cell
def _(dashboard):
    dashboard
    return