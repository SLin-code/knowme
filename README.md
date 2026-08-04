# KnowMe

> Cross-agent activity trace — record what any AI coding agent just did into a
> unified local memory. Then you own your own AI-usage knowledge base.

**Status**: v0.1.0 · early / self-hosted · one-file JSONL inbox at `~/.knowme/`

## The idea

You use several AI coding tools — Claude Code, Codex, Cursor, WorkBuddy,
OpenClaw, Copilot, others. Each one keeps its own history in its own format,
in its own place. **Reviewing "what did I do this week?" across all of them is
painful.**

KnowMe is a tiny CLI + a shared Skill definition. Any agent that can read a
`SKILL.md` (all major ones can) is told: **when you finish a real task,
call `knowme record` and briefly say what you did**. Records land in
`~/.knowme/inbox/YYYY-MM-DD/records.jsonl` — one JSON object per line.

Then:

- **You can query** — `knowme query --days 7 --grep sitemap`
- **Downstream tools can consume** — any dashboard / memory system / knowledge
  base can read `~/.knowme/inbox/` as an event stream, on its own cadence.

## Design principles

1. **Local-first** — data never leaves your machine unless you pipe it somewhere.
2. **Agent-agnostic** — the Skill is a plain `SKILL.md`, works in any tool that
   supports Skills (`~/.<agent>/skills/`).
3. **Minimum agent burden** — agent reports 3 fields (intent, outcome, decisions);
   CLI auto-detects the other 6 (project, git, cwd, timestamp, session, agent).
4. **Zero runtime deps** — pure Python stdlib. `pyyaml` is only used if you have
   a config file (fully optional).
5. **JSONL, not SQLite** — an inbox is a queue; keep it inspectable with `cat`.

## Install

Two steps: put the CLI on your PATH, install the Skill into each agent you want
to instrument.

### 1. Put `knowme` on PATH

Clone the repo (or `pip install -e .` once we ship it):

```bash
git clone https://github.com/YOUR/knowme ~/dev/knowme
```

Add the CLI to your shell:

```bash
# ~/.zshrc or ~/.bashrc
export PATH="$HOME/dev/knowme/bin:$PATH"
```

Verify:

```bash
knowme --version
knowme doctor
```

### 2. Install the Skill into each agent

The Skill is one file (`skills/knowme/SKILL.md`) and gets copied into that
agent's skills directory. Each agent has its own path — pick the one(s) you use:

```bash
# Claude Code
mkdir -p ~/.claude/skills/knowme
cp ~/dev/knowme/skills/knowme/SKILL.md ~/.claude/skills/knowme/

# Codex
mkdir -p ~/.codex/skills/knowme
cp ~/dev/knowme/skills/knowme/SKILL.md ~/.codex/skills/knowme/

# Cursor
mkdir -p ~/.cursor/skills/knowme
cp ~/dev/knowme/skills/knowme/SKILL.md ~/.cursor/skills/knowme/

# WorkBuddy / OpenClaw / Copilot / etc. — same idea, ~/.<agent>/skills/knowme/
```

After that, the next conversation with each agent will pick up the new skill
automatically — you don't need to restart anything.

### 3. Verify it's picking up

Have a real conversation with the agent — implement something, decide something,
fix something. When the agent wraps up, it should say something like *"…let me
record this to KnowMe"* and run `knowme record`.

Check what landed:

```bash
knowme status -v
knowme query --days 1
```

If the agent isn't recording, run `knowme doctor` — usually the CLI isn't on
PATH inside the agent's shell.

## CLI reference

```
knowme record   Report a completed task (agent-initiated)
knowme query    Search past records
knowme status   Show inbox counts
knowme doctor   Diagnose install & environment
```

### `knowme record`

The primary entry. Agent-initiated after a substantive task.

```bash
knowme record \
  --intent "wire pSEO SSR pipeline" \
  --outcome "SSR route works end-to-end in staging" \
  --decisions "keep v1 HTML upload as fallback, don't drop it"
```

Long outcome? Pipe via stdin:

```bash
some-tool-that-produces-long-text | knowme record --intent "…"
```

Optional fields (pass if you know them):

- `--tokens-in N` / `--tokens-out N`
- `--duration SECONDS`
- `--files a.py,b.py,c.py`
- `--notes "free text"`
- `--kind decision|insight|delivery|debug|task` (default: `task`)

Auto-detected (do not pass these):

- **agent** — from env vars (CLAUDECODE, CURSOR_TRACE_ID, CODEX_SESSION_ID, …)
- **project** — from `git remote` or cwd
- **git branch / head** — from git
- **cwd, timestamp, session id**

### `knowme query`

```bash
knowme query --days 7                     # last week
knowme query --project WorkMe --limit 20  # last 20 records in WorkMe
knowme query --grep "sitemap" -v          # full-text search with details
knowme query --agent codex --days 30      # only Codex activity, 30d
knowme query --json --days 1 | jq .       # machine-readable
```

### `knowme status` / `knowme doctor`

```bash
knowme status -v                          # today's counts + recent titles
knowme doctor                             # PATH, permissions, agent detection
```

## Where records live

```
~/.knowme/
└── inbox/
    ├── 2026-08-04/
    │   └── records.jsonl        ← append-only, one JSON per line
    ├── 2026-08-05/
    │   └── records.jsonl
    └── …
```

A record looks like:

```json
{
  "ts": "2026-08-04T10:22:31.123456+00:00",
  "v": 1,
  "kind": "task",
  "intent": "wire pSEO SSR pipeline",
  "outcome": "SSR route works end-to-end in staging",
  "decisions": ["keep v1 HTML upload as fallback"],
  "env": {
    "cwd": "/Users/you/dev/mars-web",
    "project": "mars-web",
    "git_branch": "feature/pseo-ssr",
    "git_head": "a1b2c3d4e5f6",
    "agent": "claude-code",
    "session": "abc-123"
  }
}
```

## Downstream: build your own consumer

`~/.knowme/inbox/` is a plain event stream. Consumers just tail JSONL files.
Examples:

- **Personal memory system**: a nightly script that reads today's records and
  writes a journal entry.
- **Weekly digest**: `knowme query --days 7 --json | your-summarizer`.
- **Search over your work**: index records with your favorite tool (ripgrep,
  meilisearch, etc.).

## What KnowMe is NOT

- **Not** a chat log recorder — original conversation content stays in each
  agent's own history. KnowMe records summaries agents post-hoc.
- **Not** a token-counting or time-tracking tool — try Vibe Island for that.
- **Not** a memory server that agents fetch from — that's what Memmy does.
- **Not** an LLM wrapper — KnowMe never calls an LLM. Agents provide summaries;
  KnowMe just files them.

## Contributing / roadmap

- [ ] `knowme scan` — passive-mode collector that reads agent session logs
      directly (for agents that don't cooperate with the Skill).
- [ ] `knowme export --format markdown|csv|opml`
- [ ] pip installable
- [ ] optional lightweight web viewer (`knowme serve`)

Contributions welcome, especially: agent-specific collectors and Skill tuning
for different agent behaviors.

## License

MIT (planned).
