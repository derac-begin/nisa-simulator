import marimo

__generated_with = "0.23.1"
app = marimo.App()


@app.cell
def __():
    # =============================================================================
    # 📦 インポート層: 【The Scope Isolation Trap】の完全溶接
    # =============================================================================
    import marimo as mo
    import numpy as np
    import pandas as pd
    import altair as alt
    from decimal import Decimal
    
    return Decimal, alt, mo, np, pd


@app.cell
def __(mo):
    # =============================================================================
    # 📥 状態管理層: The Reactive Ghost Protocol (バックエンド通信核)
    # =============================================================================
    inputs = mo.ui.dictionary({
        "init_taxable": mo.ui.number(start=0, stop=100000000, step=500000, value=5000000, label="初期資産 [特定口座] (円)"),
        "init_nisa": mo.ui.number(start=0, stop=18000000, step=500000, value=3000000, label="初期資産 [NISA口座] (円)"),
        "annual_invest": mo.ui.number(start=0, stop=3600000, step=100000, value=1200000, label="年間NISA積立額 (円)"),
        "withdraw_target": mo.ui.number(start=0, stop=20000000, step=100000, value=1500000, label="年間目標取り崩し額 (円)"),
        "scenario": mo.ui.dropdown(options={"通常運用 (年利 +5%)": "normal", "歴史的暴落 (リーマンショック再現)": "stress", "フラット (0%)": "flat"}, value="通常運用 (年利 +5%)", label="市場リターン・シナリオ"),
        "years": mo.ui.number(start=1, stop=50, step=1, value=25, label="シミュレーション期間 (年)")
    })
    
    return inputs,


@app.cell
def __(Decimal, np):
    # =============================================================================
    # 🛡️ コア・ロジック・エンジン: 【The Over-Underscore Trap】の完全排除
    # =============================================================================

    def nisa_quota_revival_engine(
        current_book_value_total: Decimal,
        annual_investment: Decimal,
        sales_book_value_prev_year: Decimal,
        lifetime_limit: Decimal = Decimal("18000000"),
        annual_limit: Decimal = Decimal("3600000")
    ) -> dict:
        _revived_lifetime_total = current_book_value_total - sales_book_value_prev_year
        _remaining_lifetime_quota = lifetime_limit - _revived_lifetime_total
        _investable_amount = min(annual_limit, _remaining_lifetime_quota)
        _actual_investment = min(annual_investment, _investable_amount)
        _new_book_value_total = _revived_lifetime_total + _actual_investment
        return {
            "investable_amount": _investable_amount,
            "actual_investment": _actual_investment,
            "new_book_value_total": _new_book_value_total
        }

    def historical_stress_test(returns: np.ndarray) -> np.ndarray:
        if returns.size == 0:
            return np.array([1.0])
        _clean_returns = np.nan_to_num(returns, nan=0.0)
        return np.cumprod(1 + _clean_returns)

    def decumulation_optimizer(
        target_amount: Decimal,
        taxable_balance: Decimal,
        nisa_balance: Decimal
    ) -> dict:
        _withdrawn_taxable = min(target_amount, taxable_balance)
        _remaining_need = target_amount - _withdrawn_taxable
        _withdrawn_nisa = min(_remaining_need, nisa_balance)
        _total_withdrawn = _withdrawn_taxable + _withdrawn_nisa
        return {
            "from_taxable": _withdrawn_taxable,
            "from_nisa": _withdrawn_nisa,
            "shortfall": target_amount - _total_withdrawn,
            "new_taxable": taxable_balance - _withdrawn_taxable,
            "new_nisa": nisa_balance - _withdrawn_nisa
        }

    return (
        decumulation_optimizer,
        historical_stress_test,
        nisa_quota_revival_engine,
    )


