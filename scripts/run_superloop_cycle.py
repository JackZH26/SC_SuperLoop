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
import re
import subprocess
from collections import Counter
from datetime import datetime, timedelta, timezone
from hashlib import sha1
from pathlib import Path
from typing import Any

from lane_registry import LANE_ORDER, lane_metadata_for

SC_ROOT = Path("/data/.openclaw/workspace/research/SC_SuperLoop")
REPORTS = SC_ROOT / "reports"
CORPUS = SC_ROOT / "knowledge" / "credible_superconductors.jsonl"
LOOP_STATE = REPORTS / "loop_state.json"
CYCLE_LOG = REPORTS / "superloop_cycle_log.md"
GROWTH_TARGET = REPORTS / "superloop_growth_target.json"

TARGET_PUBLIC_COUNT = 300
TARGET_WINDOW_DAYS = 7
MAX_PROMOTIONS_PER_CYCLE = 4
MIN_PUBLIC_GROWTH_PER_DAY = 9
MIN_PROMOTION_READY_BUFFER = 18
MIN_STRUCTURED_BUFFER = 12
MAX_PROMOTIONS_PER_LANE = 2
MIN_FAMILY_BUFFER = 2

MAINLINE_LANES = {"nickelate", "cuprate", "iron_based", "mgb2_diboride"}
HIGH_UPSIDE_LANES = {"hydride", "nickelate", "cuprate", "frontier_first_principles"}
CHEAP_EXPLORATION_LANES = {"conventional", "elemental", "kagome", "borocarbide", "chalcogenide"}
FRONTIER_LANE = "frontier_first_principles"

KNOWN_BASELINE_PROMOTIONS = {
    "LuNi2B2C": {
        "record_role": "benchmark_control",
        "superconductivity_status": "confirmed_superconductor",
        "novelty_class": "known_reference",
        "promotion_gate": "require_literature_source",
        "mechanism_risk": ["conventional_epc", "magnetism_interplay"],
        "claim_level": "benchmark_only",
        "next_action": "attach_primary_borocarbide_superconductivity_source",
        "exclude_from_new_discovery_leaderboard": True,
        "include_in_family_anchor_board": True,
    },
    "YNi2B2C": {
        "record_role": "benchmark_control",
        "superconductivity_status": "confirmed_superconductor",
        "novelty_class": "known_reference",
        "promotion_gate": "require_literature_source",
        "mechanism_risk": ["conventional_epc", "magnetism_interplay"],
        "claim_level": "benchmark_only",
        "next_action": "attach_primary_borocarbide_superconductivity_source",
        "exclude_from_new_discovery_leaderboard": True,
        "include_in_family_anchor_board": True,
    },
    "Ta": {
        "record_role": "benchmark_control",
        "superconductivity_status": "confirmed_superconductor",
        "novelty_class": "known_reference",
        "promotion_gate": "require_literature_source",
        "mechanism_risk": ["conventional_epc"],
        "claim_level": "benchmark_only",
        "next_action": "attach_primary_elemental_superconductivity_source",
        "exclude_from_new_discovery_leaderboard": True,
        "include_in_family_anchor_board": True,
    },
    "V": {
        "record_role": "benchmark_control",
        "superconductivity_status": "confirmed_superconductor",
        "novelty_class": "known_reference",
        "promotion_gate": "require_literature_source",
        "mechanism_risk": ["conventional_epc"],
        "claim_level": "benchmark_only",
        "next_action": "attach_primary_elemental_superconductivity_source",
        "exclude_from_new_discovery_leaderboard": True,
        "include_in_family_anchor_board": True,
    },
    "KV3Sb5": {
        "record_role": "mechanism_anchor",
        "superconductivity_status": "confirmed_superconductor",
        "novelty_class": "known_reference",
        "promotion_gate": "require_literature_source",
        "mechanism_risk": ["topology_sensitive", "cdw_competition"],
        "claim_level": "reference_only",
        "next_action": "attach_primary_kagome_superconductivity_source",
        "exclude_from_new_discovery_leaderboard": True,
        "include_in_family_anchor_board": True,
    },
    "Cu0.3Bi2Se3": {
        "record_role": "mechanism_anchor",
        "superconductivity_status": "confirmed_superconductor",
        "novelty_class": "known_reference",
        "promotion_gate": "require_literature_source",
        "mechanism_risk": ["topology_sensitive", "doping_required", "disorder_sensitive"],
        "claim_level": "reference_only",
        "next_action": "attach_primary_topological_superconductivity_source",
        "exclude_from_new_discovery_leaderboard": True,
        "include_in_family_anchor_board": True,
    },
}

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


