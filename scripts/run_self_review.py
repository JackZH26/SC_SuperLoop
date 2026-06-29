#!/usr/bin/env python3
"""Deterministic bounded self-review for SC SuperLoop cron."""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/data/.openclaw/workspace/research/SC_SuperLoop")
REPORTS = ROOT / "reports"
STRATEGY = REPORTS / "strategy_updates.md"
FAILURES = REPORTS / "failures.md"
QUEUE = REPORTS / "dft_queue_status.md"
LOOP_STATE = REPORTS / "loop_state.md"
DISCOVERY_FEED = REPORTS / "discovery_feed.json"
CORPUS = ROOT / "knowledge" / "credible_superconductors.jsonl"
AUDIT_SCRIPT = ROOT / "scripts" / "audit_discovery_feed.py"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def corpus_count() -> int:
    if not CORPUS.exists():
        return 0
    return sum(1 for line in CORPUS.read_text(encoding="utf-8").splitlines() if line.strip())


def active_anchor(queue_text: str) -> str:
    rows = [
        line for line in queue_text.splitlines()
        if line.startswith("| E0-") or line.startswith("| E1-") or line.startswith("| E2-") or line.startswith("| E3-")
    ]
    if not rows:
        return "unknown"
    cells = [cell.strip() for cell in rows[0].strip("|").split("|")]
    if len(cells) < 6:
        return "unknown"
    return f"{cells[1]} / {cells[2]} / {cells[5]}"


def stale_anchor_reason(loop_text: str) -> str:
    match = re.search(r"Stale anchor reason:\s*`?([A-Za-z0-9_\-]+)`?", loop_text)
    return match.group(1) if match else "unknown"


def append_if_missing(path: Path, block: str) -> None:
    text = read_text(path)
    if block.strip() in text:
        return
    with path.open("a", encoding="utf-8") as handle:
        if text and not text.endswith("\n"):
            handle.write("\n")
        handle.write(block)


def main() -> int:
    queue_text = read_text(QUEUE)
    loop_text = read_text(LOOP_STATE)
    feed = read_json(DISCOVERY_FEED)
    feed_count = len(feed.get("candidates", []))
    corpus_rows = corpus_count()
    anchor = active_anchor(queue_text)
    stale_reason = stale_anchor_reason(loop_text)
    audit_ok = True
    audit_payload = {}
    if AUDIT_SCRIPT.exists():
        proc = subprocess.run(["python3", str(AUDIT_SCRIPT)], capture_output=True, text=True)
        audit_ok = proc.returncode == 0
        try:
            audit_payload = json.loads(proc.stdout.strip() or "{}")
        except Exception:
            audit_payload = {"raw_stdout": proc.stdout.strip(), "raw_stderr": proc.stderr.strip()}

    ok = feed_count == corpus_rows and anchor != "unknown" and audit_ok

    stamp = datetime.now(timezone.utc).isoformat()
    strategy_block = (
        f"\n## Self-review {stamp}\n"
        f"- Active anchor: `{anchor}`\n"
        f"- Discovery feed count: `{feed_count}`\n"
        f"- Corpus row count: `{corpus_rows}`\n"
        f"- Stale-anchor reason: `{stale_reason}`\n"
        f"- Discovery audit: `{audit_payload.get('status', 'unknown')}`\n"
        f"- Verdict: `{'aligned' if ok else 'needs_followup'}`\n"
    )
    append_if_missing(STRATEGY, strategy_block)

    if not ok:
      failure_block = (
          f"\n## Self-review alert {stamp}\n"
          f"- Feed/corpus mismatch or missing active anchor detected.\n"
          f"- Active anchor: `{anchor}`\n"
          f"- Discovery feed count: `{feed_count}` vs corpus `{corpus_rows}`\n"
          f"- Stale-anchor reason: `{stale_reason}`\n"
          f"- Discovery audit: `{audit_payload.get('status', 'unknown')}`\n"
      )
      append_if_missing(FAILURES, failure_block)

    print(json.dumps({
        "active_anchor": anchor,
        "feed_count": feed_count,
        "corpus_count": corpus_rows,
        "stale_anchor_reason": stale_reason,
        "discovery_audit": audit_payload,
        "verdict": "aligned" if ok else "needs_followup",
    }, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
