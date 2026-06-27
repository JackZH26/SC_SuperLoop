#!/usr/bin/env python3
"""Build persistent loop state for autonomous SC SuperLoop runs."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Any

SC_ROOT = Path("/data/.openclaw/workspace/research/SC_SuperLoop")
REPORTS = SC_ROOT / "reports"
DOSSIERS_E3 = SC_ROOT / "dossiers" / "E3_dft_verified"
MANIFESTS = SC_ROOT / "candidates"
CORPUS_REGISTRY = SC_ROOT / "knowledge" / "credible_superconductors.jsonl"
LOOP_STATE_JSON = REPORTS / "loop_state.json"
LOOP_STATE_MD = REPORTS / "loop_state.md"
DFT_QUEUE_STATUS = REPORTS / "dft_queue_status.md"
MANIFEST_FUNNEL_STATUS = REPORTS / "manifest_candidate_funnel.md"
UPGRADE_EXECUTION_QUEUE = REPORTS / "upgrade_execution_queue.md"
RUNTIME_STATE_JSON = REPORTS / "superloop_runtime_state.json"
HEALTH_MD = REPORTS / "superloop_health.md"


def latest_manifest() -> Path:
    manifests = sorted(MANIFESTS.glob("*/candidate_manifest_prescreened.jsonl"))
    if not manifests:
        raise FileNotFoundError("No candidate_manifest_prescreened.jsonl found.")
    return manifests[-1]


def parse_dossier(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    data: dict[str, str] = {"path": str(path.relative_to(SC_ROOT))}
    simple_keys = {
        "candidate_id",
        "formula",
        "branch",
        "evidence_level",
        "checker_status",
        "next_action",
        "mechanism_note",
    }
    for line in text.splitlines():
        if ": " not in line:
            continue
        key, value = line.split(": ", 1)
        key = key.strip().lower().replace(" ", "_")
        if key in simple_keys:
            data[key] = value.strip()
    for line in text.splitlines():
        if line.startswith("- SCF total energy:"):
            data["qe_total_energy_ry"] = line.split(":", 1)[1].strip()
        elif line.startswith("- DOS(E_F):"):
            data["dos_at_ef"] = line.split(":", 1)[1].strip()
    interp = re.search(r"## Interpretation\s+([\s\S]+)$", text)
    if interp:
        lines = [ln.strip("- ").strip() for ln in interp.group(1).splitlines() if ln.strip()]
        data["interpretation"] = " ".join(lines)
    return data


def load_e3_dossiers() -> dict[str, dict[str, str]]:
    dossiers = {}
    if DOSSIERS_E3.exists():
        for path in DOSSIERS_E3.glob("*.md"):
            d = parse_dossier(path)
            cid = d.get("candidate_id")
            if cid:
                dossiers[cid] = d
    return dossiers


def load_corpus_registry() -> dict[str, dict]:
    if not CORPUS_REGISTRY.exists():
        return {}
    rows = {}
    for line in CORPUS_REGISTRY.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        rows[row.get("formula", "")] = row
    return rows


def manifest_family_ruleset_id(branch: str) -> str:
    mapping = {
        "AlB2_MgB2_boride": "ruleset_diboride_mechanism_preserving_v1",
        "AlTiPbW_exploratory": "ruleset_transition_metal_binary_v1",
        "MXene_2D": "ruleset_mxene_layered_carbide_v1",
        "iron_based_extrapolation": "ruleset_iron_based_mechanism_preserving_v1",
        "cuprate_extrapolation": "ruleset_cuprate_condition_preserving_v1",
        "layered_nitride_halonitride": "ruleset_layered_nitride_intercalation_v1",
        "fulleride_molecular": "ruleset_fulleride_condition_preserving_v1",
        "graphite_intercalation": "ruleset_intercalation_layered_v1",
    }
    return mapping.get(branch, "ruleset_manifest_prescreen_generic_v1")


def assign_manifest_funnel_fields(row: dict) -> dict:
    formula = row.get("formula", "")
    branch = row.get("branch", "")
    risk_tags = set(row.get("risk_tags", []))
    chgnet_reason = row.get("chgnet_reason")
    dft_status = row.get("dft_status")
    discovery = float(row.get("discovery_score") or 0.0)
    prescreen = float(row.get("prescreen_score") or 0.0)

    quantity = max(40.0, min(99.0, round(discovery, 1)))
    quality = max(20.0, min(90.0, round(0.55 * discovery + 0.35 * prescreen - 10.0, 1)))
    candidate_layer = "broad"
    entry_block_reason = None
    upgrade_requirements: list[str] = []

    if chgnet_reason == "no_structure_proxy":
        candidate_layer = "broad"
        entry_block_reason = "no_structure_proxy"
        upgrade_requirements = ["attach_verified_structure_proxy", "prototype_verification"]
        quality -= 14.0
    elif chgnet_reason == "prototype_proxy":
        candidate_layer = "structured"
        entry_block_reason = "proxy_only"
        upgrade_requirements = ["structure_specific_validation", "chgnet_or_relax_followup"]
        quality += 4.0

    if dft_status in {"scf_completed", "relax_completed", "completed"}:
        candidate_layer = "promotion_ready"
        entry_block_reason = None
        upgrade_requirements = ["bounded_dft_followup" if dft_status != "completed" else "checker_review"]
        quality += 10.0

    if formula == "Mo2C":
        candidate_layer = "broad"
        entry_block_reason = "no_structure_proxy"
        quantity = max(quantity, 84.0)
        quality = max(quality, 46.0)
        upgrade_requirements = ["attach_verified_structure_proxy", "prototype_verification", "condition_scope_check"]

    if formula == "LiBC":
        quantity = max(quantity, 82.0)
        quality = max(quality, 58.0)
        if candidate_layer == "structured":
            upgrade_requirements.append("encode_hole_doping_path")
        else:
            upgrade_requirements = list(dict.fromkeys(upgrade_requirements + ["encode_hole_doping_path"]))

    if formula in {"SrTiO3", "KTaO3", "BaTiO3", "TiO2", "CaTiO3"}:
        quantity = max(quantity, 72.0)
        quality = max(quality - 4.0, 38.0)
        if "interface_required" in risk_tags or "carrier_density_sensitive" in risk_tags:
            upgrade_requirements = list(dict.fromkeys(upgrade_requirements + ["encode_doping_or_interface_condition"]))

    if "surface_termination_sensitive" in risk_tags:
        quality -= 6.0
        upgrade_requirements = list(dict.fromkeys(upgrade_requirements + ["termination_scope_check"]))
    if "carrier_density_sensitive" in risk_tags:
        quality -= 4.0
    if "oxygen_vacancy_sensitive" in risk_tags:
        quality -= 4.0
    if "interface_required" in risk_tags:
        quality -= 5.0
    if "low_Tc_risk" in risk_tags:
        quality -= 5.0

    quality = max(0.0, min(99.0, round(quality, 1)))
    quantity = max(0.0, min(99.0, round(quantity, 1)))
    upgrade_requirements = list(dict.fromkeys(upgrade_requirements))
    if not upgrade_requirements:
        upgrade_requirements = ["preserve_branch_constraints"]

    return {
        "candidate_layer": candidate_layer,
        "candidate_quantity_score": quantity,
        "candidate_quality_score": quality,
        "entry_block_reason": entry_block_reason,
        "upgrade_requirements": upgrade_requirements,
        "family_ruleset_id": manifest_family_ruleset_id(branch),
    }


def parse_active_queue_anchor() -> dict[str, str]:
    if not DFT_QUEUE_STATUS.exists():
        return {}
    text = DFT_QUEUE_STATUS.read_text(encoding="utf-8")
    lines = text.splitlines()
    in_active = False
    for line in lines:
        if line.startswith("## Active This Cycle"):
            in_active = True
            continue
        if not in_active:
            continue
        if line.startswith("## "):
            break
        if not line.startswith("|") or line.startswith("| Candidate"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 6:
            continue
        if not cells[0] or cells[0] == "-" or cells[0] == "-----------":
            continue
        return {
            "candidate_id": cells[0],
            "formula": cells[1],
            "branch": cells[2],
            "verified_step": cells[3],
            "next_action": cells[5],
        }
    return {}


def load_runtime_state() -> dict[str, Any]:
    if not RUNTIME_STATE_JSON.exists():
        return {}
    try:
        return json.loads(RUNTIME_STATE_JSON.read_text(encoding="utf-8"))
    except Exception:
        return {}


def parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def anchor_signature(anchor: dict[str, Any]) -> str:
    if not anchor:
        return ""
    return "|".join(
        [
            str(anchor.get("candidate_id", "")),
            str(anchor.get("formula", "")),
            str(anchor.get("verified_step", "")),
            str(anchor.get("next_action", "")),
        ]
    )


def select_best_record(existing: dict | None, candidate: dict) -> dict:
    if existing is None:
        candidate["occurrence_count"] = 1
        candidate["merged_candidate_ids"] = [candidate["candidate_id"]]
        return candidate

    dft_rank = {
        "completed": 3,
        "relax_completed": 2,
        "scf_completed": 1,
        "not_started": 0,
    }

    priority = lambda rec: (
        {"E4": 4, "E3": 3, "E2": 2, "E1": 1, "E0": 0}.get(rec.get("evidence_level", "E0"), 0),
        dft_rank.get(rec.get("dft_status", ""), 0),
        float(rec.get("discovery_score") or -999),
        float(rec.get("prescreen_score") or -999),
        rec.get("candidate_id", ""),
    )
    chosen = existing if priority(existing) >= priority(candidate) else candidate
    chosen["occurrence_count"] = existing.get("occurrence_count", 1) + 1
    chosen["merged_candidate_ids"] = existing.get("merged_candidate_ids", [existing["candidate_id"]]) + [
        candidate["candidate_id"]
    ]
    return chosen


def candidate_gate_status(formula: str, corpus: dict[str, dict]) -> tuple[bool, str | None]:
    row = corpus.get(formula)
    if not row:
        return True, None
    role = row.get("record_role")
    gate = row.get("promotion_gate")
    layer = row.get("candidate_layer")
    block_reason = row.get("entry_block_reason")
    if role in {"negative_control", "benchmark_control", "reference_anchor", "mechanism_anchor"}:
        return False, f"classified_as_{role}"
    if gate in {"no_promotion", "require_literature_source"}:
        return False, f"promotion_gate_{gate}"
    if layer == "broad":
        return False, block_reason or "candidate_layer_broad"
    return True, None


def loop_priority_score(row: dict[str, Any], corpus: dict[str, dict]) -> float:
    formula = str(row.get("formula", ""))
    branch = str(row.get("branch", ""))
    discovery = float(row.get("discovery_score") or 0.0)
    prescreen = float(row.get("prescreen_score") or 0.0)
    layer = str(row.get("candidate_layer") or "")
    risk_tags = set(row.get("risk_tags", []))
    corpus_row = corpus.get(formula, {})
    role = str(corpus_row.get("record_role") or "")

    score = 0.65 * discovery + 0.20 * prescreen

    if branch == "cuprate_extrapolation":
        score += 18.0
    elif branch == "MXene_2D":
        score += 8.0
    elif branch == "AlB2_MgB2_boride":
        score += 4.0

    if formula in {"Nd0.8Sr0.2NiO2", "NdNiO2", "PrNiO2", "Ba2NiO2F2", "La2PdO4", "LaPdO2"}:
        score += 18.0
    if formula in {"NbB2", "MoB2", "TiB2", "ZrB2", "WB2"}:
        score -= 8.0

    if layer == "promotion_ready":
        score += 15.0
    elif layer == "structured":
        score += 8.0
    elif layer == "broad":
        score -= 6.0

    if role in {"negative_control", "benchmark_control", "reference_anchor", "mechanism_anchor"}:
        score -= 50.0

    if "wider_band_risk" in risk_tags:
        score -= 6.0
    if "ligand_field_sensitive" in risk_tags:
        score += 4.0
    if "carrier_density_sensitive" in risk_tags:
        score += 2.0
    if "conjecture_only" in risk_tags:
        score -= 1.5

    return round(score, 1)


def anchor_watchdog_status(
    active_anchor: dict[str, str],
    runtime_state: dict[str, Any],
    now: datetime,
) -> tuple[bool, str | None, dict[str, Any]]:
    if not active_anchor:
        return False, None, {"anchor_streak_cycles": 0, "anchor_age_hours": 0.0}

    sig = anchor_signature(active_anchor)
    prev_sig = runtime_state.get("anchor_signature", "")
    prev_streak = int(runtime_state.get("anchor_streak_cycles", 0) or 0)
    streak = prev_streak + 1 if sig and sig == prev_sig else 1

    last_adv = parse_iso_datetime(runtime_state.get("last_substantive_advance_at"))
    if last_adv is None:
        last_adv = now
    age_hours = max(0.0, round((now - last_adv).total_seconds() / 3600.0, 2))

    step = str(active_anchor.get("verified_step", ""))
    stale = step in {"not_started", "prescreen"} and (streak >= 4 or age_hours >= 2.0)
    reason = None
    if stale:
        reason = "stale_anchor_cycle_limit" if streak >= 4 else "stale_anchor_time_limit"

    return stale, reason, {"anchor_streak_cycles": streak, "anchor_age_hours": age_hours}


def select_resume_anchor(
    active_anchor: dict[str, str],
    ready_qe: list[dict],
    corpus: dict[str, dict],
    runtime_state: dict[str, Any],
    now: datetime,
) -> tuple[dict[str, str], str]:
    stale, stale_reason, _watchdog = anchor_watchdog_status(active_anchor, runtime_state, now)
    if active_anchor:
        allowed, reason = candidate_gate_status(active_anchor.get("formula", ""), corpus)
        if stale:
            reason = stale_reason or "stale_active_anchor"
        if allowed and not stale:
            return active_anchor, "active_anchor_still_eligible"
    else:
        reason = "missing_active_anchor"

    for row in ready_qe:
        allowed, blocked_reason = candidate_gate_status(row.get("formula", ""), corpus)
        if not allowed:
            continue
        return (
            {
                "candidate_id": row.get("candidate_id", ""),
                "formula": row.get("formula", ""),
                "branch": row.get("branch", ""),
                "verified_step": row.get("dft_status", "prescreen"),
                "next_action": row.get("next_action", "prescreen"),
                "reseeded_from": active_anchor.get("candidate_id", "") if active_anchor else "",
                "reseed_reason": reason or blocked_reason or "reseeded_to_next_eligible_lane",
            },
            "reseeded_to_next_eligible_lane",
        )

    if active_anchor:
        blocked = dict(active_anchor)
        blocked["reseed_reason"] = reason or "blocked_active_anchor"
        return blocked, "no_eligible_reseed_found"
    return {}, "no_anchor_available"


def build_state() -> dict:
    manifest = latest_manifest()
    dossiers = load_e3_dossiers()
    corpus = load_corpus_registry()
    runtime_state = load_runtime_state()
    now = datetime.now(timezone.utc)
    active_anchor = parse_active_queue_anchor()
    raw_rows = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()]

    deduped: dict[tuple[str, str], dict] = {}
    branch_counts = Counter()
    evidence_counts = Counter()
    dft_status_counts = Counter()
    chgnet_covered = 0
    next_action_counts = Counter()
    ready_qe = []
    high_value_candidates = []

    for row in raw_rows:
        if row.get("chgnet_ready"):
            chgnet_covered += 1
        branch_counts[row["branch"]] += 1
        evidence_counts[row.get("evidence_level", "E0")] += 1
        dft_status_counts[row.get("dft_status", "unknown")] += 1
        next_action_counts[row.get("next_action", "unknown")] += 1

        merged = {
            "candidate_id": row["candidate_id"],
            "formula": row.get("formula", ""),
            "branch": row.get("branch", ""),
            "evidence_level": row.get("evidence_level", "E0"),
            "prescreen_score": row.get("prescreen_score"),
            "discovery_score": row.get("discovery_score"),
            "dft_status": row.get("dft_status", ""),
            "phonon_status": row.get("phonon_status", ""),
            "checker_status": row.get("checker_status", ""),
            "next_action": row.get("next_action", ""),
            "risk_tags": row.get("risk_tags", []),
            "mechanism_hypothesis": row.get("mechanism_hypothesis", ""),
            "chgnet_force_max_ev_ang": row.get("chgnet_force_max_ev_ang"),
            "chgnet_reason": row.get("chgnet_reason"),
        }
        if row["candidate_id"] in dossiers:
            dossier = dossiers[row["candidate_id"]]
            merged["dossier"] = dossier
            # Persisted E3 dossiers are the verified source of truth when the
            # prescreen manifest still carries stale queue-era metadata.
            merged["evidence_level"] = dossier.get("evidence_level", merged["evidence_level"])
            merged["checker_status"] = dossier.get("checker_status", merged["checker_status"])
            merged["next_action"] = dossier.get("next_action", merged["next_action"])
            merged["dft_status"] = "completed"
        key = (merged["formula"], merged["branch"])
        deduped[key] = select_best_record(deduped.get(key), merged)

    unique_rows = list(deduped.values())
    unique_rows.sort(
        key=lambda r: (
            -{"E4": 4, "E3": 3, "E2": 2, "E1": 1, "E0": 0}.get(r.get("evidence_level", "E0"), 0),
            -(r.get("discovery_score") or -999),
            -(r.get("prescreen_score") or -999),
            r.get("candidate_id", ""),
        )
    )

    for row in unique_rows:
        corpus_row = corpus.get(row.get("formula", ""))
        if corpus_row:
            row["candidate_layer"] = corpus_row.get("candidate_layer")
            row["candidate_quantity_score"] = corpus_row.get("candidate_quantity_score")
            row["candidate_quality_score"] = corpus_row.get("candidate_quality_score")
            row["entry_block_reason"] = corpus_row.get("entry_block_reason")
            row["upgrade_requirements"] = corpus_row.get("upgrade_requirements", [])
            row["family_ruleset_id"] = corpus_row.get("family_ruleset_id")
        else:
            row.update(assign_manifest_funnel_fields(row))
        if row.get("dft_status") != "completed" and row.get("evidence_level") == "E1":
            if row.get("branch") in {
                "AlB2_MgB2_boride",
                "AlTiPbW_exploratory",
                "MXene_2D",
                "cuprate_extrapolation",
            }:
                ready_qe.append(row)
        if row.get("evidence_level") in {"E3", "E1"}:
            high_value_candidates.append(row)

    for row in ready_qe:
        row["loop_priority_score"] = loop_priority_score(row, corpus)
    ready_qe.sort(
        key=lambda row: (
            -(row.get("loop_priority_score") or -999.0),
            -(row.get("candidate_quality_score") or -999.0),
            -(row.get("discovery_score") or -999.0),
            row.get("formula", ""),
        )
    )

    blockers = []
    for cid, dossier in dossiers.items():
        if dossier.get("checker_status") == "revise":
            blockers.append(
                {
                    "candidate_id": cid,
                    "formula": dossier.get("formula", ""),
                    "branch": dossier.get("branch", ""),
                    "issue": dossier.get("next_action", "review_needed"),
                }
            )

    resume_anchor, resume_status = select_resume_anchor(active_anchor, ready_qe, corpus, runtime_state, now)

    top_ready = ready_qe[0] if ready_qe else {}
    public_corpus_count = len(corpus)
    completed_e3_count = len(dossiers)
    active_sig = anchor_signature(resume_anchor)
    prev_anchor_sig = str(runtime_state.get("anchor_signature", ""))
    prev_public_corpus_count = int(runtime_state.get("public_corpus_count", public_corpus_count) or public_corpus_count)
    prev_completed_e3_count = int(runtime_state.get("completed_e3_count", completed_e3_count) or completed_e3_count)
    prev_top_ready_formula = str(runtime_state.get("top_ready_formula", ""))
    progress_kinds: list[str] = []
    if public_corpus_count > prev_public_corpus_count:
        progress_kinds.append("advance_corpus")
    if completed_e3_count > prev_completed_e3_count:
        progress_kinds.append("advance_compute")
    if top_ready and top_ready.get("formula") and top_ready.get("formula") != prev_top_ready_formula:
        progress_kinds.append("advance_queue_priority")
    if active_sig and active_sig != prev_anchor_sig and resume_status != "active_anchor_still_eligible":
        progress_kinds.append("advance_reseed")

    last_substantive_advance_at = runtime_state.get("last_substantive_advance_at")
    if progress_kinds or not last_substantive_advance_at:
        last_substantive_advance_at = now.isoformat()
        cycles_since_advance = 0
        maintenance_streak = 0
    else:
        cycles_since_advance = int(runtime_state.get("cycles_since_substantive_advance", 0) or 0) + 1
        maintenance_streak = int(runtime_state.get("maintenance_only_streak", 0) or 0) + 1

    stale, stale_reason, watchdog_metrics = anchor_watchdog_status(resume_anchor, runtime_state, now)
    last_adv_dt = parse_iso_datetime(last_substantive_advance_at) or now
    hours_since_advance = round(max(0.0, (now - last_adv_dt).total_seconds() / 3600.0), 2)

    state = {
        "updated_at_utc": now.isoformat(),
        "manifest_path": str(manifest.relative_to(SC_ROOT)),
        "raw_candidate_count": len(raw_rows),
        "unique_material_count": len(unique_rows),
        "chgnet_covered_count": chgnet_covered,
        "counts": {
            "branch": dict(branch_counts),
            "evidence_level": dict(evidence_counts),
            "dft_status": dict(dft_status_counts),
            "next_action": dict(next_action_counts),
        },
        "completed_e3_candidates": [
            {
                "candidate_id": cid,
                "formula": d.get("formula", ""),
                "branch": d.get("branch", ""),
                "checker_status": d.get("checker_status", ""),
                "next_action": d.get("next_action", ""),
                "interpretation": d.get("interpretation", ""),
            }
            for cid, d in sorted(dossiers.items())
        ],
        "blockers": blockers,
        "ready_qe_candidates": ready_qe[:12],
        "high_value_candidates": high_value_candidates[:20],
        "manifest_funnel": {
            "broad": [row for row in unique_rows if row.get("candidate_layer") == "broad"][:40],
            "structured": [row for row in unique_rows if row.get("candidate_layer") == "structured"][:40],
            "promotion_ready": [row for row in unique_rows if row.get("candidate_layer") == "promotion_ready"][:40],
        },
        "loop_assessment": {
            "current_focus": "advance evidence quality over candidate volume",
            "next_round_priority": [
                "Force the loop to expire stale anchors instead of allowing indefinite prescreen refresh",
                "Prioritize mainline charge-transfer candidates when they are promotion-ready and gate-eligible",
                "Increase dossier evidence density for E3 candidates before promoting phonon work",
                "Record failures and review-needed cases before retrying alternate prototypes",
            ],
            "autonomy_gaps": [
                "phonon/EPC layer still sparse",
                "external public leaderboard publishing remains less stable than local state",
                "maker-checker separation is stronger in code flow than in scientific claims",
                "stagnation watchdog still needs a real cycle executor to trigger fallback actions automatically",
            ],
        },
        "resume_anchor": resume_anchor,
        "resume_anchor_status": resume_status,
        "watchdog": {
            "last_substantive_advance_at": last_substantive_advance_at,
            "hours_since_last_substantive_advance": hours_since_advance,
            "cycles_since_substantive_advance": cycles_since_advance,
            "maintenance_only_streak": maintenance_streak,
            "anchor_streak_cycles": watchdog_metrics.get("anchor_streak_cycles", 0),
            "anchor_age_hours": watchdog_metrics.get("anchor_age_hours", 0.0),
            "stale_anchor": stale,
            "stale_anchor_reason": stale_reason,
            "public_corpus_count": public_corpus_count,
            "completed_e3_count": completed_e3_count,
            "top_ready_formula": top_ready.get("formula", ""),
            "progress_kinds": progress_kinds,
        },
    }
    return state


def write_dft_queue_status(state: dict, corpus: dict[str, dict]) -> None:
    generated_utc = state.get("updated_at_utc") or datetime.now(timezone.utc).isoformat()
    lines = [
        "# DFT Queue Status",
        "",
        f"Generated: {generated_utc.split('T', 1)[0]}",
        "Queue policy: prioritize only lanes that remain eligible after corpus classification and gate checks.",
        "",
        "## Active This Cycle",
        "",
        "| Candidate | Formula | Branch | Verified Step | Result | Next Action |",
        "|-----------|---------|--------|---------------|--------|-------------|",
    ]
    anchor = state.get("resume_anchor") or {}
    if anchor:
        formula = anchor.get("formula", "")
        row = corpus.get(formula, {})
        result = row.get("record_role", state.get("resume_anchor_status", "active"))
        lines.append(
            f"| {anchor.get('candidate_id','-')} | {formula or '-'} | {anchor.get('branch','-')} | "
            f"{anchor.get('verified_step','-')} | {result} | {anchor.get('next_action','-')} |"
        )
    else:
        lines.append("| - | No active anchor | - | - | - | - |")

    lines += ["", "## Completed", "", "| Candidate | Formula | Branch | Result | Next Action |", "|-----------|---------|--------|--------|-------------|"]
    for row in state.get("completed_e3_candidates", []):
        lines.append(
            f"| {row.get('candidate_id','-')} | {row.get('formula','-')} | {row.get('branch','-')} | "
            f"{row.get('checker_status','-')} | {row.get('next_action','-')} |"
        )

    lines += ["", "## Ready To Promote", "", "| Rank | Candidate | Formula | Branch | Loop Priority | Discovery | Layer | Gate Status | Next Action |", "|------|-----------|---------|--------|---------------|-----------|-------|-------------|-------------|"]
    promoted = 0
    for idx, row in enumerate(state.get("ready_qe_candidates", []), start=1):
        allowed, reason = candidate_gate_status(row.get("formula", ""), corpus)
        gate_status = "eligible" if allowed else reason or "blocked"
        lines.append(
            f"| {idx} | {row.get('candidate_id','-')} | {row.get('formula','-')} | {row.get('branch','-')} | "
            f"{row.get('loop_priority_score','-')} | {row.get('discovery_score','-')} | {row.get('candidate_layer','-')} | {gate_status} | {row.get('next_action','-')} |"
        )
        promoted += 1
    if promoted == 0:
        lines.append("| - | No ready queue row | - | - | - | - | - | - | - |")

    lines += [
        "",
        "## Notes",
        "",
        f"- resume anchor status: `{state.get('resume_anchor_status', 'unknown')}`",
        "- negative controls, reference anchors, and benchmark controls must not be reopened as heavy DFT lanes",
        "- if the first queue row is structure-blocked or classification-blocked, reseed to the next eligible lane and record the reason",
        "- Lane B should continue literature-backed corpus growth whenever the heavy lane is blocked",
        f"- maintenance-only streak: `{state.get('watchdog', {}).get('maintenance_only_streak', 0)}`",
        f"- hours since substantive advance: `{state.get('watchdog', {}).get('hours_since_last_substantive_advance', 0.0)}`",
        "",
    ]
    DFT_QUEUE_STATUS.write_text("\n".join(lines), encoding="utf-8")


def write_manifest_funnel_status(state: dict) -> None:
    funnel = state.get("manifest_funnel", {})
    broad = funnel.get("broad", [])
    structured = funnel.get("structured", [])
    promotion_ready = funnel.get("promotion_ready", [])
    counts = {
        "broad": len([row for row in funnel.get("broad", [])]),
        "structured": len([row for row in funnel.get("structured", [])]),
        "promotion_ready": len([row for row in funnel.get("promotion_ready", [])]),
    }

    lines = [
        "# Manifest Candidate Funnel",
        "",
        "Generated: 2026-06-27",
        "",
        "This board tracks the broader prescreen manifest, not only the 30-row credible corpus.",
        "",
        "## Funnel Counts",
        "",
        f"- Broad candidate pool: {counts['broad']}",
        f"- Structured candidate pool: {counts['structured']}",
        f"- Promotion-ready pool: {counts['promotion_ready']}",
        "",
    ]

    sections = [
        ("Broad Candidate Pool", broad, "Preserve quantity here; most rows are blocked by missing structure proxies or missing condition encoding."),
        ("Structured Candidate Pool", structured, "These rows already have a prototype proxy or enough branch semantics to support better ranking and controlled expansion."),
        ("Promotion-Ready Pool", promotion_ready, "Only these rows should compete for heavier compute once corpus-level gates are also satisfied."),
    ]
    for title, rows, note in sections:
        lines += [f"## {title}", "", note, "", "| Candidate | Formula | Branch | Quantity | Quality | Block | Upgrade |", "|---|---|---|---|---|---|---|"]
        for row in rows[:20]:
            lines.append(
                f"| {row.get('candidate_id','-')} | {row.get('formula','-')} | {row.get('branch','-')} | "
                f"{row.get('candidate_quantity_score','-')} | {row.get('candidate_quality_score','-')} | "
                f"{row.get('entry_block_reason') or '-'} | {', '.join(row.get('upgrade_requirements', [])) or '-'} |"
            )
        if not rows:
            lines.append("| - | - | - | - | - | - | - |")
        lines.append("")

    MANIFEST_FUNNEL_STATUS.write_text("\n".join(lines), encoding="utf-8")


def write_upgrade_execution_queue(state: dict) -> None:
    funnel = state.get("manifest_funnel", {})
    broad = funnel.get("broad", [])
    structured = funnel.get("structured", [])

    broad_upgrade = sorted(
        [
            row for row in broad
            if row.get("entry_block_reason") == "no_structure_proxy"
        ],
        key=lambda row: (
            -(row.get("candidate_quantity_score") or 0.0),
            -(row.get("candidate_quality_score") or 0.0),
            row.get("formula", ""),
        ),
    )[:10]

    structured_upgrade = sorted(
        [
            row for row in structured
            if row.get("entry_block_reason") == "proxy_only"
        ],
        key=lambda row: (
            -(row.get("candidate_quality_score") or 0.0),
            -(row.get("candidate_quantity_score") or 0.0),
            row.get("formula", ""),
        ),
    )[:10]

    blocked_hold = sorted(
        [
            row for row in structured
            if row.get("entry_block_reason") in {"negative_control", "structural_minimum_unresolved", "phase_ambiguity"}
        ],
        key=lambda row: (
            row.get("entry_block_reason", ""),
            -(row.get("candidate_quality_score") or 0.0),
            row.get("formula", ""),
        ),
    )[:10]

    lines = [
        "# Upgrade Execution Queue",
        "",
        "Generated: 2026-06-27",
        "",
        "This queue converts the funnel into immediate execution order.",
        "",
        "## Broad -> Structured",
        "",
        "Attach structure proxies and explicit condition scope first. This is the fastest way to preserve quantity while increasing scientific usability.",
        "",
        "| Rank | Candidate | Formula | Branch | Quantity | Quality | Block | Next Upgrade |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for idx, row in enumerate(broad_upgrade, start=1):
        lines.append(
            f"| {idx} | {row.get('candidate_id','-')} | {row.get('formula','-')} | {row.get('branch','-')} | "
            f"{row.get('candidate_quantity_score','-')} | {row.get('candidate_quality_score','-')} | "
            f"{row.get('entry_block_reason') or '-'} | {', '.join(row.get('upgrade_requirements', [])) or '-'} |"
        )
    if not broad_upgrade:
        lines.append("| - | - | - | - | - | - | - | - |")

    lines += [
        "",
        "## Structured -> Promotion-Ready",
        "",
        "These rows already have prototype proxies and now need structure-specific cleanup plus condition encoding.",
        "",
        "| Rank | Candidate | Formula | Branch | Quality | Block | Next Upgrade |",
        "|---|---|---|---|---|---|---|",
    ]
    for idx, row in enumerate(structured_upgrade, start=1):
        lines.append(
            f"| {idx} | {row.get('candidate_id','-')} | {row.get('formula','-')} | {row.get('branch','-')} | "
            f"{row.get('candidate_quality_score','-')} | {row.get('entry_block_reason') or '-'} | "
            f"{', '.join(row.get('upgrade_requirements', [])) or '-'} |"
        )
    if not structured_upgrade:
        lines.append("| - | - | - | - | - | - | - |")

    lines += [
        "",
        "## Hold / Blocked",
        "",
        "These rows must stay blocked until the scientific gate is cleared. Do not spend heavy compute here yet.",
        "",
        "| Candidate | Formula | Branch | Block | Required Resolution |",
        "|---|---|---|---|---|",
    ]
    for row in blocked_hold:
        lines.append(
            f"| {row.get('candidate_id','-')} | {row.get('formula','-')} | {row.get('branch','-')} | "
            f"{row.get('entry_block_reason') or '-'} | {', '.join(row.get('upgrade_requirements', [])) or '-'} |"
        )
    if not blocked_hold:
        lines.append("| - | - | - | - | - |")
    lines.append("")

    UPGRADE_EXECUTION_QUEUE.write_text("\n".join(lines), encoding="utf-8")


def write_markdown(state: dict) -> None:
    lines = [
        "# Loop State",
        "",
        f"Updated (UTC): {state['updated_at_utc']}",
        f"Manifest: `{state['manifest_path']}`",
        "",
        "## Snapshot",
        "",
        f"- Raw candidates: {state['raw_candidate_count']}",
        f"- Unique materials on leaderboard: {state['unique_material_count']}",
        f"- CHGNet-covered rows: {state['chgnet_covered_count']}",
        f"- E3 completed candidates: {len(state['completed_e3_candidates'])}",
        f"- QE-ready shortlist entries: {len(state['ready_qe_candidates'])}",
        "",
        "## Current Focus",
        "",
        f"- {state['loop_assessment']['current_focus']}",
        "",
        "## Next-Round Priorities",
        "",
    ]
    for item in state["loop_assessment"]["next_round_priority"]:
        lines.append(f"- {item}")
    lines += ["", "## QE-Ready Shortlist", ""]
    for row in state["ready_qe_candidates"][:8]:
        lines.append(
            f"- `{row['formula']}` ({row['branch']}) — discovery {row.get('discovery_score')}, "
            f"occurrences {row.get('occurrence_count', 1)}, next `{row.get('next_action', 'n/a')}`"
        )
    lines += ["", "## E3 / Review Flags", ""]
    if state["completed_e3_candidates"]:
        for row in state["completed_e3_candidates"]:
            lines.append(
                f"- `{row['formula']}` ({row['branch']}) — checker `{row.get('checker_status','n/a')}`, "
                f"next `{row.get('next_action','n/a')}`"
            )
    else:
        lines.append("- None yet.")
    lines += ["", "## Loop Gaps", ""]
    for item in state["loop_assessment"]["autonomy_gaps"]:
        lines.append(f"- {item}")
    if state.get("resume_anchor"):
        anchor = state["resume_anchor"]
        lines += [
            "",
            "## Resume Anchor",
            "",
            f"- `{anchor.get('candidate_id', 'n/a')}` ({anchor.get('formula', 'n/a')}, {anchor.get('branch', 'n/a')})",
            f"- Verified step: `{anchor.get('verified_step', 'n/a')}`",
            f"- Next action: `{anchor.get('next_action', 'n/a')}`",
        ]
    watchdog = state.get("watchdog", {})
    lines += [
        "",
        "## Watchdog",
        "",
        f"- Last substantive advance: `{watchdog.get('last_substantive_advance_at', 'n/a')}`",
        f"- Hours since substantive advance: `{watchdog.get('hours_since_last_substantive_advance', 'n/a')}`",
        f"- Cycles since substantive advance: `{watchdog.get('cycles_since_substantive_advance', 'n/a')}`",
        f"- Maintenance-only streak: `{watchdog.get('maintenance_only_streak', 'n/a')}`",
        f"- Anchor streak cycles: `{watchdog.get('anchor_streak_cycles', 'n/a')}`",
        f"- Anchor age hours: `{watchdog.get('anchor_age_hours', 'n/a')}`",
        f"- Stale anchor: `{watchdog.get('stale_anchor', False)}`",
    ]
    LOOP_STATE_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_runtime_state(state: dict) -> None:
    watchdog = state.get("watchdog", {})
    anchor = state.get("resume_anchor", {})
    payload = {
        "updated_at_utc": state.get("updated_at_utc"),
        "anchor_signature": anchor_signature(anchor),
        "anchor_streak_cycles": watchdog.get("anchor_streak_cycles", 0),
        "last_substantive_advance_at": watchdog.get("last_substantive_advance_at"),
        "cycles_since_substantive_advance": watchdog.get("cycles_since_substantive_advance", 0),
        "maintenance_only_streak": watchdog.get("maintenance_only_streak", 0),
        "public_corpus_count": watchdog.get("public_corpus_count", 0),
        "completed_e3_count": watchdog.get("completed_e3_count", 0),
        "top_ready_formula": watchdog.get("top_ready_formula", ""),
    }
    RUNTIME_STATE_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_health_report(state: dict) -> None:
    watchdog = state.get("watchdog", {})
    lines = [
        "# Superloop Health",
        "",
        f"Updated (UTC): {state.get('updated_at_utc', '')}",
        "",
        "## Core Metrics",
        "",
        f"- Public corpus count: {watchdog.get('public_corpus_count', 0)}",
        f"- E3 completed count: {watchdog.get('completed_e3_count', 0)}",
        f"- Hours since substantive advance: {watchdog.get('hours_since_last_substantive_advance', 0.0)}",
        f"- Cycles since substantive advance: {watchdog.get('cycles_since_substantive_advance', 0)}",
        f"- Maintenance-only streak: {watchdog.get('maintenance_only_streak', 0)}",
        f"- Anchor streak cycles: {watchdog.get('anchor_streak_cycles', 0)}",
        f"- Anchor age hours: {watchdog.get('anchor_age_hours', 0.0)}",
        f"- Stale anchor: {watchdog.get('stale_anchor', False)}",
        f"- Stale anchor reason: {watchdog.get('stale_anchor_reason') or '-'}",
        f"- Resume anchor status: {state.get('resume_anchor_status', '-')}",
        "",
        "## Red Flags",
        "",
    ]
    red_flags = []
    if watchdog.get("hours_since_last_substantive_advance", 0.0) > 2.0:
        red_flags.append("hours_since_last_substantive_advance > 2")
    if watchdog.get("maintenance_only_streak", 0) > 2:
        red_flags.append("maintenance_only_streak > 2")
    if watchdog.get("stale_anchor"):
        red_flags.append(f"stale_anchor: {watchdog.get('stale_anchor_reason')}")
    if not red_flags:
        red_flags.append("none")
    for flag in red_flags:
        lines.append(f"- {flag}")
    HEALTH_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    state = build_state()
    corpus = load_corpus_registry()
    LOOP_STATE_JSON.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(state)
    write_dft_queue_status(state, corpus)
    write_manifest_funnel_status(state)
    write_upgrade_execution_queue(state)
    write_runtime_state(state)
    write_health_report(state)
    print(f"Wrote {LOOP_STATE_JSON}")
    print(f"Wrote {LOOP_STATE_MD}")
    print(f"Wrote {DFT_QUEUE_STATUS}")
    print(f"Wrote {MANIFEST_FUNNEL_STATUS}")
    print(f"Wrote {UPGRADE_EXECUTION_QUEUE}")
    print(f"Wrote {RUNTIME_STATE_JSON}")
    print(f"Wrote {HEALTH_MD}")


if __name__ == "__main__":
    main()
