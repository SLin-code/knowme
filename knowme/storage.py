"""Storage layer for KnowMe records.

Each record is one JSON line appended to ~/.knowme/inbox/YYYY-MM-DD/records.jsonl.
JSONL is chosen because:
- Trivial to append atomically from multiple processes (write is one open+write).
- Trivial for downstream consumers to stream.
- Human-readable when debugging.

We do NOT use a database — an inbox is a queue, not a store.
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from .config import inbox_path


def _atomic_append(fp: Path, line: str) -> None:
    """Append a single line to fp. Uses a lock file so concurrent CLIs from different
    agents don't interleave their writes. Lock is best-effort — on give-up we still
    write (data preservation > perfect ordering)."""
    lock = fp.with_suffix(fp.suffix + ".lock")
    for _ in range(50):  # ~500ms max wait
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            break
        except FileExistsError:
            time.sleep(0.01)
    try:
        with fp.open("a", encoding="utf-8") as f:
            f.write(line)
            if not line.endswith("\n"):
                f.write("\n")
    finally:
        try:
            os.unlink(lock)
        except FileNotFoundError:
            pass


def append_record(cfg: dict, record: dict) -> Path:
    """Append a record to today's inbox. Returns the path written to."""
    record.setdefault("ts", datetime.now(timezone.utc).isoformat())
    record.setdefault("v", 1)  # schema version
    fp = inbox_path(cfg) / "records.jsonl"
    _atomic_append(fp, json.dumps(record, ensure_ascii=False))
    return fp


def read_day(cfg: dict, date_str: str) -> list[dict]:
    """Read all records for a given date. Returns empty list if none."""
    fp = Path(cfg["inbox_dir_abs"]) / date_str / "records.jsonl"
    if not fp.exists():
        return []
    out: list[dict] = []
    with fp.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"knowme: skipping malformed line: {e}", file=sys.stderr)
    return out


def list_dates(cfg: dict) -> list[str]:
    """List all dates that have records, newest first. Returns list of 'YYYY-MM-DD' strings."""
    root = Path(cfg["inbox_dir_abs"])
    if not root.exists():
        return []
    # Directory names ARE the dates; filter to well-formed ones only
    dates = []
    for p in root.iterdir():
        if p.is_dir() and len(p.name) == 10 and p.name[4] == "-" and p.name[7] == "-":
            if (p / "records.jsonl").exists():
                dates.append(p.name)
    return sorted(dates, reverse=True)


def read_range(cfg: dict, since_date: str | None = None, until_date: str | None = None) -> list[dict]:
    """Read records across a date range (inclusive). None = unbounded on that side.
    Records are returned in chronological order (oldest first) by their ts field."""
    all_dates = list_dates(cfg)
    if since_date:
        all_dates = [d for d in all_dates if d >= since_date]
    if until_date:
        all_dates = [d for d in all_dates if d <= until_date]
    records: list[dict] = []
    for d in reversed(all_dates):  # oldest-first for chronological output
        records.extend(read_day(cfg, d))
    return records
