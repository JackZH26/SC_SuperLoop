#!/usr/bin/env python3
"""Execute one self-propelling SC SuperLoop cycle.

This cycle is intentionally execution-led rather than report-led:

1. refresh state
2. compare current public-corpus size against a 7-day trajectory
3. expand the candidate manifest if the funnel is too thin
4. promote the best eligible ready/structured rows into the public corpus
5. refresh reports and checkpoint substantive changes
"""

from __future__ import annotations

import json
import math
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

SC_ROOT = Path("/data/.openclaw/workspace/research/SC_SuperLoop")
REPORTS = SC_ROOT / "reports"
CORPUS = SC_ROOT / "knowledge" / "credible_superconductors.jsonl"
LOOP_STATE = REPORTS / "loop_state.json"
CYCLE_LOG = REPORTS / "superloop_cycle_log.md"
GROWTH_TARGET = REPORTS / "superloop_growth_target.json"

TARGET_PUBLIC_COUNT = 110
TARGET_WINDOW_DAYS = 7
MAX_PROMOTIONS_PER_CYCLE = 4
MIN_PUBLIC_GROWTH_PER_DAY = 9
MIN_PROMOTION_READY_BUFFER = 18
MIN_STRUCTURED_BUFFER = 12

PROMOTION_OVERRIDES = {
    "Nd0.8Sr0.2NiO2": {
        "material_class": "Sr-doped infinite-layer nickelate",
        "structure_or_prototype_note": "Infinite-layer nickelate mainline row retained as an explicit doped charge-transfer candidate rather than a passive reference anchor.",
        "superconductivity_context": "Prescreen-stage doped nickelate mainline candidate kept visible for bounded charge-transfer follow-up, not as a confirmed superconductivity claim.",
        "condition_note": "This is a DFT-screened exploratory record only; superconducting relevance depends on explicit doped infinite-layer context rather than undoped bulk semantics.",
        "mechanism_note": "Mainline charge-transfer nickelate route with explicit doped context.",
        "risk_tags": ["strong_correlation_risk", "carrier_density_sensitive", "doping_required"],
        "next_action": "bounded_dft_followup",
        "phase_or_condition_id": "sr_doped_infinite_layer_nickelate",
        "mechanism_risk": ["strong_correlation", "doping_required"],
        "promotion_gate": "ready_for_next_generation",
    },
    "NdNiO2": {
        "material_class": "parent infinite-layer nickelate",
        "structure_or_prototype_note": "Parent nickelate comparator retained as a bounded charge-transfer baseline for the doped mainline.",
        "superconductivity_context": "Prescreen-stage parent nickelate comparator retained to support the doped nickelate route, not as a confirmed superconductivity claim.",
        "condition_note": "This is a DFT-screened exploratory record only; its value is as a parent-state comparator for explicitly doped rows.",
        "mechanism_note": "Parent-state comparator for the nickelate charge-transfer lane.",
        "risk_tags": ["strong_correlation_risk", "doping_required"],
        "next_action": "bounded_dft_followup",
        "phase_or_condition_id": "parent_infinite_layer_nickelate",
        "mechanism_risk": ["strong_correlation", "doping_required"],
        "promotion_gate": "ready_for_next_generation",
    },
    "PrNiO2": {
        "material_class": "rare-earth infinite-layer nickelate comparator",
        "structure_or_prototype_note": "Rare-earth nickelate comparator retained to widen the mainline charge-transfer lane without changing evidence semantics.",
        "superconductivity_context": "Prescreen-stage rare-earth comparator for the nickelate lane, not a confirmed superconductivity claim.",
        "condition_note": "This is a DFT-screened exploratory record only; it remains a comparator row pending bounded follow-up.",
        "mechanism_note": "Rare-earth comparator within the nickelate charge-transfer lane.",
        "risk_tags": ["strong_correlation_risk", "doping_required"],
        "next_action": "bounded_dft_followup",
        "phase_or_condition_id": "pr_infinite_layer_nickelate_parent",
        "mechanism_risk": ["strong_correlation", "doping_required"],
        "promotion_gate": "ready_for_next_generation",
    },
    "Ba2NiO2F2": {
        "material_class": "square-ligand nickel oxyfluoride",
        "structure_or_prototype_note": "Square-ligand nickel oxyfluoride retained as a structured mainline extension of the charge-transfer lane.",
        "superconductivity_context": "Prescreen-stage structured oxyfluoride candidate kept for bounded square-ligand follow-up, not as a confirmed superconductivity claim.",
        "condition_note": "This is a DFT-screened exploratory record only; structural validation remains part of the bounded follow-up path.",
        "mechanism_note": "Square-ligand extension of the charge-transfer nickelate lane.",
        "risk_tags": ["strong_correlation_risk", "ligand_field_sensitive"],
        "next_action": "bounded_dft_followup",
        "phase_or_condition_id": "square_ligand_nickel_oxyfluoride",
        "mechanism_risk": ["strong_correlation", "ligand_field_sensitive"],
        "promotion_gate": "ready_for_next_generation",
    },
    "La2PdO4": {
        "material_class": "214 palladate boundary comparator",
        "structure_or_prototype_note": "4d palladate comparator retained as a bounded boundary test around the nickelate/cuprate mainline.",
        "superconductivity_context": "Prescreen-stage boundary comparator for wider-band charge-transfer testing, not as a confirmed superconductivity claim.",
        "condition_note": "This is a DFT-screened exploratory record only; it remains a boundary comparator while the loop prioritizes nickelate-like rows.",
        "mechanism_note": "4d boundary comparator for the main charge-transfer lane.",
        "risk_tags": ["strong_correlation_risk", "wider_band_risk", "palladate_comparator"],
        "next_action": "bounded_dft_followup",
        "phase_or_condition_id": "214_palladate_boundary_test",
        "mechanism_risk": ["strong_correlation", "wider_band_risk"],
        "promotion_gate": "ready_for_next_generation",
    },
    "LaPdO2": {
        "material_class": "infinite-layer palladate analog",
        "structure_or_prototype_note": "4d infinite-layer palladate comparator retained as a wider-band boundary test for the charge-transfer lane.",
        "superconductivity_context": "Prescreen-stage 4d infinite-layer comparator retained as a bounded charge-transfer boundary test, not as a confirmed superconductivity claim.",
        "condition_note": "This is a DFT-screened exploratory record only; it is kept visible because it tests whether the 4d route loses the desired confinement too early.",
        "mechanism_note": "4d infinite-layer boundary comparator for the nickelate/cuprate mainline.",
        "risk_tags": ["strong_correlation_risk", "carrier_density_sensitive", "conjecture_only", "wider_band_risk", "palladate_comparator"],
        "next_action": "bounded_dft_followup",
        "phase_or_condition_id": "infinite_layer_palladate_boundary_test",
        "mechanism_risk": ["strong_correlation", "wider_band_risk"],
        "promotion_gate": "ready_for_next_generation",
    },
    "SrTiO3": {
        "material_class": "d0 oxide perovskite",
        "structure_or_prototype_note": "Canonical STO-family oxide entry retained under explicit low-carrier-density superconducting semantics.",
        "superconductivity_context": "Prescreen-stage oxide-side-branch candidate kept for the dilute-carrier / ferroelectric-proximity route.",
        "condition_note": "This is a DFT-screened exploratory record only; superconducting relevance depends on dilute doping / vacancy context rather than stoichiometric bulk SrTiO3.",
        "mechanism_note": "Useful oxide side branch for low-density superconductivity benchmarking rather than a room-temperature mainline claim.",
        "risk_tags": ["carrier_density_sensitive", "oxygen_vacancy_sensitive", "oxide_side_branch"],
        "next_action": "promote_to_oxide_structured_queue",
        "phase_or_condition_id": "dilute_carrier_sto",
        "mechanism_risk": ["carrier_density_sensitive", "oxygen_stoichiometry_sensitive"],
        "promotion_gate": "ready_for_next_generation",
    },
    "CaTiO3": {
        "material_class": "oxide perovskite analog",
        "structure_or_prototype_note": "Calcium titanate perovskite entry retained as an STO-adjacent oxide-side-branch comparator.",
        "superconductivity_context": "Prescreen-stage oxide-side-branch comparator retained to test structural compression in the STO-like family.",
        "condition_note": "This is a DFT-screened exploratory record only; no bulk superconductivity claim is implied.",
        "mechanism_note": "Oxide comparator for perovskite-side structure-pressure effects.",
        "risk_tags": ["carrier_density_sensitive", "oxide_side_branch", "conjecture_only"],
        "next_action": "promote_to_oxide_structured_queue",
        "phase_or_condition_id": "perovskite_oxide_comparator",
        "mechanism_risk": ["carrier_density_sensitive"],
        "promotion_gate": "ready_for_next_generation",
    },
    "KTaO3": {
        "material_class": "d0 oxide perovskite",
        "structure_or_prototype_note": "KTaO3 perovskite retained as a dilute-carrier oxide-side-branch candidate with SOC relevance.",
        "superconductivity_context": "Prescreen-stage KTaO3-derived oxide candidate retained for the low-density superconductivity side branch.",
        "condition_note": "This is a DFT-screened exploratory record only; relevant superconducting interpretations depend on explicit low-density/interface conditions.",
        "mechanism_note": "SOC-relevant oxide-side benchmark within the dilute-carrier family.",
        "risk_tags": ["carrier_density_sensitive", "oxide_side_branch", "SOC_check_later"],
        "next_action": "promote_to_oxide_structured_queue",
        "phase_or_condition_id": "dilute_carrier_ktao3",
        "mechanism_risk": ["carrier_density_sensitive", "soc_sensitive"],
        "promotion_gate": "ready_for_next_generation",
    },
    "BaTiO3": {
        "material_class": "ferroelectric oxide comparator",
        "structure_or_prototype_note": "Ferroelectric BaTiO3 retained as a structured oxide-side comparator around STO-like low-density routes.",
        "superconductivity_context": "Prescreen-stage oxide-side comparator retained for bounded structural / ferroelectric follow-up, not as a confirmed superconductivity claim.",
        "condition_note": "This is a DFT-screened exploratory record only; any superconducting relevance would remain condition-dependent.",
        "mechanism_note": "Ferroelectric comparator in the dilute-carrier oxide side branch.",
        "risk_tags": ["carrier_density_sensitive", "oxide_side_branch"],
        "next_action": "promote_to_oxide_structured_queue",
        "phase_or_condition_id": "ferroelectric_oxide_comparator",
        "mechanism_risk": ["carrier_density_sensitive"],
        "promotion_gate": "ready_for_next_generation",
    },
}


