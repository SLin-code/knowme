"""Auto-detect the environment around a `knowme record` call.

Rationale: we want agents to report *minimally* (intent + outcome + decisions).
Everything mechanical — project name, git branch, cwd, agent kind, session id —
should be inferred, so agents don't have to know how to describe themselves.

All detection is best-effort: if we can't detect something, we return None
and let the record carry a shorter shape. Never crash on detection failures.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path


def _run(cmd: list[str], cwd: str | Path | None = None) -> str | None:
    """Run a subprocess, return stripped stdout or None on any failure."""
    try:
        r = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=2,  # detection must be fast — never block record()
        )
        if r.returncode == 0:
            return r.stdout.strip() or None
    except (subprocess.SubprocessError, OSError):
        pass
    return None


def detect_cwd() -> str:
    """Working directory the agent was in when it invoked us."""
    return os.getcwd()


def detect_project(cwd: str | Path | None = None) -> str | None:
    """Best-effort project name.

    Order of preference:
      1. `git remote get-url origin` basename (most stable)
      2. Nearest ancestor dir containing .git
      3. cwd basename
    """
    cwd = str(cwd or detect_cwd())
    # Try git remote first
    remote = _run(["git", "config", "--get", "remote.origin.url"], cwd=cwd)
    if remote:
        # e.g. git@github.com:user/repo.git or https://.../repo.git or .../repo
        name = remote.rstrip("/").split("/")[-1]
        if name.endswith(".git"):
            name = name[:-4]
        if name:
            return name
    # Walk up looking for a .git dir
    p = Path(cwd)
    for parent in [p, *p.parents]:
        if (parent / ".git").exists():
            return parent.name
    # Fallback: cwd basename
    return p.name or None


def detect_git_branch(cwd: str | Path | None = None) -> str | None:
    return _run(["git", "branch", "--show-current"], cwd=cwd or detect_cwd())


def detect_git_head(cwd: str | Path | None = None) -> str | None:
    """Current commit SHA (short). Useful for downstream 'what did this session change'."""
    return _run(["git", "rev-parse", "--short=12", "HEAD"], cwd=cwd or detect_cwd())


def detect_agent() -> str | None:
    """Which agent invoked us? Env vars are the reliable channel — parent-process
    inspection is fragile across platforms and shells."""
    # Common env markers, in order of preference (most specific first)
    markers = [
        ("KNOWME_AGENT", None),           # explicit override wins
        ("CLAUDECODE", "claude-code"),
        ("CURSOR_TRACE_ID", "cursor"),
        ("CURSOR_AGENT", "cursor"),
        ("CODEX_SESSION_ID", "codex"),
        ("TERM_PROGRAM", None),           # e.g. "vscode" — weak signal, use last
    ]
    for var, label in markers:
        v = os.environ.get(var)
        if v:
            return label or v.lower()
    return None


def detect_session() -> str | None:
    """Session id if the agent exposes one. Useful for stitching multiple records
    from the same conversation together."""
    for var in ("KNOWME_SESSION", "CLAUDE_SESSION_ID", "CODEX_SESSION_ID", "CURSOR_TRACE_ID"):
        v = os.environ.get(var)
        if v:
            return v
    return None


def snapshot(cwd: str | Path | None = None) -> dict:
    """Bundle everything into a dict ready to merge into a record."""
    cwd = str(cwd or detect_cwd())
    return {
        "cwd": cwd,
        "project": detect_project(cwd),
        "git_branch": detect_git_branch(cwd),
        "git_head": detect_git_head(cwd),
        "agent": detect_agent(),
        "session": detect_session(),
    }
