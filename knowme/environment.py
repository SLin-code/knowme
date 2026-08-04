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
    """Which agent invoked us?

    Design principle: agents self-declare who they are.

    KnowMe does NOT hardcode an env-var-to-agent-name mapping — that approach forces
    a KnowMe release for every new agent. Instead:

      1. Preferred: agents pass `--agent <name>` to the CLI (handled at CLI layer).
      2. Fallback: agents set `KNOWME_AGENT=<name>` in their shell before invoking.
      3. Unknown: return None. Downstream can filter by absence.

    Any agent — existing or future — can integrate without KnowMe knowing about it.
    """
    v = os.environ.get("KNOWME_AGENT")
    return v.lower() if v else None


def detect_session() -> str | None:
    """Session id if the agent exposes one. Only reads KNOWME_SESSION —
    same self-declaration principle as detect_agent()."""
    v = os.environ.get("KNOWME_SESSION")
    return v if v else None


def snapshot(
    cwd: str | Path | None = None,
    agent: str | None = None,
    session: str | None = None,
) -> dict:
    """Bundle detected environment into a dict ready to merge into a record.

    Explicit `agent`/`session` (from CLI flags) win over env-var detection —
    self-declaration is the reliable channel; env-var is the fallback.
    """
    cwd = str(cwd or detect_cwd())
    return {
        "cwd": cwd,
        "project": detect_project(cwd),
        "git_branch": detect_git_branch(cwd),
        "git_head": detect_git_head(cwd),
        "agent": agent or detect_agent(),
        "session": session or detect_session(),
    }
