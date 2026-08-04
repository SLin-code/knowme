"""KnowMe · Cross-agent activity trace CLI.

KnowMe lets any AI coding agent (Claude Code, Codex, Cursor, others) record
what they did — intent, outcome, decisions, tokens — into a unified per-user
inbox at ~/.knowme/inbox/. Consumers (dashboards, memory systems, personal
knowledge bases) can then read that inbox on their own cadence.

Design principles:
- Agent reports minimally (intent + outcome + decisions).
- CLI auto-detects the rest from the environment (cwd, git, timing).
- Storage is dumb JSONL append; abstraction happens downstream.
- No dependency on any specific consumer.
"""

__version__ = "0.1.0"
