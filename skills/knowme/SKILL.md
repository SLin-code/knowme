---
name: knowme
description: "KnowMe · 跨 AI Agent 工具的本地个人使用记忆库，让你在所有 AI 工具里做过的事（编码/写作/研究/内容创作/设计/分析）都被统一记录、可复盘、可检索。When to activate 触发场景：任何 substantive task 完成时，包括但不限于：(1) 编程 — implement/refactor/debug/fix；(2) 内容创作 — 写文章/写文案/写脚本/生成报告/整理笔记；(3) 研究调研 — 分析问题/对比方案/竞品调研/技术选型；(4) 设计决策 — 定架构/敲定方案/画图；(5) 交付类 — 产出文件/PR/PPT/报告/代码/图片/视频。任务收尾前主动调用 `knowme record` 命令记录 `--agent`（你是谁）、`--intent`（要做什么）、`--outcome`（实际结果）、`--decisions`（关键决策）。CRITICAL：请在**交付内容前**就调用，不要等用户追问才补。中文触发词：完成/搞定/写完了/交付/产出/整理好了/生成了/实现了/修好了/修复/解决了/决定用/搞清楚了/定下来/落地/上线/做完了/理清了/敲定/搞完了/做好了/成了/通了/OK 了/终于弄完。英文触发词：done/finished/wrote/produced/delivered/generated/implemented/fixed/resolved/decided/shipped/completed/nailed it/works now/all set/wrapped up/landed。DO NOT activate 不激活于：单纯读代码/看文档/浏览文件；一句话闲聊；探索到一半没结论；用户明确说'先不做/取消/算了'。Skill 静默运行 —— 若 knowme CLI 不在 PATH，跳过即可，不要报错打扰用户。"
---

# KnowMe · report what you just did

## When to invoke

**CRITICAL TIMING**: call `knowme record` **BEFORE** you deliver the final result to the user,
not after they ask "did you record it?". Recording is part of finishing the task, not an
afterthought.

At the **end of a substantive task**. A task is "substantive" if any of these are true:

### Coding & engineering
- You implemented, refactored, or fixed something
- You reached a design/architecture decision that will affect future work
- You debugged a real issue to root cause

### Content & writing
- You wrote an article, blog post, doc, README, PRD, or long-form piece
- You produced marketing copy, video script, presentation, or notes
- You generated a report, digest, summary, or research writeup

### Research & analysis
- You did competitive analysis, technology comparison, or feasibility study
- You investigated a question and reached a conclusion
- You surveyed literature/prior art and synthesized findings

### Deliverables (any medium)
- You produced a concrete file: PR, plan, report, script, image, video, deck
- You shipped something the user asked for

Do **not** invoke for:

- Trivial single-file reads, one-line edits, or "let me check X"
- Aborted exploratory sessions with no conclusion
- Meta-conversations about the user's workflow (this counts as chat, not work)
- Purely conversational replies with no artifact produced

## How

Call the `knowme` CLI (installed on the user's PATH). Minimum required + self-declare who you are:

```bash
knowme record \
  --agent "your-agent-name" \
  --intent "one line: what you set out to do" \
  --outcome "one line: what actually happened"
```

**`--agent` is your self-declared name** (e.g. `claude-code`, `codex`, `cursor`, `catpaw`, or whatever
identifies you). KnowMe doesn't guess — every agent identifies itself so records can be filtered by
source later. If you're not sure what to call yourself, use your product name in lowercase-kebab-case.

Add decisions when relevant (they compound into the user's long-term memory):

```bash
knowme record \
  --agent "claude-code" \
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

Every example includes `--agent` — substitute your own name.

**A refactor decision**
```bash
knowme record \
  --agent claude-code \
  --intent "refactor the auth module for testability" \
  --outcome "split into 3 files, all tests still green" \
  --decisions "extract token verifier as pure fn, keep session store injectable" \
  --files "auth.py,auth_verifier.py,auth_session.py"
```

**A debugging session**
```bash
knowme record \
  --agent codex \
  --kind debug \
  --intent "figure out why sitemap.xml returns 404 in prod" \
  --outcome "platform whitelist excludes .xml, switched to sitemap.txt format" \
  --notes "took ~1h; discovered by checking rewrite rules"
```

**A design decision (no code yet)**
```bash
knowme record \
  --agent cursor \
  --kind decision \
  --intent "pick storage format for KnowMe inbox" \
  --outcome "chose JSONL over SQLite" \
  --decisions "append-only fits the queue metaphor,human-readable,zero deps"
```
