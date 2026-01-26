# Skill: Code Auditor (v0.19.0 Modern)

## 🎯 Technical Environment
- **Framework:** marimo (v0.19.0)
- **Layout:** Native Responsive (`mo.flex`)
- **Strict Version:** 0.19.0 以前の非効率な手書きCSSハックは卒業し、純正APIを優先する。

## 🛡️ Audit Protocols
1. **Layout Logic:** `mo.hstack` 単独使用を検知した場合は `mo.flex(wrap=True)` への変更を促せ。
2. **Reactive Safety:** f-string 内に `mo.ui` 要素が含まれていないか厳格にチェックせよ。
3. **UX Check:** 計算負荷が高い処理に対し、`mo.status` での進捗表示が検討されているか。
4. **WASM Native:** 引き続き `requests`, `os` 等の外部依存を排除せよ。

## ✅ Validation Checklist
- [ ] `__generated_with = "0.19.0"` もしくはそれ以上か？
- [ ] スマホ対応が `mo.flex` 等の純正機能で実現されているか？
- [ ] UI がリスト形式でレイアウト関数に渡されているか？