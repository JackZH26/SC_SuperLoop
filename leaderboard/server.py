#!/usr/bin/env python3
"""Serve a paginated SC SuperLoop public discovery registry."""

from __future__ import annotations

import http.server
import json
import math
import urllib.parse
from pathlib import Path

HOST = "0.0.0.0"
PORT = 3088
PAGE_SIZE = 20
ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = Path(__file__).resolve().parent / "index.html"
DISCOVERY_FEED = ROOT / "reports" / "discovery_feed.json"


def load_candidates() -> tuple[list[dict], str]:
    if not DISCOVERY_FEED.exists():
        return [], ""
    payload = json.loads(DISCOVERY_FEED.read_text(encoding="utf-8"))
    records = list(payload.get("candidates") or [])
    records.sort(
        key=lambda r: (
            str(r.get("taxonomy_bucket") or ""),
            -float(r.get("discovery_score") or -999),
            str(r.get("formula") or ""),
        )
    )
    for index, record in enumerate(records, start=1):
        record["rank"] = index
    return records, str(payload.get("updated_at_utc") or "")


def render_index() -> str:
    return TEMPLATE.read_text(encoding="utf-8")


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _json(self, payload: dict, status: int = 200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _html(self, text: str):
        body = text.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path in {"/", "/index.html"}:
            self._html(render_index())
            return
        if parsed.path == "/api/leaderboard":
            qs = urllib.parse.parse_qs(parsed.query)
            page = max(1, int(qs.get("page", ["1"])[0]))
            records, generated = load_candidates()
            total = len(records)
            pages = max(1, math.ceil(total / PAGE_SIZE))
            page = min(page, pages)
            start = (page - 1) * PAGE_SIZE
            end = start + PAGE_SIZE
            payload = {
                "generated": generated,
                "page": page,
                "pageSize": PAGE_SIZE,
                "totalRecords": total,
                "totalPages": pages,
                "dedupeMode": "formula_branch_best_record",
                "records": records[start:end],
            }
            self._json(payload)
            return
        self.send_response(404)
        self.end_headers()


def main():
    server = http.server.ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"SC SuperLoop leaderboard serving on http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
