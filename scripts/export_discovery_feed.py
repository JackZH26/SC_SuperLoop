#!/usr/bin/env python3
"""Export a Discovery feed for SCLib.

The public Discovery page should never mirror the internal leaderboard
directly. This script now exports the credible-superconductor corpus used by
SC SuperLoop: a mixed registry of literature-confirmed references,
benchmark-adjacent controls, and loop-verified DFT-screened records.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
import re

from lane_registry import infer_condition_class, infer_required_condition_vector, lane_metadata_for

SC_ROOT = Path("/data/.openclaw/workspace/research/SC_SuperLoop")
REPORTS = SC_ROOT / "reports"
DOSSIERS_E3 = SC_ROOT / "dossiers" / "E3_dft_verified"
CORPUS_REGISTRY = SC_ROOT / "knowledge" / "credible_superconductors.jsonl"
DEFAULT_OUTPUT = REPORTS / "discovery_feed.json"
DEFAULT_META_OUTPUT = REPORTS / "discovery_meta.json"
AUDIT_SCRIPT = SC_ROOT / "scripts" / "audit_discovery_feed.py"
DEFAULT_SOURCE = "SC SuperLoop credible superconductors export"
PUBLIC_EVIDENCE_LABEL = "DFT-screened"
KNOWN_REFERENCE_ROLES = {"reference_anchor", "mechanism_anchor"}
KNOWN_BASELINE_ROLES = {"benchmark_control"}
LEAD_ROLES = {"exploratory_candidate", "conditional_candidate"}
EPC_LANES = {"conventional", "elemental", "mgb2_diboride", "borocarbide", "hydride"}
CORRELATED_LANES = {"cuprate", "iron_based", "nickelate", "heavy_fermion", "kagome"}
CONDITIONAL_LANES = {"chalcogenide", "frontier_first_principles"}


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
        help="Require `checker_status=pass` only. Default mode exports a preview feed, but the public wording should still treat `pending` and `revise` as internal review states.",
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


def load_corpus_registry() -> list[dict]:
    if not CORPUS_REGISTRY.exists():
        return []
    rows = []
    for line in CORPUS_REGISTRY.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def stable_public_candidate_id(record: dict) -> str:
    payload = "|".join(
        [
            str(record.get("record_role") or ""),
            str(record.get("normalized_formula") or record.get("formula") or ""),
            str(record.get("branch_or_family") or ""),
            str(record.get("phase_or_condition_id") or ""),
        ]
    )
    digest = hashlib.sha1(payload.encode("utf-8")).hexdigest()[:10]
    formula_slug = slugify(str(record.get("formula") or "candidate")) or "candidate"
    branch_slug = slugify(str(record.get("branch_or_family") or "misc")) or "misc"
    return f"disc-{formula_slug}-{branch_slug}-{digest}"


def display_class(record: dict) -> str:
    role = str(record.get("record_role") or "")
    condition = str(record.get("condition_class") or "")
    if role in KNOWN_REFERENCE_ROLES:
        return "known_reference"
    if role in KNOWN_BASELINE_ROLES:
        return "benchmark"
    if role == "negative_control":
        return "negative_control"
    if condition == "parent_state_comparator":
        return "parent_comparator"
    if role == "conditional_candidate":
        return "conditional_candidate"
    if role == "mechanism_anchor":
        return "mechanism_anchor"
    return "dft_screened_lead"


def taxonomy_bucket(record: dict) -> str:
    role = str(record.get("record_role") or "")
    novelty = str(record.get("novelty_class") or "")
    if role in KNOWN_REFERENCE_ROLES or novelty in {"known_reference", "rediscovery_reference"}:
        return "known_or_rediscovery_reference"
    if role in KNOWN_BASELINE_ROLES:
        return "benchmark_control"
    if role == "negative_control":
        return "negative_control"
    if role == "conditional_candidate":
        return "conditional_or_context_locked"
    if role == "exploratory_candidate":
        return "exploratory_dft_lead"
    return "mixed_registry_record"


def family_gate_stage(record: dict) -> str:
    lane_id = str(record.get("lane_id") or lane_metadata_for(
        str(record.get("branch_or_family") or ""),
        str(record.get("formula") or ""),
        record.get("risk_tags") or [],
    ).get("lane_id") or "")
    role = str(record.get("record_role") or "")
    gate = str(record.get("promotion_gate") or "")
    claim = str(record.get("claim_level") or "")
    if role in KNOWN_REFERENCE_ROLES | KNOWN_BASELINE_ROLES:
        return "literature_or_reference_anchor"
    if role == "negative_control":
        return "negative_control"
    if lane_id in EPC_LANES:
        if "require_literature_source" == gate:
            return "rediscovery_or_reference"
        if "ready_for_next_generation" == gate and claim == "dft_screened_not_tc_claim":
            return "dft_metallic_only"
        if "free_cell" in gate or "structure" in gate:
            return "structure_or_phonon_gate_pending"
        return "epc_conditioning_pending"
    if lane_id in CORRELATED_LANES:
        if "doping" in gate or "context" in gate:
            return "parent_or_condition_comparator"
        return "family_mechanism_comparator"
    if lane_id in CONDITIONAL_LANES:
        return "conditional_context_required"
    return "unclassified_gate_stage"


def confidence_label(record: dict) -> str:
    evidence = str(record.get("evidence_class") or "").lower()
    checker = str(record.get("review_status") or "").lower()
    role = str(record.get("record_role") or "")
    kind = display_class(record)
    if kind == "negative_control":
        return "Negative control"
    if role in KNOWN_REFERENCE_ROLES:
        return "Known reference"
    if role in KNOWN_BASELINE_ROLES:
        if evidence == "literature-confirmed":
            return "Known reference"
        if evidence == "reference":
            return "Reference anchor"
        return "Known baseline"
    if checker == "revise":
        return "Needs revision"
    if checker in {"pass", "verified"}:
        return "Reviewed DFT-screened lead"
    if evidence == "literature-confirmed":
        return "Literature Confirmed"
    if evidence == "reference":
        return "Reference anchor"
    return "DFT-screened lead"


def condition_badges(record: dict) -> list[str]:
    badges: list[str] = []
    role = str(record.get("record_role") or "")
    condition = str(record.get("condition_class") or "")
    required = [str(x) for x in (record.get("required_condition_vector") or [])]
    risk_tags = {str(x) for x in (record.get("risk_tags") or [])}
    if role in KNOWN_REFERENCE_ROLES or role in KNOWN_BASELINE_ROLES:
        badges.append("known superconductor")
    if role == "negative_control":
        badges.append("negative control")
    if condition == "parent_state_comparator":
        badges.append("parent only")
    if "doping" in required:
        badges.append("doping required")
    if "intercalation" in required:
        badges.append("intercalation required")
    if "pressure" in required or "high_pressure_risk" in risk_tags:
        badges.append("high pressure")
    if "interface" in required or "interface_required" in risk_tags:
        badges.append("interface required")
    if "surface_termination_sensitive" in risk_tags:
        badges.append("surface termination sensitive")
    return list(dict.fromkeys(badges))


def calibrated_discovery_score(record: dict) -> float | None:
    base = record.get("discovery_score_public")
    if base is None:
        return None
    score = float(base)
    kind = display_class(record)
    required = [str(x) for x in (record.get("required_condition_vector") or [])]
    if kind in {"known_reference", "benchmark", "negative_control"}:
        return None
    if kind == "parent_comparator":
        score -= 18.0
    elif kind == "conditional_candidate":
        score -= 8.0
    elif len(required) >= 2:
        score -= 4.0
    return round(max(0.0, min(99.0, score)), 1)


ROLE_ORDER = {
    "reference_anchor": 0,
    "mechanism_anchor": 1,
    "benchmark_control": 2,
    "exploratory_candidate": 3,
    "conditional_candidate": 4,
    "negative_control": 5,
    "failed_memory": 6,
}


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


def build_review_summary(record: dict) -> str | None:
    parts: list[str] = []
    context = sanitize_public_text(record.get("superconductivity_context"))
    condition = sanitize_public_text(record.get("condition_note"))
    if context:
        parts.append(context)
    if condition:
        parts.append(condition)
    return " ".join(parts) if parts else None


def build_provenance_summary(record: dict) -> str | None:
    source_type = str(record.get("source_type") or "").strip()
    source_citation = sanitize_public_text(record.get("source_citation"))
    if source_type and source_citation:
        return f"{source_type}: {source_citation}"
    if source_citation:
        return source_citation
    return None


def map_record_to_candidate(record: dict) -> dict:
    record_id = str(record.get("record_id") or "")
    review_status = str(record.get("review_status") or "pending")
    evidence = str(record.get("evidence_class") or "")
    branch = str(record.get("branch_or_family") or "")
    formula = str(record.get("formula") or "")
    risk_tags = record.get("risk_tags") or []
    lane_meta = lane_metadata_for(branch, formula, risk_tags)
    lane_id = str(record.get("lane_id") or lane_meta.get("lane_id") or branch)
    public_id = stable_public_candidate_id(record)
    return {
        "candidate_id": public_id,
        "legacy_candidate_id": record_id,
        "formula": record.get("formula"),
        "normalized_formula": record.get("normalized_formula"),
        "branch": branch or lane_id,
        "lane_id": lane_id,
        "display_class": display_class(record),
        "taxonomy_bucket": taxonomy_bucket(record),
        "family_gate_stage": family_gate_stage(record),
        "condition_badges": condition_badges(record),
        "prototype_family": record.get("material_class"),
        "candidate_layer": record.get("candidate_layer"),
        "candidate_quantity_score": record.get("candidate_quantity_score"),
        "candidate_quality_score": record.get("candidate_quality_score"),
        "entry_block_reason": record.get("entry_block_reason"),
        "upgrade_requirements": record.get("upgrade_requirements") or [],
        "family_ruleset_id": record.get("family_ruleset_id") or lane_meta.get("family_ruleset_id"),
        "validation_recipe_id": record.get("validation_recipe_id") or lane_meta.get("validation_recipe_id"),
        "condition_class": record.get("condition_class") or infer_condition_class(branch, formula, risk_tags),
        "required_condition_vector": record.get("required_condition_vector") or infer_required_condition_vector(branch, formula, risk_tags),
        "evidence_level": evidence,
        "checker_status": review_status,
        "public_confidence": confidence_label(record),
        "record_role": record.get("record_role"),
        "claim_level": record.get("claim_level"),
        "next_action": record.get("next_action"),
        "base_discovery_score": record.get("discovery_score_public"),
        "discovery_score": calibrated_discovery_score(record),
        "mechanism_hypothesis": sanitize_public_text(record.get("mechanism_note")),
        "risk_tags": record.get("risk_tags") or [],
        "review_summary": build_review_summary(record),
        "provenance_summary": build_provenance_summary(record),
        "recommended_next_step": record.get("next_action"),
        "last_reviewed_at_utc": datetime.now(timezone.utc).isoformat(),
        "published_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def include_record(record: dict, allow_pending: bool) -> bool:
    checker = str(record.get("review_status") or "").lower()
    if checker in {"pass", "verified"}:
        return True
    if allow_pending and checker == "pending":
        return True
    if allow_pending and checker == "revise":
        return True
    return False


def build_feed(source: str, allow_pending: bool) -> dict:
    candidates = [
        map_record_to_candidate(record)
        for record in load_corpus_registry()
        if include_record(record, allow_pending=allow_pending)
    ]
    candidates.sort(
        key=lambda c: (
            ROLE_ORDER.get(str(c.get("record_role") or ""), 99),
            str(c.get("formula") or ""),
        )
    )

    return {
        "page_title": "Reviewed Leads and Controls",
        "intro": [
            "This page presents the reviewed SC SuperLoop lead-and-control queue exported into SCLib.",
            "The feed intentionally mixes known references, benchmark controls, parent comparators, conditional candidates, and DFT-screened leads under explicit front-visible labels.",
            "Lane identity, required-condition semantics, and public-facing display classes are preserved so parent systems and known superconductors do not masquerade as equivalent new predictions.",
        ],
        "status": "active" if candidates else "planned",
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "filter_rules": [
            {"key": "credible_corpus", "label": "Corpus", "value": "Literature + reference + DFT-screened"},
            {"key": "lane_system", "label": "Lane system", "value": "12-lane family-aware SC SuperLoop"},
            {
                "key": "minimum_evidence_level",
                "label": "Minimum evidence",
                "value": "Explicit evidence label required",
            },
            {
                "key": "required_checker_status",
                "label": "Checker",
                "value": "verified / pass rows are reviewed; pending and revise remain visible but explicitly labeled"
                if allow_pending
                else "verified or pass",
            },
            {"key": "require_provenance", "label": "Provenance", "value": "Required"},
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
    if AUDIT_SCRIPT.exists():
        proc = subprocess.run(["python3", str(AUDIT_SCRIPT)], check=False)
        if proc.returncode != 0:
            return proc.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
