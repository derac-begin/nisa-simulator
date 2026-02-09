# Ver 1.2
import marimo

__generated_with = "0.19.0"
# アプリ設定
app = marimo.App(width="full", app_title="AI Shift Scheduler v1.2")

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
        /* テキストエリアの調整 */
        textarea {
            font-family: monospace !important;
            line-height: 1.5 !important;
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
            <div class="app-subtitle">公平・高速・サーバーレス | 自動シフト作成エンジン v1.2</div>
        </div>
        """
    )
    return header,

@app.cell
def _(mo):
    # --- Input UI Section (Refactored for Mobile) ---
    
    # 1. Elements Definition (Mobile Optimized Labels)
    # ラベルを短くし、full_width=Trueにすることでスマホでの折り返しを防ぐ
    
    staff_input = mo.ui.text_area(
        value="佐藤, 鈴木, 高橋, 田中, 伊藤", 
        label="👥 スタッフ名簿 (カンマ区切り)", # 短縮
        placeholder="例: 佐藤, 鈴木, 高橋...",
        full_width=True,
        rows=3
    )

    # スライダー群 (ラベルを短く、全幅表示)
    days_count = mo.ui.slider(7, 31, value=14, label="📅 作成期間 (日)", full_width=True)
    req_staff = mo.ui.slider(1, 10, value=2, label="👤 必要人数/日", full_width=True)
    max_conse = mo.ui.slider(2, 7, value=4, label="🛑 連勤上限", full_width=True)

    # 2. Form Definition (Must use mo.ui.array)
    # mo.vstack(HTML) は渡せないので、mo.ui.array を使用する
    shift_form = mo.ui.form(
        element=mo.ui.array([
            staff_input, 
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
        mo.md("スタッフ名簿と条件を入力し、「Submit」ボタンを押してください。"),
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
        staff_input,
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

    # パラメータ取得 (Fixed Indices)
    # mo.ui.array の順番通りに取得 (0:Staff, 1:Days, 2:Req, 3:Max)
    vals = shift_form.value
    raw_staff_text = vals[0]
    p_days_count = vals[1]
    p_req_staff = vals[2]
    p_max_conse = vals[3]

    # スタッフリストのパース処理 (Logic)
    # カンマまたは改行で分割し、空白を除去
    staff_list = [
        name.strip() 
        for name in raw_staff_text.replace("\n", ",").split(",") 
        if name.strip()
    ]
    p_staff_count = len(staff_list)

    # 停止条件2: 入力バリデーション (修正: マークダウン・HTMLタグを除去)
    # スタッフが0人、または必要人数が総数を超えている場合
    error_msg = ""
    if p_staff_count == 0:
        error_msg = "⚠️ エラー: スタッフ名が入力されていません。"
    elif p_req_staff > p_staff_count:
        error_msg = f"⚠️ 設定エラー: 1日の必要人数 ({p_req_staff}人) がスタッフ総数 ({p_staff_count}人) を超えています。"

    if error_msg:
        error_view = mo.vstack([
            header,
            control_panel,
            mo.md("---"),
            mo.callout(error_msg, kind="danger")
        ])
        mo.stop(True, error_view)


    # 計算処理
    with mo.status.spinner("AIが最適なシフトパズルを解いています..."):

        # 1. ロジック実行
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

        # 4. CSVダウンロード機能 (Mobile Fix)
        # mo.download を使用して独立したボタンを作成
        # .encode("utf-8-sig") を追加して、Excel用の「BOM」を付与
        csv_data = df_calendar.to_csv(index=False).encode("utf-8-sig")
        download_btn = mo.download(
            data=csv_data, 
            filename="shift_schedule.csv", 
            label="📥 CSVをダウンロード"
        )

        # 5. 結果通知エリア (成功/警告)
        if failed_dates:
            status_alert = mo.callout(
                f"⚠️ 注意 : 以下の日程で必要人数を確保できませんでした（連勤制限のため）。\n欠員日 : {', '.join(failed_dates)}\n ⇒ スタッフを増やすか、連勤制限を緩和してください。",
                kind="warn"
            )
        else:
            status_alert = mo.callout(
                "✅ 成功 : 全日程で必要人数を確保しました！",
                kind="success"
            )

        # 6. 最終レイアウト構築
        # ダウンロードボタンをテーブル直上に配置し、スマホでも押しやすくする
        dashboard = mo.vstack([
            header,
            control_panel,
            mo.md("---"),
            status_alert,
            mo.md("### 📈 分析レポート"),
            chart_ui,
            mo.md("### 📅 確定シフト表"),
            download_btn, # UI Fix: テキストではなく実ボタンを配置
            mo.ui.table(df_calendar, pagination=True, page_size=10, selection=None),
            mo.md("---"),
            mo.md(f"<small>Generated by AI Shift Scheduler v1.2 | {datetime.now().strftime('%Y-%m-%d')}</small>")
        ], gap=1.5)

    return (
        assigned_today,
        calendar_rows,
        candidates,
        chart,
        chart_ui,
        csv_data,
        d,
        dashboard,
        dates,
        df_calendar,
        df_stats,
        download_btn,
        error_msg,
        error_view,
        failed_dates,
        p_days_count,
        p_max_conse,
        p_req_staff,
        p_staff_count,
        raw_staff_text,
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