@app.cell
def __(
    Decimal,
    decumulation_optimizer,
    nisa_quota_revival_engine,
    inputs,
    mo,
    np,
    pd,
):
    # =============================================================================
    # 🛡️ 時系列シミュレーション実行セル (The Stealth Block Trap 対策版)
    # =============================================================================
    if inputs.value is None:
        df_results = None
    else:
        _conf = inputs.value
        
        # ⚠️【CRITICAL FIX】mo.stop()を廃止し、Noneオブジェクトのエクスポートに切り替え
        # 必須入力項目の網羅的欠損バリデーション（空欄検出）
        _required_keys = ["init_taxable", "init_nisa", "annual_invest", "withdraw_target", "scenario", "years"]
        if any(_conf.get(_k) is None for _k in _required_keys) or _conf["years"] <= 0:
            df_results = None
        else:
            _years = int(_conf["years"])
            _init_taxable = Decimal(str(_conf["init_taxable"]))
            _init_nisa = Decimal(str(_conf["init_nisa"]))
            _annual_invest = Decimal(str(_conf["annual_invest"]))
            _withdraw_target = Decimal(str(_conf["withdraw_target"]))
            _scenario = _conf["scenario"]

            if _scenario == "normal":
                _raw_returns = np.full(_years, 0.05)
            elif _scenario == "stress":
                _stress_pattern = [-0.15, -0.25, -0.10, 0.04, 0.05, 0.06]
                _raw_returns = np.array((_stress_pattern * (_years // 6 + 1))[:_years])
            else:
                _raw_returns = np.zeros(_years)

            _clean_returns = np.nan_to_num(_raw_returns, nan=0.0)

            _current_taxable = _init_taxable
            _current_nisa = _init_nisa
            _current_nisa_book = _init_nisa

            _simulation_records = []
            _sales_book_prev = Decimal("0")

            for _i in range(_years):
                _year_idx = _i + 1
                _rate = Decimal(str(_clean_returns[_i]))

                _quota_res = nisa_quota_revival_engine(
                    current_book_value_total=_current_nisa_book,
                    annual_investment=_annual_invest,
                    sales_book_value_prev_year=_sales_book_prev
                )

                _actual_invest = min(_quota_res["actual_investment"], _current_taxable)
                _current_taxable -= _actual_invest
                _current_nisa += _actual_invest
                _current_nisa_book = _quota_res["new_book_value_total"] - _annual_invest + _actual_invest

                _decum_res = decumulation_optimizer(
                    target_amount=_withdraw_target,
                    taxable_balance=_current_taxable,
                    nisa_balance=_current_nisa
                )

                _current_taxable = _decum_res["new_taxable"]
                _current_nisa = _decum_res["new_nisa"]

                if _decum_res["from_nisa"] > 0:
                    _old_nisa_total = _current_nisa + _decum_res["from_nisa"]
                    _reduction_ratio = _decum_res["from_nisa"] / _old_nisa_total
                    _sales_book_prev = _current_nisa_book * _reduction_ratio
                    _current_nisa_book -= _sales_book_prev
                else:
                    _sales_book_prev = Decimal("0")

                _current_taxable *= (Decimal("1") + _rate)
                _current_nisa *= (Decimal("1") + _rate)

                if _current_taxable < 0: _current_taxable = Decimal("0")
                if _current_nisa < 0: _current_nisa = Decimal("0")
                if _current_nisa_book < 0: _current_nisa_book = Decimal("0")

                _total_assets = _current_taxable + _current_nisa

                _simulation_records.append({
                    "経過年": _year_idx,
                    "特定口座残高": float(_current_taxable),
                    "NISA口座残高": float(_current_nisa),
                    "総資産": float(_total_assets),
                    "特定取り崩し": float(_decum_res["from_taxable"]),
                    "NISA取り崩し": float(_decum_res["from_nisa"]),
                    "資産不足額": float(_decum_res["shortfall"])
                })

            df_results = pd.DataFrame(_simulation_records)
    
    return df_results,


@app.cell
def __(alt, df_results, mo):
    # =============================================================================
    # 📈 可視化描画層: 【UI Error Binding】適用セル
    # =============================================================================
    # ⚠️【CRITICAL FIX】上位でエラー(None)を検知した場合、下流を止めずに「警告UI」を流通させる
    if df_results is None:
        chart_ui = mo.callout(
            mo.md("⚠️ **エラー: シミュレーション条件設定のすべての項目に正しい数値を入力してください（期間は1年以上）。**"),
            kind="warn"
        )
    else:
        _df_melted = df_results.melt(
            id_vars=["経過年"],
            value_vars=["特定口座残高", "NISA口座残高", "総資産"],
            var_name="資産内訳",
            value_name="残高 (円)"
        )

        _chart = alt.Chart(_df_melted).mark_line(point=True).encode(
            x=alt.X("経過年:Q", title="経過年数 (年)"),
            y=alt.Y("残高 (円):Q", title="資産残高 (円)"),
            color=alt.Color("資産内訳:N", scale=alt.Scale(domain=["特定口座残高", "NISA口座残高", "総資産"], range=["#e74c3c", "#2ecc71", "#3498db"]))
        ).properties(
            title="資産残高の経年推移プロジェクション",
            width="container",
            height=350
        )

        chart_ui = mo.ui.altair_chart(_chart)
    return chart_ui,


@app.cell
def __(df_results, mo):
    # =============================================================================
    # 📄 データ表示層: The Zero-Index Protocol (静的HTMLテーブル出力)
    # =============================================================================
    # ⚠️【CRITICAL FIX】上位でエラー(None)を検知した場合、こちらは静かに非表示（空文字）化してDAGを維持
    if df_results is None:
        summary_table_ui = mo.md("")
    else:
        _df_summary = df_results[["経過年", "特定口座残高", "NISA口座残高", "総資産"]].copy()
        _df_summary["特定口座 (万)"] = (_df_summary["特定口座残高"] / 10000).round(1)
        _df_summary["NISA口座 (万)"] = (_df_summary["NISA口座残高"] / 10000).round(1)
        _df_summary["総資産 (万)"] = (_df_summary["総資産"] / 10000).round(1)
        
        _df_compressed = _df_summary[["経過年", "特定口座 (万)", "NISA口座 (万)", "総資産 (万)"]]
        _table_html = _df_compressed.to_html(index=False, classes='pure-table pure-table-horizontal', border=0)
        
        summary_table_ui = mo.Html(
            f'<div style="width: 100%; overflow-x: auto; -webkit-overflow-scrolling: touch;">{_table_html}</div>'
        )
    
    return summary_table_ui,


@app.cell
def __(chart_ui, inputs, mo, summary_table_ui):
    # =============================================================================
    # 📦 最終レイアウト統合: ステルスクラッシュを完全に完全克服した垂直ストリーム
    # =============================================================================
    _title_section = mo.md(
        """
        # 📦 NISA Simulator v4.0 (The Decumulation Optimizer)
        WASMによる完全サーバーレス・ローカル計算環境。資産データはブラウザ外へ一歩も流出しません。
        """
    )

    _input_panel_vertical = mo.vstack([
        mo.md("### 🛠️ シミュレーション条件設定"),
        inputs["init_taxable"],
        inputs["init_nisa"],
        inputs["annual_invest"],
        inputs["withdraw_target"],
        inputs["scenario"],
        inputs["years"]
    ]).style({"background-color": "#f8f9fa", "padding": "15px", "border-radius": "8px", "margin-bottom": "20px"})

    final_assembly_ui = mo.vstack([
        _title_section,
        mo.md("---"),
        _input_panel_vertical,
        mo.md("---"),
        mo.md("### 📊 資産残高の推移チャート"),
        chart_ui,
        mo.md("---"),
        mo.md("### 📋 キャッシュフロー詳細サマリー"),
        summary_table_ui
    ])

    final_assembly_ui


if __name__ == "__main__":
    app.run()