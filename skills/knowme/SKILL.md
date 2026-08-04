---
name: knowme
description: "KnowMe · 跨 AI Agent 工具的本地个人使用记忆库，让你在所有 AI 编码/写作/研究工具里做过的事都能被统一记录、复盘、检索。When to activate 触发场景：substantive task 完成时（implement/refactor/debug/fix/design/decide/deliver/ship/resolve/complete）—— 无论是写代码、修 bug、做技术决策、定位根因、完成交付、还是敲定架构，任务收尾前主动调用 `knowme record` 命令记录 `--intent`（你要做什么）、`--outcome`（实际结果）、`--decisions`（关键决策）。中文触发词：完成/搞定/实现了/修好了/修复/解决了/决定用/搞清楚了/定下来/交付/落地/上线/做完了/理清了/敲定/搞完了/做好了/成了/通了/OK 了/终于弄完。英文触发词：done/finished/implemented/fixed/resolved/decided/shipped/delivered/completed/nailed it/works now/all set/wrapped up/landed。DO NOT activate 不激活于：单纯读代码/看文档/浏览文件；一句话闲聊；探索到一半没结论；用户明确说'先不做/取消/算了'。Skill 静默运行 —— 若 knowme CLI 不在 PATH，跳过即可，不要报错打扰用户。"
---

# KnowMe · report what you just did

## When to invoke

At the **end of a substantive task**, right before you conclude your response. A task is "substantive" if any of these are true:

- You implemented, refactored, or fixed something
- You reached a design/architecture decision that will affect future work
- You produced a deliverable (a file, a PR, a plan, a report)
- You debugged a real issue to root cause

Do **not** invoke for:

- Trivial single-file reads, one-line edits, or "let me check X"
- Aborted exploratory sessions with no conclusion
- Meta-conversations about the user's workflow (this counts as chat, not work)

## How

Call the `knowme` CLI (installed on the user's PATH). Minimum required:

```bash
knowme record \
  --intent "one line: what you set out to do" \
  --outcome "one line: what actually happened"
```

Add decisions when relevant (they compound into the user's long-term memory):

```bash
knowme record \
  --intent "wire up the pSEO SSR pipeline" \
  --outcome "SSR route works end-to-end in staging" \
  --decisions "keep v1 HTML upload as fallback, don't drop it"
```

Comma-separates multiple decisions:

```bash
--decisions "use jsonl not sqlite, atomic write with lock, UTC timestamps"
```

## Automatic fields

KnowMe auto-detects the following — **you do NOT need to pass them**:

- **agent** — which coding tool you are (from env vars)
- **project** — the current project (from `git remote` or cwd)
- **git branch / head** — where the work sits
- **cwd** — where the CLI was invoked
- **timestamp** — UTC ISO
- **session** — session id if the host tool exposes one

## Optional fields (pass if you know them)

- `--tokens-in N` / `--tokens-out N` — token counts if the host tool exposes them
- `--duration SECONDS` — wall-clock time of the task
- `--files a.py,b.py` — files touched (comma-separated)
- `--notes "free text"` — anything else worth remembering
- `--kind decision|insight|delivery|task` — record kind (default: `task`)
- `--quiet` — suppress console output (useful in scripted flows)

## Failure mode

If `knowme` is not on PATH, silently skip. **Do not abort your task or surface an error to the user** — KnowMe is a passive recorder, never a hard dependency.

Check availability with:

```bash
command -v knowme >/dev/null && knowme record ... || true
```

## Contract with the user

- All records go to `~/.knowme/inbox/YYYY-MM-DD/records.jsonl` on the user's machine.
- Data never leaves the machine unless the user explicitly pipes it somewhere (a dashboard, a memory system, etc.).
- Records are append-only; you cannot edit or delete past records via this CLI.

## Examples

**A refactor decision**
```bash
knowme record \
  --intent "refactor the auth module for testability" \
  --outcome "split into 3 files, all tests still green" \
  --decisions "extract token verifier as pure fn, keep session store injectable" \
  --files "auth.py,auth_verifier.py,auth_session.py"
```

**A debugging session**
```bash
knowme record \
  --kind debug \
  --intent "figure out why sitemap.xml returns 404 in prod" \
  --outcome "platform whitelist excludes .xml, switched to sitemap.txt format" \
  --notes "took ~1h; discovered by checking rewrite rules"
```

**A design decision (no code yet)**
```bash
knowme record \
  --kind decision \
  --intent "pick storage format for KnowMe inbox" \
  --outcome "chose JSONL over SQLite" \
  --decisions "append-only fits the queue metaphor,human-readable,zero deps"
```