def run_script(script: str, *args: str) -> None:
    subprocess.run(["python3", str(SC_ROOT / "scripts" / script), *args], check=True)


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def current_date_str() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def ensure_growth_target(public_count: int) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    state = load_json(GROWTH_TARGET, {})
    if state:
        return state
    target = {
        "started_at_utc": now.isoformat(),
        "baseline_public_count": public_count,
        "target_public_count": TARGET_PUBLIC_COUNT,
        "target_due_at_utc": (now + timedelta(days=TARGET_WINDOW_DAYS)).isoformat(),
        "minimum_daily_growth": MIN_PUBLIC_GROWTH_PER_DAY,
    }
    GROWTH_TARGET.write_text(json.dumps(target, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return target


def target_progress(growth: dict[str, Any], public_count: int) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    started = datetime.fromisoformat(growth["started_at_utc"])
    due = datetime.fromisoformat(growth["target_due_at_utc"])
    baseline = int(growth["baseline_public_count"])
    target = int(growth["target_public_count"])
    total_seconds = max(1.0, (due - started).total_seconds())
    elapsed_seconds = min(max(0.0, (now - started).total_seconds()), total_seconds)
    fraction = elapsed_seconds / total_seconds
    expected_now = baseline + math.ceil((target - baseline) * fraction)
    shortfall = max(0, expected_now - public_count)
    remaining_days = max(0.0, (due - now).total_seconds() / 86400.0)
    needed = max(0, target - public_count)
    per_day_needed = max(
        int(growth.get("minimum_daily_growth", MIN_PUBLIC_GROWTH_PER_DAY)),
        math.ceil(needed / max(1.0, remaining_days)) if needed else 0,
    )
    return {
        "expected_now": expected_now,
        "shortfall_now": shortfall,
        "remaining_needed": needed,
        "remaining_days": round(remaining_days, 2),
        "daily_growth_needed": per_day_needed,
    }


def manifest_paths() -> tuple[Path, Path]:
    day_dir = SC_ROOT / "candidates" / current_date_str()
    return day_dir / "candidate_manifest.jsonl", day_dir / "candidate_manifest_prescreened.jsonl"


def maybe_expand_manifest(loop_state: dict[str, Any], trajectory: dict[str, Any]) -> list[str]:
    manifest = loop_state.get("manifest_funnel", {})
    broad = len(manifest.get("broad", []))
    structured = len(manifest.get("structured", []))
    promotion_ready = len(manifest.get("promotion_ready", []))
    raw_count = int(loop_state.get("raw_candidate_count", 0) or 0)
    unique_count = int(loop_state.get("unique_material_count", 0) or 0)

    should_expand = (
        promotion_ready < MIN_PROMOTION_READY_BUFFER
        or structured < MIN_STRUCTURED_BUFFER
        or raw_count < 280
        or unique_count < 120
        or trajectory["daily_growth_needed"] >= MIN_PUBLIC_GROWTH_PER_DAY + 2
    )
    if not should_expand:
        return []

    actions = [
        f"expand_manifest: raw={raw_count}, unique={unique_count}, structured={structured}, promotion_ready={promotion_ready}",
    ]
    run_script("generate_candidates.py")
    run_script("prescreen.py", "--date", current_date_str())
    actions.append("prescreen_manifest_refreshed")
    return actions


def loop_state() -> dict[str, Any]:
    return load_json(LOOP_STATE, {})


def candidate_sort_key(row: dict[str, Any]) -> tuple:
    layer_rank = {"promotion_ready": 2, "structured": 1, "broad": 0}
    return (
        layer_rank.get(str(row.get("candidate_layer") or ""), -1),
        float(row.get("loop_priority_score") or -999.0),
        float(row.get("candidate_quality_score") or -999.0),
        float(row.get("discovery_score") or -999.0),
        float(row.get("prescreen_score") or -999.0),
        row.get("formula", ""),
    )


def eligible_candidates(state: dict[str, Any], existing: set[str]) -> list[dict]:
    rows = list(state.get("ready_qe_candidates", []))
    manifest = state.get("manifest_funnel", {})
    rows.extend(manifest.get("promotion_ready", []))
    rows.extend(manifest.get("structured", []))
    deduped: dict[str, dict] = {}
    for row in rows:
        formula = str(row.get("formula") or "").strip()
        if not formula or formula in existing:
            continue
        block_reason = row.get("entry_block_reason")
        if block_reason in {"negative_control", "phase_ambiguity", "structural_minimum_unresolved", "no_structure_proxy"}:
            continue
        layer = str(row.get("candidate_layer") or "")
        evidence = str(row.get("evidence_level") or "")
        if layer not in {"promotion_ready", "structured", "broad"}:
            continue
        if layer == "broad" and evidence != "E1":
            continue
        if float(row.get("prescreen_score") or 0.0) < 52.0:
            continue
        if float(row.get("discovery_score") or 0.0) < 50.0:
            continue
        if formula not in deduped or candidate_sort_key(row) > candidate_sort_key(deduped[formula]):
            deduped[formula] = row
    return sorted(deduped.values(), key=candidate_sort_key, reverse=True)


def build_public_record(candidate: dict) -> dict:
    formula = str(candidate.get("formula") or "").strip()
    config = PROMOTION_OVERRIDES.get(formula, {})
    risk_tags = list(dict.fromkeys(config.get("risk_tags", candidate.get("risk_tags", [])) or []))
    branch = str(candidate.get("branch") or "")
    return {
        "record_id": f"track-b-{str(candidate.get('candidate_id') or formula).lower().replace('.', '').replace('/', '-')}",
        "track": "B",
        "formula": formula,
        "normalized_formula": formula,
        "material_class": config.get("material_class", f"{branch} exploratory candidate"),
        "branch_or_family": branch,
        "structure_or_prototype_note": config.get(
            "structure_or_prototype_note",
            f"Loop-promoted {branch} candidate retained with explicit DFT-screened exploratory semantics.",
        ),
        "evidence_class": "DFT-screened",
        "superconductivity_context": config.get(
            "superconductivity_context",
            "Prescreen-stage SC SuperLoop exploratory candidate retained as a bounded public research row, not as a confirmed superconductivity claim.",
        ),
        "Tc_value_or_range": None,
        "condition_note": config.get(
            "condition_note",
            "This is a DFT-screened exploratory record only; public visibility does not imply a validated Tc claim.",
        ),
        "mechanism_note": config.get("mechanism_note", str(candidate.get("mechanism_hypothesis") or "").strip()),
        "risk_tags": risk_tags,
        "source_citation": f"SC SuperLoop prescreen candidate {candidate.get('candidate_id')}",
        "source_type": "internal_dft_screen",
        "review_status": "pending",
        "record_role": "exploratory_candidate",
        "superconductivity_status": "unconfirmed_candidate",
        "novelty_class": "loop_generated_variant",
        "promotion_gate": config.get("promotion_gate", "ready_for_next_generation"),
        "mechanism_risk": config.get("mechanism_risk", []),
        "claim_level": "dft_screened_not_tc_claim",
        "next_action": config.get("next_action", "bounded_dft_followup"),
        "discovery_score_public": candidate.get("discovery_score"),
        "phase_or_condition_id": config.get("phase_or_condition_id", f"{formula.lower()}_loop_variant"),
        "exclude_from_new_discovery_leaderboard": False,
        "include_in_family_anchor_board": False,
        "avoid_rule": None,
        "allowed_escape_routes": ["structure_proxy_upgrade", "structured_lane_promotion", "bounded_dft_followup"],
        "candidate_layer": str(candidate.get("candidate_layer") or "promotion_ready"),
        "candidate_quantity_score": float(candidate.get("candidate_quantity_score") or 74.0),
        "candidate_quality_score": float(candidate.get("candidate_quality_score") or 70.0),
        "entry_block_reason": candidate.get("entry_block_reason"),
        "upgrade_requirements": candidate.get("upgrade_requirements", ["bounded_dft_followup"]),
        "family_ruleset_id": candidate.get(
            "family_ruleset_id",
            "ruleset_single_orbital_charge_transfer_v1"
            if branch == "cuprate_extrapolation"
            else "ruleset_generic_reference_v1",
        ),
    }


def promote_candidates(limit: int) -> list[str]:
    corpus_rows = load_jsonl(CORPUS)
    existing = {row.get("formula", "") for row in corpus_rows}
    state = loop_state()
    promoted: list[str] = []
    for row in eligible_candidates(state, existing):
        if len(promoted) >= limit:
            break
        corpus_rows.append(build_public_record(row))
        existing.add(row["formula"])
        promoted.append(row["formula"])
    if promoted:
        write_jsonl(CORPUS, corpus_rows)
    return promoted


def append_cycle_log(lines: list[str]) -> None:
    stamp = datetime.now(timezone.utc).isoformat()
    block = "\n".join([f"## Cycle {stamp}", ""] + [f"- {line}" for line in lines] + [""])
    with CYCLE_LOG.open("a", encoding="utf-8") as handle:
        handle.write(block)


def update_growth_report(public_count: int, trajectory: dict[str, Any]) -> None:
    report = {
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "public_corpus_count": public_count,
        **trajectory,
    }
    GROWTH_TARGET.write_text(
        json.dumps({**ensure_growth_target(public_count), "latest": report}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def maybe_checkpoint(promoted: list[str], expanded: bool) -> None:
    if not promoted and not expanded:
        return
    tracked = [
        "knowledge/credible_superconductors.jsonl",
        "reports/discovery_feed.json",
        "reports/discovery_meta.json",
        "reports/loop_state.json",
        "reports/loop_state.md",
        "reports/dft_queue_status.md",
        "reports/manifest_candidate_funnel.md",
        "reports/upgrade_execution_queue.md",
        "reports/superloop_runtime_state.json",
        "reports/superloop_health.md",
        "reports/superloop_growth_target.json",
        "reports/credible_corpus_status.md",
        "reports/strategy_updates.md",
    ]
    manifest, prescreened = manifest_paths()
    if manifest.exists():
        tracked.append(str(manifest.relative_to(SC_ROOT)))
    if prescreened.exists():
        tracked.append(str(prescreened.relative_to(SC_ROOT)))
    subprocess.run(["git", "-C", str(SC_ROOT), "add", *tracked], check=True)
    summary_bits = []
    if promoted:
        summary_bits.append(f"promote {' '.join(promoted)}")
    if expanded:
        summary_bits.append("refresh manifest funnel")
    subprocess.run(
        ["git", "-C", str(SC_ROOT), "commit", "-m", f"Superloop cycle {'; '.join(summary_bits)}"],
        check=True,
    )


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    run_script("optimize_discovery_corpus.py")
    run_script("update_loop_state.py")
    run_script("export_discovery_feed.py")

    state = loop_state()
    public_count = len(load_jsonl(CORPUS))
    growth = ensure_growth_target(public_count)
    trajectory = target_progress(growth, public_count)

    lines = [
        f"weekly_target: {public_count}/{growth['target_public_count']} public records, shortfall_now={trajectory['shortfall_now']}, daily_growth_needed={trajectory['daily_growth_needed']}",
    ]

    expansion_notes = maybe_expand_manifest(state, trajectory)
    if expansion_notes:
        lines.extend(expansion_notes)
        run_script("optimize_discovery_corpus.py")
        run_script("update_loop_state.py")
        run_script("export_discovery_feed.py")
        state = loop_state()

    promotion_limit = min(
        MAX_PROMOTIONS_PER_CYCLE,
        max(1, trajectory["shortfall_now"], math.ceil(trajectory["daily_growth_needed"] / 3)),
    )
    promoted = promote_candidates(promotion_limit)
    if promoted:
        lines.append(f"advance_corpus: promoted {', '.join(promoted)}")
        run_script("optimize_discovery_corpus.py")
        run_script("update_loop_state.py")
        run_script("export_discovery_feed.py")
    else:
        lines.append("no_corpus_promotion: no eligible queue-driven row found")

    public_count = len(load_jsonl(CORPUS))
    trajectory = target_progress(growth, public_count)
    update_growth_report(public_count, trajectory)
    lines.append(f"post_cycle_public_count: {public_count}")

    if (REPORTS / "superloop_health.md").exists():
        lines.append("health_report_refreshed")

    append_cycle_log(lines)
    maybe_checkpoint(promoted, bool(expansion_notes))


if __name__ == "__main__":
    main()
