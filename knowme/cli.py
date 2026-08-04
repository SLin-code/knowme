"""KnowMe CLI dispatch.

Subcommands:
  record   — agent-initiated report of a completed task
  query    — read past records with filters
  status   — quick sanity check (config path, inbox counts)
  doctor   — diagnose install: PATH, permissions, detected agents

We handroll argument parsing with argparse; no external CLI framework so
KnowMe stays a zero-runtime-dep pure-Python tool (yaml is optional).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path

from . import __version__
from .config import load as load_config
from .recorder import record as do_record
from .storage import read_day, read_range, list_dates


# ---------- helpers ----------

def _split_csv(s: str | None) -> list[str] | None:
    """Parse comma-separated CLI args. None passthrough."""
    if not s:
        return None
    return [x.strip() for x in s.split(",") if x.strip()] or None


def _read_stdin_if_any() -> str | None:
    """Read stdin if it's a pipe (not a terminal). Used so agents can pipe long-form
    outcome/notes rather than cramming them into a single --outcome flag."""
    if sys.stdin.isatty():
        return None
    data = sys.stdin.read().strip()
    return data or None


def _fmt_ts(iso: str) -> str:
    """Localize ISO ts to HH:MM for compact display."""
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone().strftime("%m-%d %H:%M")
    except Exception:
        return iso[:16]


# ---------- record ----------

def cmd_record(args: argparse.Namespace, cfg: dict) -> int:
    # If --outcome not given but stdin has content, use stdin as outcome.
    outcome = args.outcome
    if outcome is None:
        piped = _read_stdin_if_any()
        if piped:
            outcome = piped
    result = do_record(
        cfg,
        intent=args.intent,
        outcome=outcome,
        decisions=_split_csv(args.decisions),
        tokens_in=args.tokens_in,
        tokens_out=args.tokens_out,
        duration_seconds=args.duration,
        files=_split_csv(args.files),
        notes=args.notes,
        kind=args.kind,
        agent=args.agent,
        session=args.session,
    )
    if args.quiet:
        return 0
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        rec = result["record"]
        proj = rec["env"].get("project") or "?"
        agent = rec["env"].get("agent") or "?"
        print(f"✓ recorded [{agent} @ {proj}] {rec['intent']}")
        print(f"  → {result['written_to']}")
    return 0


# ---------- query ----------

def cmd_query(args: argparse.Namespace, cfg: dict) -> int:
    # Resolve date range
    if args.since:
        since = args.since
    elif args.days:
        since = (datetime.now() - timedelta(days=args.days)).strftime("%Y-%m-%d")
    else:
        since = None

    rows = read_range(cfg, since_date=since, until_date=args.until)

    # Filter by fields
    if args.project:
        rows = [r for r in rows if (r.get("env") or {}).get("project") == args.project]
    if args.agent:
        rows = [r for r in rows if (r.get("env") or {}).get("agent") == args.agent]
    if args.kind:
        rows = [r for r in rows if r.get("kind") == args.kind]
    if args.grep:
        needle = args.grep.lower()
        def has(r):
            hay = " ".join([
                r.get("intent", ""), r.get("outcome", ""), r.get("notes", ""),
                " ".join(r.get("decisions", [])),
            ]).lower()
            return needle in hay
        rows = [r for r in rows if has(r)]

    if args.limit:
        rows = rows[-args.limit:]

    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0

    if not rows:
        print("(no matching records)")
        return 0

    for r in rows:
        env = r.get("env") or {}
        proj = env.get("project") or "?"
        agent = env.get("agent") or "?"
        ts = _fmt_ts(r.get("ts", ""))
        print(f"{ts}  [{agent} @ {proj}]  {r.get('intent','?')}")
        if r.get("outcome") and args.verbose:
            print(f"           → {r['outcome']}")
        if r.get("decisions") and args.verbose:
            print(f"           decisions: {', '.join(r['decisions'])}")
    print(f"\n{len(rows)} record(s)")
    return 0


# ---------- status ----------

def cmd_status(args: argparse.Namespace, cfg: dict) -> int:
    print(f"knowme {__version__}")
    print(f"inbox: {cfg['inbox_dir_abs']}")
    dates = list_dates(cfg)
    today = datetime.now().strftime("%Y-%m-%d")
    today_rows = read_day(cfg, today)
    print(f"today ({today}): {len(today_rows)} record(s)")
    print(f"total days with records: {len(dates)}")
    if dates:
        print(f"date range: {dates[-1]} .. {dates[0]}")
    if today_rows and args.verbose:
        print("recent:")
        for r in today_rows[-5:]:
            env = r.get("env") or {}
            print(f"  [{env.get('agent','?')} @ {env.get('project','?')}] {r.get('intent','?')}")
    return 0


# ---------- doctor ----------

def cmd_doctor(args: argparse.Namespace, cfg: dict) -> int:
    """Diagnose install: PATH, inbox writable, which agents are candidates for skill install."""
    ok = True

    def check(name: str, passed: bool, hint: str = "") -> None:
        nonlocal ok
        mark = "✓" if passed else "✗"
        line = f"  {mark} {name}"
        if not passed and hint:
            line += f"  — {hint}"
        print(line)
        if not passed:
            ok = False

    print("KnowMe doctor")
    print(f"version: {__version__}")

    # 1. knowme on PATH?
    on_path = shutil.which("knowme") is not None
    check("knowme on PATH", on_path,
          "add ~/dev/knowme/bin (or wherever `bin/knowme` lives) to PATH")

    # 2. inbox writable?
    inbox = Path(cfg["inbox_dir_abs"])
    try:
        inbox.mkdir(parents=True, exist_ok=True)
        test = inbox / ".doctor-test"
        test.write_text("ok")
        test.unlink()
        check(f"inbox writable ({inbox})", True)
    except OSError as e:
        check(f"inbox writable ({inbox})", False, str(e))

    # 3. agent skill dirs — where user *could* install the skill
    print("\nagents detected (skill install candidates):")
    candidates = [
        ("claude-code", "~/.claude/skills"),
        ("codex", "~/.codex/skills"),
        ("cursor", "~/.cursor/skills"),
        ("workbuddy", "~/.workbuddy/skills"),
        ("openclaw", "~/.openclaw/skills"),
        ("copilot", "~/.copilot/skills"),
        ("gemini", "~/.gemini/skills"),
        ("kiro", "~/.kiro/skills"),
    ]
    any_agent = False
    for name, path in candidates:
        p = Path(path).expanduser()
        if p.exists():
            any_agent = True
            installed = (p / "knowme").exists()
            mark = "✓" if installed else "•"
            note = "(knowme skill installed)" if installed else "(available; skill not installed)"
            print(f"  {mark} {name:<15} {path}  {note}")
    if not any_agent:
        print("  (no known agent skill dirs found; that's fine if you're just using CLI)")

    # 4. detected env
    print("\ncurrent environment:")
    from . import environment as env
    snap = env.snapshot()
    for k in ("agent", "project", "git_branch", "git_head", "cwd", "session"):
        print(f"  {k}: {snap.get(k) or '-'}")

    print()
    print("OK" if ok else "issues found — see hints above")
    return 0 if ok else 1


# ---------- parser ----------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="knowme",
        description="Cross-agent activity trace — record what any AI agent just did.",
    )
    p.add_argument("--version", action="version", version=f"knowme {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    # record
    pr = sub.add_parser("record", help="Report a completed task")
    pr.add_argument("--intent", required=True, help="What you set out to do (one line)")
    pr.add_argument("--outcome", help="What actually happened (or pipe long text via stdin)")
    pr.add_argument("--decisions", help="Key decisions, comma-separated")
    pr.add_argument("--tokens-in", type=int, dest="tokens_in", help="Input tokens used")
    pr.add_argument("--tokens-out", type=int, dest="tokens_out", help="Output tokens used")
    pr.add_argument("--duration", type=int, help="Duration in seconds")
    pr.add_argument("--files", help="Files touched, comma-separated")
    pr.add_argument("--notes", help="Free-text notes")
    pr.add_argument("--kind", default="task", help="Record kind (default: task)")
    pr.add_argument("--agent", help="Agent name (self-declared; overrides KNOWME_AGENT env)")
    pr.add_argument("--session", help="Session id (self-declared; overrides KNOWME_SESSION env)")
    pr.add_argument("--json", action="store_true", help="Print result as JSON")
    pr.add_argument("--quiet", "-q", action="store_true", help="Suppress output")
    pr.set_defaults(func=cmd_record)

    # query
    pq = sub.add_parser("query", help="Search past records")
    pq.add_argument("--since", help="Date (YYYY-MM-DD) — records on or after")
    pq.add_argument("--until", help="Date (YYYY-MM-DD) — records on or before")
    pq.add_argument("--days", type=int, help="Shortcut: last N days (implies --since)")
    pq.add_argument("--project", help="Filter by project name")
    pq.add_argument("--agent", help="Filter by agent name (claude-code, codex, ...)")
    pq.add_argument("--kind", help="Filter by record kind")
    pq.add_argument("--grep", help="Full-text search across intent/outcome/notes/decisions")
    pq.add_argument("--limit", type=int, help="Show at most N records (from tail)")
    pq.add_argument("--verbose", "-v", action="store_true", help="Show outcome + decisions")
    pq.add_argument("--json", action="store_true", help="Emit JSON array")
    pq.set_defaults(func=cmd_query)

    # status
    ps = sub.add_parser("status", help="Show inbox status")
    ps.add_argument("--verbose", "-v", action="store_true", help="Show today's recent records")
    ps.set_defaults(func=cmd_status)

    # doctor
    pd = sub.add_parser("doctor", help="Diagnose install & environment")
    pd.set_defaults(func=cmd_doctor)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    cfg = load_config()
    try:
        return args.func(args, cfg)
    except KeyboardInterrupt:
        return 130
    except Exception as e:
        print(f"knowme: error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
