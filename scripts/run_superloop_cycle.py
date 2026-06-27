#!/usr/bin/env python3
"""Execute one substantive SC SuperLoop cycle.

This orchestrator exists to prevent report-refresh-only cycles.
It prefers one concrete advance per run:

1. promote a safe new DFT-screened record into the public corpus when the
   corpus is still below the configured target
2. refresh corpus / loop state / discovery exports
3. emit a compact cycle log
4. checkpoint meaningful changes
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

SC_ROOT = Path("/data/.openclaw/workspace/research/SC_SuperLoop")
REPORTS = SC_ROOT / "reports"
SCRIPTS = SC_ROOT / "scripts"
CORPUS = SC_ROOT / "knowledge" / "credible_superconductors.jsonl"
MANIFEST = SC_ROOT / "candidates" / datetime.now(timezone.utc).date().isoformat() / "candidate_manifest_prescreened.jsonl"
CYCLE_LOG = REPORTS / "superloop_cycle_log.md"

TARGET_PUBLIC_COUNT = 40
PROMOTION_LIMIT = 2


PROMOTION_CONFIGS = {
    "LaPdO2": {
        "material_class": "infinite-layer palladate analog",
        "structure_or_prototype_note": "4d infinite-layer palladate comparator retained as a wider-band boundary test for the charge-transfer lane.",
        "superconductivity_context": "Prescreen-stage 4d infinite-layer comparator retained as a bounded charge-transfer boundary test, not as a confirmed superconductivity claim.",
        "condition_note": "This is a DFT-screened exploratory record only; it is kept visible because it tests whether the 4d route loses the desired confinement too early.",
        "mechanism_note": "4d infinite-layer boundary comparator for the nickelate/cuprate mainline.",
        "risk_tags": ["strong_correlation_risk", "carrier_density_sensitive", "conjecture_only", "wider_band_risk", "palladate_comparator"],
        "next_action": "keep_as_4d_boundary_comparator",
        "phase_or_condition_id": "infinite_layer_palladate_boundary_test",
        "mechanism_risk": ["strong_correlation", "wider_band_risk"],
        "promotion_gate": "require_structure_validation",
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
        "promotion_gate": "require_structure_validation",
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
        "promotion_gate": "require_structure_validation",
    },
    "KTaO3": {
        "material_class": "d0 oxide perovskite",
        "structure_or_prototype_note": "KTaO3 perovskite retained as a dilute-carrier oxide-side-branch candidate with SOC relevance.",
        "superconductivity_context": "Prescreen-stage KTaO3-derived oxide candidate retained for the low-density superconductivity side branch.",
        "condition_note": "This is a DFT-screened exploratory record only; relevant superconducting interpretations depend on explicit low-density/interface conditions.",
        "mechanism_note": "SOC-relevant oxide-side benchmark within the dilute-carrier family.",
        "risk_tags": ["carrier_density_sensitive", "interface_required", "soc_relevant", "oxide_side_branch"],
        "next_action": "promote_to_oxide_structured_queue",
        "phase_or_condition_id": "low_density_kto",
        "mechanism_risk": ["carrier_density_sensitive", "soc_relevant"],
        "promotion_gate": "require_structure_validation",
    },
    "BaTiO3": {
        "material_class": "ferroelectric oxide perovskite",
        "structure_or_prototype_note": "BaTiO3 perovskite retained as a ferroelectric-proximity oxide-side-branch comparator.",
        "superconductivity_context": "Prescreen-stage oxide comparator retained to test the ferroelectric-proximity side route.",
        "condition_note": "This is a DFT-screened exploratory record only; no direct superconductivity claim is implied for bulk stoichiometric BaTiO3.",
        "mechanism_note": "Ferroelectric-side comparator rather than a mainline room-temperature candidate.",
        "risk_tags": ["carrier_density_sensitive", "oxide_side_branch", "conjecture_only"],
        "next_action": "promote_to_oxide_structured_queue",
        "phase_or_condition_id": "ferroelectric_oxide_comparator",
        "mechanism_risk": ["carrier_density_sensitive"],
        "promotion_gate": "require_structure_validation",
    },
}


def run_script(script_name: str) -> None:
    subprocess.run(["python3", str(SCRIPTS / script_name)], cwd=SC_ROOT, check=True)


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def best_manifest_rows() -> dict[str, dict]:
    rows = load_jsonl(MANIFEST)
    best: dict[str, dict] = {}
    for row in rows:
        formula = row.get("formula", "")
        current = best.get(formula)
        if current is None or (
            float(row.get("prescreen_score") or 0.0),
            float(row.get("discovery_score") or 0.0),
        ) > (
            float(current.get("prescreen_score") or 0.0),
            float(current.get("discovery_score") or 0.0),
        ):
            best[formula] = row
    return best


def make_public_record(candidate: dict) -> dict | None:
    formula = candidate.get("formula", "")
    config = PROMOTION_CONFIGS.get(formula)
    if not config:
        return None
    return {
        "record_id": f"track-b-{str(candidate.get('candidate_id')).lower()}",
        "track": "B",
        "formula": formula,
        "normalized_formula": formula,
        "material_class": config["material_class"],
        "branch_or_family": candidate.get("branch", ""),
        "structure_or_prototype_note": config["structure_or_prototype_note"],
        "evidence_class": "DFT-screened",
        "superconductivity_context": config["superconductivity_context"],
        "Tc_value_or_range": None,
        "condition_note": config["condition_note"],
        "mechanism_note": config["mechanism_note"],
        "risk_tags": config["risk_tags"],
        "source_citation": f"SC SuperLoop prescreen candidate {candidate.get('candidate_id')}",
        "source_type": "internal_dft_screen",
        "review_status": "pending",
        "record_role": "exploratory_candidate",
        "superconductivity_status": "unconfirmed_candidate",
        "novelty_class": "loop_generated_variant",
        "promotion_gate": config["promotion_gate"],
        "mechanism_risk": config["mechanism_risk"],
        "claim_level": "dft_screened_not_tc_claim",
        "next_action": config["next_action"],
        "discovery_score_public": candidate.get("discovery_score"),
        "phase_or_condition_id": config["phase_or_condition_id"],
        "exclude_from_new_discovery_leaderboard": False,
        "include_in_family_anchor_board": False,
        "avoid_rule": None,
        "allowed_escape_routes": ["structure_proxy_upgrade", "structured_lane_promotion"],
        "candidate_layer": "promotion_ready",
        "candidate_quantity_score": 74.0,
        "candidate_quality_score": 70.0,
        "entry_block_reason": None,
        "upgrade_requirements": ["bounded_dft_followup"],
        "family_ruleset_id": "ruleset_single_orbital_charge_transfer_v1" if candidate.get("branch") == "cuprate_extrapolation" else candidate.get("family_ruleset_id", "ruleset_generic_reference_v1"),
    }


def promote_next_public_records(limit: int = PROMOTION_LIMIT) -> list[str]:
    corpus_rows = load_jsonl(CORPUS)
    existing = {row.get("formula", "") for row in corpus_rows}
    best_rows = best_manifest_rows()
    promoted: list[str] = []
    priority = ["LaPdO2", "SrTiO3", "CaTiO3", "KTaO3", "BaTiO3"]
    for formula in priority:
        if len(existing) >= TARGET_PUBLIC_COUNT or len(promoted) >= limit:
            break
        if formula in existing or formula not in best_rows:
            continue
        candidate = best_rows[formula]
        if float(candidate.get("prescreen_score") or 0.0) < 50.0:
            continue
        record = make_public_record(candidate)
        if not record:
            continue
        corpus_rows.append(record)
        existing.add(formula)
        promoted.append(formula)
    if promoted:
        write_jsonl(CORPUS, corpus_rows)
    return promoted


def append_cycle_log(lines: list[str]) -> None:
    stamp = datetime.now(timezone.utc).isoformat()
    prefix = [f"## Cycle {stamp}", ""]
    block = "\n".join(prefix + [f"- {line}" for line in lines] + [""])
    with CYCLE_LOG.open("a", encoding="utf-8") as handle:
        handle.write(block)


def maybe_checkpoint(promoted: list[str]) -> None:
    if not promoted:
        return
    subprocess.run(["git", "-C", str(SC_ROOT), "add", "knowledge/credible_superconductors.jsonl", "reports/discovery_feed.json", "reports/discovery_meta.json", "reports/loop_state.json", "reports/loop_state.md", "reports/dft_queue_status.md", "reports/manifest_candidate_funnel.md", "reports/upgrade_execution_queue.md", "reports/superloop_runtime_state.json", "reports/superloop_health.md"], check=True)
    subprocess.run(["git", "-C", str(SC_ROOT), "commit", "-m", f"Night cycle promote {' '.join(promoted)} into discovery feed"], check=True)


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    run_script("optimize_discovery_corpus.py")
    run_script("update_loop_state.py")
    run_script("export_discovery_feed.py")

    promoted = promote_next_public_records()
    if promoted:
        run_script("optimize_discovery_corpus.py")
        run_script("update_loop_state.py")
        run_script("export_discovery_feed.py")

    lines = []
    if promoted:
        lines.append(f"advance_corpus: promoted {', '.join(promoted)}")
    else:
        lines.append("no_corpus_promotion: no eligible priority row found")

    health = REPORTS / "superloop_health.md"
    if health.exists():
        lines.append("health_report_refreshed")

    append_cycle_log(lines)
    maybe_checkpoint(promoted)


if __name__ == "__main__":
    main()
