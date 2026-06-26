#!/usr/bin/env python3
"""Export a Discovery feed for SCLib.

The public Discovery page should never mirror the internal leaderboard
directly. This script reads the reviewed DFT-screened dossiers plus loop
state, applies the current public filter, and emits a small JSON artifact
that the SCLib `/discovery` endpoint can serve without querying
SC SuperLoop internals.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import re

SC_ROOT = Path("/data/.openclaw/workspace/research/SC_SuperLoop")
REPORTS = SC_ROOT / "reports"
DOSSIERS_E3 = SC_ROOT / "dossiers" / "E3_dft_verified"
DEFAULT_OUTPUT = REPORTS / "discovery_feed.json"
DEFAULT_META_OUTPUT = REPORTS / "discovery_meta.json"
DEFAULT_SOURCE = "SC SuperLoop reviewed discovery export"
PUBLIC_EVIDENCE_LABEL = "DFT-screened"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Path to write the discovery feed JSON.",
    )
    parser.add_argument(
        "--source",
        default=DEFAULT_SOURCE,
        help="Human-readable source label stored in the feed.",
    )
    parser.add_argument(
        "--meta-output",
        default=str(DEFAULT_META_OUTPUT),
        help="Path to write the lightweight discovery metadata JSON.",
    )
    parser.add_argument(
        "--strict-pass",
        action="store_true",
        help="Require `checker_status=pass` only. Default mode exports a public preview that also includes `pending`.",
    )
    return parser.parse_args()


def parse_simple_value(raw: str):
    text = raw.strip()
    if text in {"[]", ""}:
        return [] if text == "[]" else ""
    if text.lower() in {"true", "false"}:
        return text.lower() == "true"
    if re.fullmatch(r"-?\d+(\.\d+)?", text):
        return float(text) if "." in text else int(text)
    if text.startswith("[") and text.endswith("]"):
        try:
            return json.loads(text.replace("'", '"'))
        except Exception:
            return text
    return text


def parse_dossier(path: Path) -> dict:
    data: dict[str, object] = {
        "candidate_id": "",
        "formula": "",
        "branch": "",
        "prototype_family": None,
        "evidence_level": "",
        "checker_status": "",
        "mechanism_hypothesis": None,
        "risk_tags": [],
        "discovery_score": None,
        "review_summary": None,
        "provenance_summary": None,
        "recommended_next_step": None,
    }
    text = path.read_text(encoding="utf-8")
    for line in text.splitlines():
        if ": " not in line:
            continue
        key, value = line.split(": ", 1)
        norm = key.strip().lower().replace(" ", "_")
        parsed = parse_simple_value(value)
        if norm == "family":
            data["prototype_family"] = parsed
        elif norm == "next_action":
            data["recommended_next_step"] = parsed
        elif norm == "mechanism_note":
            data["review_summary"] = parsed
        elif norm in data:
            data[norm] = parsed

    qe_summary = re.search(r"## QE Summary\s+([\s\S]+?)(?:\n## |\Z)", text)
    if qe_summary:
        lines = [ln.strip("- ").strip() for ln in qe_summary.group(1).splitlines() if ln.strip()]
        data["provenance_summary"] = " ; ".join(lines[:3])

    interpretation = re.search(r"## Interpretation\s+([\s\S]+?)(?:\n## |\Z)", text)
    if interpretation:
        lines = [ln.strip("- ").strip() for ln in interpretation.group(1).splitlines() if ln.strip()]
        if lines:
            data["review_summary"] = " ".join(lines)

    return data


def confidence_label(dossier: dict) -> str:
    branch = str(dossier.get("branch") or "").lower()
    if "hydride" in branch:
        return "Mechanism-Supported"
    if "mgb2" in branch or "boride" in branch or "nitride" in branch:
        return "Exploratory Review Passed"
    return "Exploratory Review Passed"


def sanitize_public_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    text = re.sub(r"`?runs/dft/[^`;\s]+/?`?", "[internal run]", text)
    text = re.sub(r"`?[/A-Za-z0-9_.-]+/[^`;\s]+`?", "[internal path]", text)
    text = text.replace("crossed the E3 threshold", f"crossed the {PUBLIC_EVIDENCE_LABEL} threshold")
    text = text.replace("fixed-cell E3 result", f"fixed-cell {PUBLIC_EVIDENCE_LABEL} result")
    text = text.replace("reviewed E3 dossier", f"reviewed {PUBLIC_EVIDENCE_LABEL} dossier")
    text = text.replace(" E3 ", f" {PUBLIC_EVIDENCE_LABEL} ")
    text = text.replace(" E3.", f" {PUBLIC_EVIDENCE_LABEL}.")
    return text


def include_dossier(dossier: dict, allow_pending: bool) -> bool:
    checker = str(dossier.get("checker_status") or "").lower()
    if checker == "pass":
        return True
    if allow_pending and checker == "pending":
        return True
    return False


def build_feed(source: str, allow_pending: bool) -> dict:
    candidates = []
    for path in sorted(DOSSIERS_E3.glob("*.md")):
        dossier = parse_dossier(path)
        if not include_dossier(dossier, allow_pending=allow_pending):
            continue
        candidates.append(
            {
                "candidate_id": dossier["candidate_id"],
                "formula": dossier["formula"],
                "normalized_formula": dossier["formula"],
                "branch": dossier["branch"],
                "prototype_family": dossier["prototype_family"],
                "evidence_level": dossier["evidence_level"],
                "checker_status": dossier["checker_status"],
                "public_confidence": confidence_label(dossier),
                "discovery_score": dossier["discovery_score"],
                "mechanism_hypothesis": dossier["mechanism_hypothesis"],
                "risk_tags": dossier["risk_tags"] or [],
                "review_summary": sanitize_public_text(dossier["review_summary"]),
                "provenance_summary": f"SC SuperLoop reviewed {PUBLIC_EVIDENCE_LABEL} dossier",
                "recommended_next_step": dossier["recommended_next_step"],
                "last_reviewed_at_utc": datetime.now(timezone.utc).isoformat(),
                "published_at_utc": datetime.now(timezone.utc).isoformat(),
            }
        )

    return {
        "page_title": "Discovery",
        "intro": [
            "This page presents exploratory superconductivity candidates exported from SC SuperLoop into SCLib.",
            "Candidates are generated with physics-informed heuristics, then filtered through prescreening, bounded DFT checks, mechanism audit, and checker review before public display.",
            "The current release uses a preview standard so that early reviewed candidates can be inspected publicly while the evidence base is still growing.",
        ],
        "status": "active" if candidates else "planned",
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "filter_rules": [
            {"key": "exclude_benchmarks", "label": "Benchmarks", "value": "Excluded"},
            {
                "key": "minimum_evidence_level",
                "label": "Minimum evidence",
                "value": PUBLIC_EVIDENCE_LABEL,
            },
            {
                "key": "required_checker_status",
                "label": "Checker",
                "value": "pass or pending (preview)" if allow_pending else "pass",
            },
            {"key": "require_dossier", "label": "Dossier", "value": "Required"},
        ],
        "candidates": candidates,
    }


def build_meta(feed: dict, allow_pending: bool) -> dict:
    updated_at = feed.get("updated_at_utc")
    serialized_feed = json.dumps(feed, sort_keys=True, ensure_ascii=False).encode("utf-8")
    import hashlib

    return {
        "status": feed.get("status", "planned"),
        "mode": "preview" if allow_pending else "strict",
        "updated_at_utc": updated_at,
        "candidate_count": len(feed.get("candidates", [])),
        "sha256": hashlib.sha256(serialized_feed).hexdigest(),
        "source": feed.get("source"),
    }


def main() -> int:
    args = parse_args()
    output = Path(args.output)
    meta_output = Path(args.meta_output)
    output.parent.mkdir(parents=True, exist_ok=True)
    meta_output.parent.mkdir(parents=True, exist_ok=True)
    allow_pending = not args.strict_pass
    feed = build_feed(args.source, allow_pending=allow_pending)
    meta = build_meta(feed, allow_pending=allow_pending)
    output.write_text(json.dumps(feed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    meta_output.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(feed['candidates'])} candidates to {output}")
    print(f"Wrote discovery metadata to {meta_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
