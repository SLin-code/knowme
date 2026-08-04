"""KnowMe config resolution.

Reads ~/.knowme/config.yaml if present, else uses defaults.
Everything is a pure function — no side effects, no globals.

Config precedence (later overrides earlier):
  1. built-in defaults
  2. ~/.knowme/config.yaml
  3. env vars (KNOWME_*)

We intentionally keep config minimal — an inbox tool should be inbox-shaped, not app-shaped.
"""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

DEFAULTS = {
    # Where to write records. Downstream consumers read from the same place.
    "inbox_dir": "~/.knowme/inbox",
    # Sources to auto-scan when `knowme scan` runs.
    # Each is a directory; a matching collector reads *.jsonl files under it.
    "scan_sources": {
        "claude_code": "~/.claude/projects",
        "codex": "~/.codex/sessions",
    },
}


def load() -> dict:
    """Load effective config: defaults + optional YAML + env overrides."""
    cfg = {**DEFAULTS}
    yaml_path = Path.home() / ".knowme" / "config.yaml"
    if yaml_path.exists():
        try:
            import yaml  # optional dependency — only needed if user has a config file
            with yaml_path.open(encoding="utf-8") as f:
                loaded = yaml.safe_load(f) or {}
            _deep_update(cfg, loaded)
        except ImportError:
            # If pyyaml not installed, just use defaults + env — don't crash the CLI.
            pass
    # Env overrides — one-level only, deliberate
    if v := os.environ.get("KNOWME_INBOX_DIR"):
        cfg["inbox_dir"] = v
    # Resolve ~ in paths
    cfg["inbox_dir_abs"] = str(Path(cfg["inbox_dir"]).expanduser())
    return cfg


def _deep_update(base: dict, override: dict) -> None:
    """In-place recursive dict merge — override wins on scalar conflicts."""
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _deep_update(base[k], v)
        else:
            base[k] = v


def inbox_path(cfg: dict, date_str: str | None = None) -> Path:
    """Return the directory where today's (or given date's) records go.
    Creates it if missing."""
    date_str = date_str or datetime.now().strftime("%Y-%m-%d")
    p = Path(cfg["inbox_dir_abs"]) / date_str
    p.mkdir(parents=True, exist_ok=True)
    return p