def canonical_lane(row: dict[str, Any]) -> str:
    lane_id = str(row.get("lane_id") or "").strip()
    if lane_id:
        return lane_id
    branch = str(row.get("branch") or row.get("branch_or_family") or "").strip()
    formula = str(row.get("formula") or "").strip()
    risk_tags = row.get("risk_tags", []) or []
    return lane_metadata_for(branch, formula, risk_tags).get("lane_id", FRONTIER_LANE)


def corpus_lane_counts(rows: list[dict[str, Any]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in rows:
        counts[canonical_lane(row)] += 1
    for lane_id in LANE_ORDER:
        counts.setdefault(lane_id, 0)
    return counts


def manifest_lane_buffers(state: dict[str, Any]) -> dict[str, int]:
    counts = {lane_id: 0 for lane_id in LANE_ORDER}
    manifest = state.get("manifest_funnel", {})
    for layer in ("promotion_ready", "structured"):
        for row in manifest.get(layer, []):
            counts[canonical_lane(row)] = counts.get(canonical_lane(row), 0) + 1
    return counts


def lane_deficit_priority(corpus_counts: Counter[str]) -> dict[str, int]:
    ordered = sorted(LANE_ORDER, key=lambda lane_id: (corpus_counts.get(lane_id, 0), lane_id))
    return {lane_id: idx for idx, lane_id in enumerate(ordered)}


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def current_date_str() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def stable_record_id(candidate: dict, formula: str, lane_id: str) -> str:
    phase = str(candidate.get("phase_or_condition_id") or "")
    payload = "|".join([formula, lane_id, phase, str(candidate.get("candidate_id") or "")])
    digest = sha1(payload.encode("utf-8")).hexdigest()[:10]
    formula_slug = re.sub(r"[^a-z0-9]+", "-", formula.lower()).strip("-") or "candidate"
    lane_slug = re.sub(r"[^a-z0-9]+", "-", lane_id.lower()).strip("-") or "misc"
    return f"track-b-{lane_slug}-{formula_slug}-{digest}"


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


def watchdog_recovery_plan(loop_state: dict[str, Any]) -> dict[str, Any]:
    watchdog = loop_state.get("watchdog", {}) or {}
    maintenance_streak = int(watchdog.get("maintenance_only_streak", 0) or 0)
    hours_since_advance = float(watchdog.get("hours_since_last_substantive_advance", 0.0) or 0.0)
    stale_anchor = bool(watchdog.get("stale_anchor"))
    level = str(watchdog.get("escalation_level") or "normal")
    actions = list(watchdog.get("escalation_actions", []) or [])
    should_recover = level != "normal" or maintenance_streak >= 3 or hours_since_advance >= 2.0 or stale_anchor
    return {
        "should_recover": should_recover,
        "level": level,
        "actions": actions,
        "maintenance_streak": maintenance_streak,
        "hours_since_advance": hours_since_advance,
        "stale_anchor": stale_anchor,
    }


def maybe_expand_manifest(loop_state: dict[str, Any], trajectory: dict[str, Any]) -> list[str]:
    manifest = loop_state.get("manifest_funnel", {})
    broad = len(manifest.get("broad", []))
    structured = len(manifest.get("structured", []))
    promotion_ready = len(manifest.get("promotion_ready", []))
    raw_count = int(loop_state.get("raw_candidate_count", 0) or 0)
    unique_count = int(loop_state.get("unique_material_count", 0) or 0)
    recovery = watchdog_recovery_plan(loop_state)
    maintenance_streak = recovery["maintenance_streak"]
    hours_since_advance = recovery["hours_since_advance"]
    lane_buffers = manifest_lane_buffers(loop_state)
    thin_lanes = [lane_id for lane_id in LANE_ORDER if lane_buffers.get(lane_id, 0) < MIN_FAMILY_BUFFER]

    should_expand = (
        promotion_ready < MIN_PROMOTION_READY_BUFFER
        or structured < MIN_STRUCTURED_BUFFER
        or raw_count < 280
        or unique_count < 120
        or trajectory["daily_growth_needed"] >= MIN_PUBLIC_GROWTH_PER_DAY + 2
        or recovery["should_recover"]
        or bool(thin_lanes)
    )
    if not should_expand:
        return []

    actions = [
        f"expand_manifest: raw={raw_count}, unique={unique_count}, structured={structured}, promotion_ready={promotion_ready}",
    ]
    if thin_lanes:
        actions.append("family_buffer_recovery: " + ", ".join(thin_lanes))
    generator_args: list[str] = []
    if recovery["should_recover"]:
        generator_args.append("--exclude-corpus")
        actions.append(
            "watchdog_recovery: "
            f"level={recovery['level']}, actions={','.join(recovery['actions']) or 'diversify_away_from_public_corpus'}"
        )
        actions.append(
            f"generator_mode: diversify_away_from_public_corpus (maintenance_streak={maintenance_streak}, hours_since_advance={hours_since_advance})"
        )
    run_script("generate_candidates.py", *generator_args)
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


def lane_of(row: dict[str, Any]) -> str:
    return canonical_lane(row)


def eligible_candidates(state: dict[str, Any], existing: set[str]) -> list[dict]:
    rows = list(state.get("ready_qe_candidates", []))
    manifest = state.get("manifest_funnel", {})
    rows.extend(manifest.get("promotion_ready", []))
    rows.extend(manifest.get("structured", []))
    rows.extend(manifest.get("broad", []))
    recovery = watchdog_recovery_plan(state)
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
        if layer == "broad":
            broad_recovery_ok = (
                recovery["should_recover"]
                and float(row.get("prescreen_score") or 0.0) >= 53.0
                and float(row.get("discovery_score") or 0.0) >= 52.0
            )
            if evidence != "E1" and not broad_recovery_ok:
                continue
        if float(row.get("prescreen_score") or 0.0) < 52.0:
            continue
        if float(row.get("discovery_score") or 0.0) < 50.0:
            continue
        if formula not in deduped or candidate_sort_key(row) > candidate_sort_key(deduped[formula]):
            deduped[formula] = row
    return sorted(deduped.values(), key=candidate_sort_key, reverse=True)


def select_lane_aware_candidates(rows: list[dict], limit: int, corpus_counts: Counter[str]) -> list[dict]:
    selected: list[dict] = []
    selected_formulas: set[str] = set()
    lane_counts: dict[str, int] = {}
    deficit_rank = lane_deficit_priority(corpus_counts)
    ordered_rows = sorted(
        rows,
        key=lambda row: (
            deficit_rank.get(lane_of(row), len(LANE_ORDER)),
            -float(row.get("candidate_quality_score") or -999.0),
            -float(row.get("discovery_score") or -999.0),
            str(row.get("formula") or ""),
        ),
    )

    def try_pick(group: set[str] | None = None, prefer_new_lane: bool = True) -> None:
        for require_fresh_lane in ([True, False] if prefer_new_lane else [False]):
            for row in ordered_rows:
                formula = str(row.get("formula") or "").strip()
                lane_id = lane_of(row)
                if formula in selected_formulas:
                    continue
                if group is not None and lane_id not in group:
                    continue
                if require_fresh_lane and lane_counts.get(lane_id, 0) > 0:
                    continue
                if lane_counts.get(lane_id, 0) >= MAX_PROMOTIONS_PER_LANE:
                    continue
                selected.append(row)
                selected_formulas.add(formula)
                lane_counts[lane_id] = lane_counts.get(lane_id, 0) + 1
                return

    if limit <= 0:
        return []

    try_pick(MAINLINE_LANES)
    if len(selected) < limit:
        try_pick(HIGH_UPSIDE_LANES)
    if len(selected) < limit:
        try_pick(CHEAP_EXPLORATION_LANES)
    if len(selected) < limit:
        try_pick({FRONTIER_LANE})

    for row in ordered_rows:
        if len(selected) >= limit:
            break
        formula = str(row.get("formula") or "").strip()
        lane_id = lane_of(row)
        if formula in selected_formulas:
            continue
        if lane_counts.get(lane_id, 0) >= MAX_PROMOTIONS_PER_LANE:
            continue
        selected.append(row)
        selected_formulas.add(formula)
        lane_counts[lane_id] = lane_counts.get(lane_id, 0) + 1

    return selected


def build_public_record(candidate: dict) -> dict:
    formula = str(candidate.get("formula") or "").strip()
    config = PROMOTION_OVERRIDES.get(formula, {})
    config = {**KNOWN_BASELINE_PROMOTIONS.get(formula, {}), **config}
    risk_tags = list(dict.fromkeys(config.get("risk_tags", candidate.get("risk_tags", [])) or []))
    branch = str(candidate.get("branch") or "")
    lane_id = lane_of(candidate)
    return {
        "record_id": stable_record_id(candidate, formula, lane_id),
        "track": "B",
        "formula": formula,
        "normalized_formula": formula,
        "material_class": config.get("material_class", f"{lane_id} exploratory candidate"),
        "branch_or_family": lane_id,
        "structure_or_prototype_note": config.get(
            "structure_or_prototype_note",
            f"Loop-promoted {lane_id} candidate retained with explicit DFT-screened exploratory semantics.",
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
        "record_role": config.get("record_role", "exploratory_candidate"),
        "superconductivity_status": config.get("superconductivity_status", "unconfirmed_candidate"),
        "novelty_class": config.get("novelty_class", "loop_generated_variant"),
        "promotion_gate": config.get("promotion_gate", "ready_for_next_generation"),
        "mechanism_risk": config.get("mechanism_risk", []),
        "claim_level": config.get("claim_level", "dft_screened_not_tc_claim"),
        "next_action": config.get("next_action", "bounded_dft_followup"),
        "discovery_score_public": candidate.get("discovery_score"),
        "phase_or_condition_id": config.get("phase_or_condition_id", f"{formula.lower()}_loop_variant"),
        "exclude_from_new_discovery_leaderboard": config.get("exclude_from_new_discovery_leaderboard", False),
        "include_in_family_anchor_board": config.get("include_in_family_anchor_board", False),
        "avoid_rule": None,
        "allowed_escape_routes": ["structure_proxy_upgrade", "structured_lane_promotion", "bounded_dft_followup"],
        "candidate_layer": str(candidate.get("candidate_layer") or "promotion_ready"),
        "candidate_quantity_score": float(candidate.get("candidate_quantity_score") or 74.0),
        "candidate_quality_score": float(candidate.get("candidate_quality_score") or 70.0),
        "entry_block_reason": candidate.get("entry_block_reason"),
        "upgrade_requirements": candidate.get("upgrade_requirements", ["bounded_dft_followup"]),
        "family_ruleset_id": candidate.get("family_ruleset_id", "ruleset_generic_reference_v1"),
        "lane_id": lane_id,
        "validation_recipe_id": candidate.get("validation_recipe_id"),
        "condition_class": candidate.get("condition_class"),
        "required_condition_vector": candidate.get("required_condition_vector", []),
    }


def promote_candidates(limit: int) -> list[dict[str, str]]:
    corpus_rows = load_jsonl(CORPUS)
    existing = {row.get("formula", "") for row in corpus_rows}
    counts = corpus_lane_counts(corpus_rows)
    state = loop_state()
    promoted: list[dict[str, str]] = []
    chosen = select_lane_aware_candidates(eligible_candidates(state, existing), limit, counts)
    for row in chosen:
        corpus_rows.append(build_public_record(row))
        existing.add(row["formula"])
        promoted.append({"formula": row["formula"], "lane_id": lane_of(row)})
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


def maybe_checkpoint(promoted: list[dict[str, str]], expanded: bool) -> None:
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
        promoted_labels = [f"{item['formula']}[{item['lane_id']}]" for item in promoted]
        summary_bits.append(f"promote {' '.join(promoted_labels)}")
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
    lane_counts = corpus_lane_counts(load_jsonl(CORPUS))
    growth = ensure_growth_target(public_count)
    trajectory = target_progress(growth, public_count)
    thinnest_lanes = sorted(LANE_ORDER, key=lambda lane_id: (lane_counts.get(lane_id, 0), lane_id))[:4]

    lines = [
        f"weekly_target: {public_count}/{growth['target_public_count']} public records, shortfall_now={trajectory['shortfall_now']}, daily_growth_needed={trajectory['daily_growth_needed']}",
        "family_balance_frontier: " + ", ".join(f"{lane_id}={lane_counts.get(lane_id, 0)}" for lane_id in thinnest_lanes),
    ]
    recovery = watchdog_recovery_plan(state)
    if recovery["should_recover"]:
        lines.append(
            "watchdog_escalation: "
            f"level={recovery['level']}, maintenance_streak={recovery['maintenance_streak']}, "
            f"hours_since_advance={recovery['hours_since_advance']}, stale_anchor={recovery['stale_anchor']}"
        )
        if recovery["actions"]:
            lines.append("watchdog_actions: " + ", ".join(recovery["actions"]))

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
        lines.append(
            "advance_corpus: promoted "
            + ", ".join(f"{item['formula']}[{item['lane_id']}]" for item in promoted)
        )
        run_script("optimize_discovery_corpus.py")
        run_script("update_loop_state.py")
        run_script("export_discovery_feed.py")
    else:
        lines.append("no_corpus_promotion: no eligible queue-driven row found")
        recovery = watchdog_recovery_plan(state)
        if recovery["should_recover"]:
            lines.append("watchdog_retry: forcing same-cycle manifest recovery and second promotion attempt")
            retry_notes = maybe_expand_manifest(state, trajectory)
            if retry_notes:
                lines.extend([f"retry_{note}" for note in retry_notes])
                run_script("optimize_discovery_corpus.py")
                run_script("update_loop_state.py")
                run_script("export_discovery_feed.py")
                state = loop_state()
                retry_promoted = promote_candidates(promotion_limit)
                if retry_promoted:
                    promoted = retry_promoted
                    lines.append(
                        "advance_corpus_after_retry: promoted "
                        + ", ".join(f"{item['formula']}[{item['lane_id']}]" for item in retry_promoted)
                    )
                    run_script("optimize_discovery_corpus.py")
                    run_script("update_loop_state.py")
                    run_script("export_discovery_feed.py")
                else:
                    lines.append("watchdog_retry_result: still no eligible queue-driven row after forced recovery")

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
