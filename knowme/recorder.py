"""The `knowme record` command — the primary entry for agent-initiated reporting.

Design contract with agents:
- REQUIRED: --intent (what you set out to do, one line)
- STRONGLY RECOMMENDED: --outcome (what actually happened)
- OPTIONAL: --decisions (comma-separated key decisions), --tokens-in/out, --duration,
  --files (comma-separated files touched), --notes (free text)

Everything else (project, git, agent kind, session, cwd, timestamp) is auto-detected.

The record shape is deliberately loose so agents that only know two fields still
succeed, while agents that know more can enrich the row.

Long-form outcomes / notes can also be piped via stdin — see `knowme record --help`.
"""
from __future__ import annotations

from typing import Any

from . import environment as env
from .storage import append_record


def build_record(
    *,
    intent: str,
    outcome: str | None = None,
    decisions: list[str] | None = None,
    tokens_in: int | None = None,
    tokens_out: int | None = None,
    duration_seconds: int | None = None,
    files: list[str] | None = None,
    notes: str | None = None,
    kind: str = "task",
    agent: str | None = None,
    session: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict:
    """Compose a record from user-provided fields + auto-detected environment.

    Fields set to None are omitted from the record (keeps JSONL tidy).
    `agent`/`session` override env-var detection — agents self-declare who they are.
    """
    rec: dict[str, Any] = {"kind": kind, "intent": intent}
    if outcome:
        rec["outcome"] = outcome
    if decisions:
        rec["decisions"] = decisions
    if tokens_in is not None:
        rec["tokens_in"] = tokens_in
    if tokens_out is not None:
        rec["tokens_out"] = tokens_out
    if duration_seconds is not None:
        rec["duration_s"] = duration_seconds
    if files:
        rec["files"] = files
    if notes:
        rec["notes"] = notes
    if extra:
        rec["extra"] = extra
    # Auto-detected fields go into an "env" sub-object so user data and system data
    # are cleanly separated in the record.
    rec["env"] = env.snapshot(agent=agent, session=session)
    return rec


def record(cfg: dict, **kwargs) -> dict:
    """High-level entry: build the record and persist it."""
    rec = build_record(**kwargs)
    fp = append_record(cfg, rec)
    return {"written_to": str(fp), "record": rec}
