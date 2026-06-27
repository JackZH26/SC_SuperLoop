#!/usr/bin/env python3
"""Apply discovery-corpus classification upgrades and generate board reports."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

SC_ROOT = Path("/data/.openclaw/workspace/research/SC_SuperLoop")
REGISTRY = SC_ROOT / "knowledge" / "credible_superconductors.jsonl"
REPORTS = SC_ROOT / "reports"
KNOWLEDGE = SC_ROOT / "knowledge"
GENERATED_DATE = datetime.now(timezone.utc).date().isoformat()


def load_records() -> list[dict]:
    rows = []
    for line in REGISTRY.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def classify(record: dict) -> dict:
    rid = record["record_id"]
    formula = record["formula"]

    defaults = {
        # Preserve explicit per-record semantics when they already exist.
        # Falling back to reference-anchor defaults for unknown rows caused
        # newly promoted exploratory records to be silently collapsed into
        # passive anchors, which kills forward loop motion.
        "record_role": record.get("record_role", "reference_anchor"),
        "superconductivity_status": record.get("superconductivity_status", "confirmed_superconductor"),
        "novelty_class": record.get("novelty_class", "known_reference"),
        "promotion_gate": record.get("promotion_gate", "ready_for_next_generation"),
        "mechanism_risk": record.get("mechanism_risk", []),
        "claim_level": record.get("claim_level", "reference_only"),
        "next_action": record.get("next_action", "use_as_family_anchor"),
        "discovery_score_public": record.get("discovery_score_public"),
        "phase_or_condition_id": record.get("phase_or_condition_id"),
        "exclude_from_new_discovery_leaderboard": record.get("exclude_from_new_discovery_leaderboard", True),
        "include_in_family_anchor_board": record.get("include_in_family_anchor_board", True),
        "avoid_rule": record.get("avoid_rule"),
        "allowed_escape_routes": record.get("allowed_escape_routes", []),
    }

    if rid == "track-b-e0-2026-06-25-0029":  # TiN
        defaults.update(
            {
                "record_role": "benchmark_control",
                "superconductivity_status": "confirmed_superconductor",
                "novelty_class": "known_reference",
                "promotion_gate": "require_literature_source",
                "mechanism_risk": ["conventional_epc", "disorder_sensitive"],
                "claim_level": "dft_screened_not_tc_claim",
                "next_action": "attach_primary_tin_superconductivity_source",
                "discovery_score_public": None,
                "phase_or_condition_id": "rocksalt_tin_film_context",
                "exclude_from_new_discovery_leaderboard": True,
                "include_in_family_anchor_board": True,
            }
        )
    elif rid == "track-b-e0-2026-06-25-0095":  # NbB2
        defaults.update(
            {
                "record_role": "conditional_candidate",
                "superconductivity_status": "unconfirmed_candidate",
                "novelty_class": "known_family_new_variant",
                "promotion_gate": "require_free_cell_relax",
                "mechanism_risk": ["conventional_epc", "phase_sensitive"],
                "claim_level": "conditional_candidate",
                "next_action": "run_free_cell_relax_and_eos_mini_scan",
                "discovery_score_public": 74.0,
                "phase_or_condition_id": "alb2_type_fixed_cell_proxy",
                "exclude_from_new_discovery_leaderboard": False,
                "include_in_family_anchor_board": False,
            }
        )
    elif rid == "track-b-e0-2026-06-25-0273":  # MoB2
        defaults.update(
            {
                "record_role": "conditional_candidate",
                "superconductivity_status": "unconfirmed_candidate",
                "novelty_class": "known_family_new_variant",
                "promotion_gate": "require_structure_validation",
                "mechanism_risk": ["phase_sensitive", "conventional_epc"],
                "claim_level": "conditional_candidate",
                "next_action": "split_mob2_by_phase_before_any_promotion",
                "discovery_score_public": 66.0,
                "phase_or_condition_id": "mob2_phase_unresolved",
                "exclude_from_new_discovery_leaderboard": False,
                "include_in_family_anchor_board": False,
            }
        )
    elif rid in {
        "track-b-e0-2026-06-25-0103",  # TiB2
        "track-b-e0-2026-06-25-0177",  # ZrB2
        "track-b-e0-2026-06-25-0091",  # WB2
    }:
        avoid = {
            "TiB2": "do_not_promote_stoichiometric_tib2_without_positive_dos_at_ef",
            "ZrB2": "do_not_promote_stoichiometric_zrb2_without_positive_dos_at_ef",
            "WB2": "do_not_promote_stoichiometric_wb2_without_positive_dos_at_ef",
        }[formula]
        defaults.update(
            {
                "record_role": "negative_control",
                "superconductivity_status": "likely_not_candidate_in_current_phase",
                "novelty_class": "negative_control",
                "promotion_gate": "no_promotion",
                "mechanism_risk": ["phase_sensitive"],
                "claim_level": "negative_control",
                "next_action": "write_failure_memory_and_block_phonon_promotion",
                "discovery_score_public": None,
                "phase_or_condition_id": "current_stoichiometric_alb2_proxy",
                "exclude_from_new_discovery_leaderboard": True,
                "include_in_family_anchor_board": False,
                "avoid_rule": avoid,
                "allowed_escape_routes": [
                    "doped_variant",
                    "pressure_variant",
                    "different_phase",
                    "b_c_n_framework_derivative",
                ],
            }
        )
    elif formula in {"MgB2", "Pb", "Nb", "Nb3Sn"}:
        defaults.update(
            {
                "record_role": "benchmark_control",
                "superconductivity_status": "confirmed_superconductor",
                "novelty_class": "known_reference",
                "promotion_gate": "ready_for_next_generation",
                "mechanism_risk": ["conventional_epc"],
                "claim_level": "benchmark_only",
                "next_action": "use_as_calibration_and_generator_anchor",
            }
        )
    elif formula in {"Li_xZrNCl", "Li_xHfNCl", "Ba8Si46", "LaO1-xFxFeAs", "Ba1-xKxFe2As2", "SmFeAsO1-xFx", "Mo3Sb7", "Ba0.6K0.4BiO3"}:
        mechanism_risk = {
            "Li_xZrNCl": ["doping_required", "interface_required"],
            "Li_xHfNCl": ["doping_required", "interface_required"],
            "Ba8Si46": ["conventional_epc"],
            "LaO1-xFxFeAs": ["spin_fluctuation", "doping_required"],
            "Ba1-xKxFe2As2": ["spin_fluctuation", "doping_required"],
            "SmFeAsO1-xFx": ["spin_fluctuation", "doping_required"],
            "Mo3Sb7": ["conventional_epc", "phase_sensitive"],
            "Ba0.6K0.4BiO3": ["doping_required", "oxygen_stoichiometry_sensitive"],
        }[formula]
        defaults.update(
            {
                "record_role": "reference_anchor",
                "superconductivity_status": "confirmed_superconductor",
                "novelty_class": "known_reference",
                "promotion_gate": "ready_for_next_generation",
                "mechanism_risk": mechanism_risk,
                "claim_level": "reference_only",
                "next_action": "use_as_family_anchor",
            }
        )
    elif formula in {"CsV3Sb5", "FeSe", "LiFeAs", "Cu_xBi2Se3", "La2-xBaxCuO4", "YBa2Cu3O7-delta", "Sr2RuO4", "CeCu2Si2", "UBe13"}:
        mechanism_risk = {
            "CsV3Sb5": ["strong_correlation", "topology_sensitive"],
            "FeSe": ["spin_fluctuation", "phase_sensitive"],
            "LiFeAs": ["spin_fluctuation"],
            "Cu_xBi2Se3": ["doping_required", "topology_sensitive", "disorder_sensitive"],
            "La2-xBaxCuO4": ["strong_correlation", "doping_required"],
            "YBa2Cu3O7-delta": ["strong_correlation", "oxygen_stoichiometry_sensitive"],
            "Sr2RuO4": ["disorder_sensitive", "strong_correlation"],
            "CeCu2Si2": ["strong_correlation", "heavy_fermion"],
            "UBe13": ["strong_correlation", "heavy_fermion", "disorder_sensitive"],
        }[formula]
        defaults.update(
            {
                "record_role": "mechanism_anchor",
                "superconductivity_status": "confirmed_superconductor",
                "novelty_class": "known_reference",
                "promotion_gate": "ready_for_next_generation",
                "mechanism_risk": mechanism_risk,
                "claim_level": "reference_only",
                "next_action": "use_as_mechanism_preserving_generator_anchor",
            }
        )
    elif formula in {"Nd0.8Sr0.2NiO2", "NdNiO2", "PrNiO2", "Ba2NiO2F2", "La2PdO4", "LaPdO2", "AgF2", "Cs2AgF4"}:
        explicit = {
            "Nd0.8Sr0.2NiO2": {
                "record_role": "exploratory_candidate",
                "superconductivity_status": "unconfirmed_candidate",
                "novelty_class": "loop_generated_variant",
                "promotion_gate": "require_structure_validation",
                "mechanism_risk": ["strong_correlation", "doping_required"],
                "claim_level": "dft_screened_not_tc_claim",
                "next_action": "promote_to_structured_nickelate_queue",
                "discovery_score_public": 62.0,
                "phase_or_condition_id": "sr_doped_infinite_layer_nickelate",
                "exclude_from_new_discovery_leaderboard": False,
                "include_in_family_anchor_board": False,
            },
            "NdNiO2": {
                "record_role": "exploratory_candidate",
                "superconductivity_status": "unconfirmed_candidate",
                "novelty_class": "loop_generated_variant",
                "promotion_gate": "require_doping_context",
                "mechanism_risk": ["strong_correlation", "doping_required"],
                "claim_level": "dft_screened_not_tc_claim",
                "next_action": "keep_as_parent_comparator_and_link_to_doped_nickelate_rows",
                "discovery_score_public": 59.6,
                "phase_or_condition_id": "parent_infinite_layer_nickelate",
                "exclude_from_new_discovery_leaderboard": False,
                "include_in_family_anchor_board": False,
            },
            "PrNiO2": {
                "record_role": "exploratory_candidate",
                "superconductivity_status": "unconfirmed_candidate",
                "novelty_class": "loop_generated_variant",
                "promotion_gate": "require_doping_context",
                "mechanism_risk": ["strong_correlation", "doping_required"],
                "claim_level": "dft_screened_not_tc_claim",
                "next_action": "keep_as_rare_earth_comparator",
                "discovery_score_public": 59.6,
                "phase_or_condition_id": "pr_infinite_layer_nickelate_parent",
                "exclude_from_new_discovery_leaderboard": False,
                "include_in_family_anchor_board": False,
            },
            "Ba2NiO2F2": {
                "record_role": "exploratory_candidate",
                "superconductivity_status": "unconfirmed_candidate",
                "novelty_class": "loop_generated_variant",
                "promotion_gate": "require_structure_validation",
                "mechanism_risk": ["strong_correlation", "ligand_field_sensitive"],
                "claim_level": "dft_screened_not_tc_claim",
                "next_action": "promote_to_square_ligand_structured_queue",
                "discovery_score_public": 57.2,
                "phase_or_condition_id": "square_ligand_nickel_oxyfluoride",
                "exclude_from_new_discovery_leaderboard": False,
                "include_in_family_anchor_board": False,
            },
            "La2PdO4": {
                "record_role": "exploratory_candidate",
                "superconductivity_status": "unconfirmed_candidate",
                "novelty_class": "loop_generated_variant",
                "promotion_gate": "require_structure_validation",
                "mechanism_risk": ["strong_correlation", "wider_band_risk"],
                "claim_level": "dft_screened_not_tc_claim",
                "next_action": "keep_as_4d_boundary_comparator",
                "discovery_score_public": 54.2,
                "phase_or_condition_id": "214_palladate_boundary_test",
                "exclude_from_new_discovery_leaderboard": False,
                "include_in_family_anchor_board": False,
            },
            "LaPdO2": {
                "record_role": "exploratory_candidate",
                "superconductivity_status": "unconfirmed_candidate",
                "novelty_class": "loop_generated_variant",
                "promotion_gate": "require_structure_validation",
                "mechanism_risk": ["strong_correlation", "wider_band_risk"],
                "claim_level": "dft_screened_not_tc_claim",
                "next_action": "keep_as_4d_boundary_comparator",
                "discovery_score_public": 51.2,
                "phase_or_condition_id": "infinite_layer_palladate_boundary_test",
                "exclude_from_new_discovery_leaderboard": False,
                "include_in_family_anchor_board": False,
            },
            "AgF2": {
                "record_role": "exploratory_candidate",
                "superconductivity_status": "unconfirmed_candidate",
                "novelty_class": "loop_generated_variant",
                "promotion_gate": "require_structure_validation",
                "mechanism_risk": ["strong_correlation", "ligand_field_sensitive"],
                "claim_level": "dft_screened_not_tc_claim",
                "next_action": "promote_to_square_ligand_structured_queue",
                "discovery_score_public": record.get("discovery_score_public"),
                "phase_or_condition_id": "silver_fluoride_square_ligand_test",
                "exclude_from_new_discovery_leaderboard": False,
                "include_in_family_anchor_board": False,
            },
            "Cs2AgF4": {
                "record_role": "exploratory_candidate",
                "superconductivity_status": "unconfirmed_candidate",
                "novelty_class": "loop_generated_variant",
                "promotion_gate": "require_structure_validation",
                "mechanism_risk": ["strong_correlation", "ligand_field_sensitive"],
                "claim_level": "dft_screened_not_tc_claim",
                "next_action": "promote_to_square_ligand_structured_queue",
                "discovery_score_public": record.get("discovery_score_public"),
                "phase_or_condition_id": "layered_silver_fluoride_test",
                "exclude_from_new_discovery_leaderboard": False,
                "include_in_family_anchor_board": False,
            },
        }[formula]
        defaults.update(explicit)

    if defaults["record_role"] == "negative_control":
        record.setdefault("risk_tags", [])
        for tag in ["negative_control", "failed_memory"]:
            if tag not in record["risk_tags"]:
                record["risk_tags"].append(tag)

    if defaults["record_role"] == "conditional_candidate":
        record.setdefault("risk_tags", [])
        if "conditional_candidate" not in record["risk_tags"]:
            record["risk_tags"].append("conditional_candidate")

    if formula == "TiN":
        record["source_citation"] = "Zhang et al., Applied Physics Letters 124, 182601 (2024), doi:10.1063/5.0207852"
        record["source_type"] = "primary_literature"
        record["Tc_value_or_range"] = "up to 5.3 K"
        record["condition_note"] = "This reference context is film- and orientation-sensitive TiN; do not generalize the quoted Tc to arbitrary TiN morphologies or disorder regimes."
        record["review_status"] = "verified"
        record["risk_tags"] = [tag for tag in record["risk_tags"] if tag != "experimental_tc_unverified"]

    record.update(defaults)
    record.update(assign_funnel_fields(record))
    return record


def assign_funnel_fields(record: dict) -> dict:
    formula = record["formula"]
    role = record.get("record_role")
    gate = record.get("promotion_gate")
    branch = record.get("branch_or_family", "")
    risk_tags = set(record.get("risk_tags", []))

    family_ruleset_map = {
        "AlB2_MgB2_boride": "ruleset_diboride_mechanism_preserving_v1",
        "AlTiPbW_exploratory": "ruleset_transition_metal_binary_v1",
        "MXene_2D": "ruleset_mxene_layered_carbide_v1",
        "iron_based_extrapolation": "ruleset_iron_based_mechanism_preserving_v1",
        "cuprate_extrapolation": "ruleset_cuprate_condition_preserving_v1",
        "layered_nitride_halonitride": "ruleset_layered_nitride_intercalation_v1",
        "fulleride_molecular": "ruleset_fulleride_condition_preserving_v1",
        "graphite_intercalation": "ruleset_intercalation_layered_v1",
    }
    family_ruleset_id = record.get("family_ruleset_id") or family_ruleset_map.get(branch, "ruleset_generic_reference_v1")
    if branch == "cuprate_extrapolation" and formula in {
        "Nd0.8Sr0.2NiO2",
        "NdNiO2",
        "PrNiO2",
        "Ba2NiO2F2",
        "La2PdO4",
        "LaPdO2",
        "AgF2",
        "Cs2AgF4",
    }:
        family_ruleset_id = "ruleset_single_orbital_charge_transfer_v1"

    quantity = 60.0
    quality = 35.0
    entry_block_reason = None
    upgrade_requirements: list[str] = []
    candidate_layer = "broad"

    if role in {"reference_anchor", "mechanism_anchor", "benchmark_control"}:
        quantity = 92.0
        quality = 88.0
        candidate_layer = "structured"
        upgrade_requirements = ["retain_as_family_anchor"]
    elif role == "negative_control":
        quantity = 58.0
        quality = 22.0
        candidate_layer = "structured"
        entry_block_reason = "negative_control"
        upgrade_requirements = ["record_avoid_rule", "explore_only_escape_routes"]
    elif role == "conditional_candidate":
        quantity = 78.0
        quality = 61.0
        candidate_layer = "structured"
        if gate == "require_free_cell_relax":
            entry_block_reason = "structural_minimum_unresolved"
            upgrade_requirements = ["free_cell_relax", "eos_mini_scan", "phase_consistency_check"]
        elif gate == "require_structure_validation":
            entry_block_reason = "phase_ambiguity"
            upgrade_requirements = ["phase_split", "structure_validation", "prototype_specific_followup"]
        else:
            upgrade_requirements = ["gate_clearance_review"]
    elif role == "exploratory_candidate":
        quantity = 74.0
        quality = 70.0
        candidate_layer = "promotion_ready"
        upgrade_requirements = ["bounded_dft_followup"]

    if "doping_required" in risk_tags:
        quantity += 4.0
        quality += 3.0
    if "mechanism_complex" in risk_tags or "strong_correlation" in risk_tags:
        quantity += 2.0
    if "phase_sensitive" in risk_tags and role not in {"reference_anchor", "mechanism_anchor"}:
        quality -= 8.0
    if "conditional_candidate" in risk_tags:
        quality -= 4.0

    if formula == "Mo2C":
        candidate_layer = "broad"
        entry_block_reason = "no_structure_proxy"
        quantity = 84.0
        quality = 46.0
        upgrade_requirements = ["attach_verified_structure_proxy", "prototype_verification", "condition_scope_check"]

    if gate in {"ready_for_next_generation", "benchmark_complete"} and role in {"reference_anchor", "mechanism_anchor", "benchmark_control"}:
        upgrade_requirements = ["reference_maintenance_only"]

    quality = max(0.0, min(99.0, quality))
    quantity = max(0.0, min(99.0, quantity))

    return {
        "candidate_layer": candidate_layer,
        "candidate_quantity_score": round(quantity, 1),
        "candidate_quality_score": round(quality, 1),
        "entry_block_reason": entry_block_reason,
        "upgrade_requirements": upgrade_requirements,
        "family_ruleset_id": family_ruleset_id,
    }


def write_registry(records: list[dict]) -> None:
    REGISTRY.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in records) + "\n",
        encoding="utf-8",
    )


def write_board(name: str, title: str, records: list[dict], extra_note: str | None = None) -> None:
    lines = [f"# {title}", "", f"Updated: {GENERATED_DATE}", ""]
    if extra_note:
        lines += [extra_note, ""]
    if not records:
        lines += ["No records currently assigned.", ""]
    else:
        lines += ["| Formula | Role | Claim | Next Action | Key Caveat |", "|---|---|---|---|---|"]
        for row in records:
            caveat = row.get("condition_note") or row.get("avoid_rule") or "-"
            lines.append(
                f"| {row['formula']} | {row['record_role']} | {row['claim_level']} | {row['next_action']} | {str(caveat).replace('|', '/')} |"
            )
        lines.append("")
    (REPORTS / name).write_text("\n".join(lines), encoding="utf-8")


def write_funnel_board(name: str, title: str, records: list[dict], note: str) -> None:
    lines = [f"# {title}", "", f"Updated: {GENERATED_DATE}", "", note, ""]
    lines += ["| Formula | Layer | Quantity | Quality | Entry Block | Upgrade Requirements |", "|---|---|---|---|---|---|"]
    for row in records:
        lines.append(
            f"| {row['formula']} | {row['candidate_layer']} | {row['candidate_quantity_score']} | "
            f"{row['candidate_quality_score']} | {row.get('entry_block_reason') or '-'} | "
            f"{', '.join(row.get('upgrade_requirements', [])) or '-'} |"
        )
    lines.append("")
    (REPORTS / name).write_text("\n".join(lines), encoding="utf-8")


def write_failed_memory(records: list[dict]) -> None:
    lines = [
        "# Failed Memory",
        "",
        f"Updated: {GENERATED_DATE}",
        "",
        "| Formula | Failed Stage | Failure Reason | Avoid Rule | Allowed Escape Routes |",
        "|---|---|---|---|---|",
    ]
    for row in records:
        lines.append(
            f"| {row['formula']} | DFT-screened DOS | {'; '.join(row.get('risk_tags', []))} | {row.get('avoid_rule') or '-'} | {', '.join(row.get('allowed_escape_routes', [])) or '-'} |"
        )
    lines.append("")
    (REPORTS / "failed_memory.md").write_text("\n".join(lines), encoding="utf-8")
    (REPORTS / "negative_controls.md").write_text("\n".join(lines), encoding="utf-8")

    failed_patterns = []
    for row in records:
        failed_patterns.append(
            {
                "formula": row["formula"],
                "branch": row["branch_or_family"],
                "failed_stage": "DFT-screened DOS",
                "failure_reason": ",".join(row.get("risk_tags", [])),
                "avoid_rule": row.get("avoid_rule"),
                "allowed_escape_routes": row.get("allowed_escape_routes", []),
            }
        )
    try:
        import pandas as pd  # type: ignore

        pd.DataFrame(failed_patterns).to_parquet(
            SC_ROOT / "knowledge" / "failed_patterns.parquet",
            index=False,
        )
    except Exception:
        (SC_ROOT / "knowledge" / "failed_patterns.json").write_text(
            json.dumps(failed_patterns, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


def fmt_score(value: float | int | None) -> str:
    if value is None:
        return "Insufficient data"
    return f"{float(value):.1f}"


def write_blockers(records: list[dict]) -> None:
    lines = [
        "# Blockers",
        "",
        f"Updated: {GENERATED_DATE}",
        "",
        "| Item | Blocker | Continue With |",
        "|---|---|---|",
        "| NbB2 | structural minimum unresolved; needs free-cell relax and EOS mini scan before phonon promotion | continue reference-anchor expansion and phase-specific candidate generation |",
        "| MoB2 | phase-sensitive record flattened into one formula; needs phase split before promotion | continue negative-control memory routing and mechanism-anchor generation |",
    ]
    if any(r["formula"] == "TiN" and r["promotion_gate"] == "require_literature_source" for r in records):
        lines.append("| TiN | external superconductivity source needed before pure reference-only wording | continue benchmark / reference boards in parallel |")
    lines.append("")
    (REPORTS / "blockers.md").write_text("\n".join(lines), encoding="utf-8")


def update_status(records: list[dict]) -> None:
    total = len(records)
    track_a = sum(1 for r in records if r["track"] == "A")
    track_b = sum(1 for r in records if r["track"] == "B")
    track_c = sum(1 for r in records if r["track"] == "C")
    broad = sum(1 for r in records if r["candidate_layer"] == "broad")
    structured = sum(1 for r in records if r["candidate_layer"] == "structured")
    promotion_ready = sum(1 for r in records if r["candidate_layer"] == "promotion_ready")
    text = f"""# Credible Superconductors Corpus Status

Updated: {GENERATED_DATE}

## Goal

Build a 100-record scientifically credible superconducting-material corpus.

## Current Counts

- total credible corpus records: {total}
- Track A literature-backed references: {track_a} / 70
- Track B loop-verified exploratory records: {track_b} / 20
- Track C benchmark-adjacent / review anchors: {track_c} / 10

## Funnel Counts

- Broad candidate pool: {broad}
- Structured candidate pool: {structured}
- Promotion-ready pool: {promotion_ready}

## Registry Source

- canonical registry: `knowledge/credible_superconductors.jsonl`
- this count intentionally mixes source-backed literature/reference records with reviewed SC SuperLoop `DFT-screened` records

## Current Rule

Do not optimize for "100 discoveries".
Optimize for "100 scientifically credible superconducting-material records" with explicit evidence labels.

## Classification Completion

- all records now carry: `record_role`, `superconductivity_status`, `novelty_class`, `promotion_gate`, `mechanism_risk`, `claim_level`, and `next_action`
- `TiB2`, `ZrB2`, and `WB2` are routed to negative-control / failed-memory handling
- `NbB2` and `MoB2` are routed to conditional-candidate handling with unmet gates
- known references are excluded from the new-discovery leaderboard by schema
- candidate funnel fields are now live: `candidate_layer`, `candidate_quantity_score`, `candidate_quality_score`, `entry_block_reason`, `upgrade_requirements`, `family_ruleset_id`

## Next Update Contract

Each update should report:

- total count
- newly added records
- records promoted / demoted
- missing-source blockers
- family coverage gaps
"""
    (REPORTS / "credible_corpus_status.md").write_text(text, encoding="utf-8")


def update_strategy() -> None:
    path = REPORTS / "strategy_updates.md"
    text = path.read_text(encoding="utf-8")
    marker = "## Diboride Branch Correction — 2026-06-26"
    if marker in text:
        return
    addition = """

## Diboride Branch Correction — 2026-06-26

- learned rule: `AlB2-type` alone is insufficient for positive promotion in the MgB2-neighbor lane
- do not promote diboride candidates solely because they are AlB2-type
- require boron-derived DOS near `E_F`, a credible doping path, or a phase-resolved mechanism-preserving rationale before positive promotion
- `TiB2`, `ZrB2`, and `WB2` now serve as negative-control / failed-memory anchors rather than active positive candidates
- `NbB2` and `MoB2` remain conditional candidates only, with unmet structure / phase gates
"""
    path.write_text(text.rstrip() + addition + "\n", encoding="utf-8")


def write_funnel_assets(records: list[dict]) -> None:
    broad = [r for r in records if r["candidate_layer"] == "broad"]
    structured = [r for r in records if r["candidate_layer"] == "structured"]
    promotion_ready = [r for r in records if r["candidate_layer"] == "promotion_ready"]

    write_funnel_board(
        "broad_candidate_pool.md",
        "Broad Candidate Pool",
        broad,
        "Broad pool preserves quantity. Candidates stay here if they still need a verified structure proxy, explicit condition encoding, or family-specific cleanup.",
    )
    write_funnel_board(
        "structured_candidate_pool.md",
        "Structured Candidate Pool",
        structured,
        "Structured pool preserves scientific usability. Records here already carry explicit family/condition semantics and can be upgraded without collapsing material identity.",
    )
    write_funnel_board(
        "promotion_ready_pool.md",
        "Promotion-Ready Pool",
        promotion_ready,
        "Promotion-ready pool is the only layer that should regularly consume heavy compute or stronger public-forward pressure.",
    )

    family_rulesets = {
        "ruleset_diboride_mechanism_preserving_v1": {
            "branch": "AlB2_MgB2_boride",
            "goal": "Preserve MgB2-neighbor mechanism continuity rather than structure-only similarity",
            "must_have": ["boron_sigma_continuity_or_credible_doping_path", "explicit_prototype"],
            "avoid": ["stoichiometric_transition_metal_diboride_promoted_only_by_AlB2_symmetry"],
        },
        "ruleset_mxene_layered_carbide_v1": {
            "branch": "MXene_2D",
            "goal": "Preserve layered carbide context and explicit termination/structure scope",
            "must_have": ["verified_structure_proxy", "termination_or_bare_scope"],
            "avoid": ["formula_only_mxene_without_structure_proxy"],
        },
        "ruleset_layered_nitride_intercalation_v1": {
            "branch": "layered_nitride_halonitride",
            "goal": "Keep host/intercalant/doping conditions explicit",
            "must_have": ["intercalation_or_doping_condition", "layered_host_identity"],
            "avoid": ["flatten_parent_to_undoped_host"],
        },
        "ruleset_iron_based_mechanism_preserving_v1": {
            "branch": "iron_based_extrapolation",
            "goal": "Preserve Fe-layer identity, doping path, and magnetic competition",
            "must_have": ["fe_layer_identity", "doping_route_or_condition"],
            "avoid": ["generic_metallicity_claim_as_superconductivity_proxy"],
        },
        "ruleset_cuprate_condition_preserving_v1": {
            "branch": "cuprate_extrapolation",
            "goal": "Preserve CuO2-plane and oxygen/doping semantics",
            "must_have": ["cuo2_plane_identity", "charge_reservoir_or_oxygen_context"],
            "avoid": ["flatten_parent_and_doped_cuprate"],
        },
        "ruleset_fulleride_condition_preserving_v1": {
            "branch": "fulleride_molecular",
            "goal": "Keep molecular fulleride stoichiometry and dopant context explicit",
            "must_have": ["dopant_stoichiometry", "molecular_phase_context"],
            "avoid": ["collapse_doped_fulleride_into_parent_c60"],
        },
        "ruleset_intercalation_layered_v1": {
            "branch": "graphite_intercalation",
            "goal": "Keep intercalation chemistry and host structure explicit",
            "must_have": ["host_identity", "intercalant_identity"],
            "avoid": ["generic_carbon_mixture_without_intercalation_context"],
        },
    }
    (KNOWLEDGE / "family_rulesets.json").write_text(
        json.dumps(family_rulesets, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    prototype_library = {
        "MXene_2D": ["Mo2C_bare_layer", "Ti2C_bare_layer", "Ti3C2_bare_layer", "V2C_bare_layer"],
        "AlB2_MgB2_boride": ["MgB2_alb2", "LiBC_alb2_like", "CaB2_alb2_like", "MgBC_borocarbide"],
        "layered_nitride_halonitride": ["Li_xZrNCl_layered_host", "Li_xHfNCl_layered_host"],
        "iron_based_extrapolation": ["FeSe_layered", "LiFeAs_111", "LaO1-xFxFeAs_1111", "Ba1-xKxFe2As2_122"],
        "graphite_intercalation": ["CaC6_rhombohedral", "KC8_layered_gic"],
        "fulleride_molecular": ["K3C60_fulleride", "Cs_xRb_yC60_fulleride"],
    }
    (KNOWLEDGE / "prototype_library.json").write_text(
        json.dumps(prototype_library, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    implementation_plan = """# Candidate Funnel Optimization Plan

Updated: 2026-06-27

## Objective

Increase both the quantity and quality of candidate materials by replacing a single queue with a three-layer funnel:

- broad candidate pool
- structured candidate pool
- promotion-ready pool

## Immediate Structural Changes

1. Add funnel fields to the corpus registry:
   - `candidate_layer`
   - `candidate_quantity_score`
   - `candidate_quality_score`
   - `entry_block_reason`
   - `upgrade_requirements`
   - `family_ruleset_id`
2. Generate explicit pool reports:
   - `broad_candidate_pool.md`
   - `structured_candidate_pool.md`
   - `promotion_ready_pool.md`
3. Persist reusable generator assets:
   - `knowledge/family_rulesets.json`
   - `knowledge/prototype_library.json`

## Routing Policy

- Broad pool preserves volume.
- Structured pool preserves scientific usability.
- Promotion-ready pool is the only layer that should regularly consume heavy compute.

## Success Metrics

- broad pool size grows without collapsing identity/condition information
- structured pool share rises over time
- promotion-ready pool grows slowly but steadily
- `no_structure_proxy` fraction falls over time
- negative-control reopen rate stays near zero
"""
    (REPORTS / "candidate_funnel_plan.md").write_text(implementation_plan, encoding="utf-8")


def write_leaderboards(records: list[dict]) -> None:
    positive = [
        r for r in records
        if not r.get("exclude_from_new_discovery_leaderboard")
        and r["record_role"] in {"exploratory_candidate", "conditional_candidate"}
    ]
    positive.sort(
        key=lambda r: (
            -(r.get("discovery_score_public") or -1.0),
            r["formula"],
        )
    )

    discovery_lines = [
        "# Discovery Leaderboard",
        "",
        f"Generated: {GENERATED_DATE}",
        "",
        "This board now ranks only records that are eligible for forward exploratory promotion.",
        "Known references, benchmark controls, and negative controls are excluded by schema.",
        "",
        "| Rank | Formula | Role | Discovery Score | Claim Level | Promotion Gate | Next Action |",
        "|---|---|---|---|---|---|---|",
    ]
    if positive:
        for idx, row in enumerate(positive, start=1):
            discovery_lines.append(
                f"| {idx} | {row['formula']} | {row['record_role']} | {fmt_score(row.get('discovery_score_public'))} | "
                f"{row['claim_level']} | {row['promotion_gate']} | {row['next_action']} |"
            )
    else:
        discovery_lines.append("| - | No active positive records | - | - | - | - | - |")
    discovery_lines += [
        "",
        "## Excluded By Design",
        "",
        "- known references and mechanism anchors do not enter the new-discovery leaderboard",
        "- benchmark controls do not enter the new-discovery leaderboard",
        "- negative controls and failed-memory records do not enter the new-discovery leaderboard",
        "",
    ]
    (REPORTS / "discovery_leaderboard.md").write_text("\n".join(discovery_lines), encoding="utf-8")

    evidence_rank = {
        "reference_only": 0,
        "benchmark_only": 1,
        "dft_screened_not_tc_claim": 2,
        "conditional_candidate": 3,
        "negative_control": 4,
    }
    evidence_rows = sorted(
        records,
        key=lambda r: (
            evidence_rank.get(r["claim_level"], 99),
            -(r.get("discovery_score_public") or -1.0),
            r["formula"],
        ),
    )
    evidence_lines = [
        "# Evidence Leaderboard",
        "",
        f"Generated: {GENERATED_DATE}",
        "",
        "Records are grouped by public claim discipline first, then by available score.",
        "",
        "| Formula | Role | Claim Level | Superconductivity Status | Discovery Score | Next Action |",
        "|---|---|---|---|---|---|",
    ]
    for row in evidence_rows:
        evidence_lines.append(
            f"| {row['formula']} | {row['record_role']} | {row['claim_level']} | "
            f"{row['superconductivity_status']} | {fmt_score(row.get('discovery_score_public'))} | {row['next_action']} |"
        )
    evidence_lines += [
        "",
        "## Language Rules",
        "",
        "- `reference_only` / `benchmark_only`: not a new-discovery claim",
        "- `dft_screened_not_tc_claim`: computed evidence exists, but no Tc claim is allowed",
        "- `conditional_candidate`: scientifically interesting but blocked by unmet gates",
        "- `negative_control`: evidence-bearing record that should teach avoid rules, not trigger promotion",
        "",
    ]
    (REPORTS / "evidence_leaderboard.md").write_text("\n".join(evidence_lines), encoding="utf-8")

    experiment_rows = [
        r for r in records
        if r["record_role"] in {"exploratory_candidate", "conditional_candidate"}
    ]
    experiment_rows.sort(
        key=lambda r: (
            -(r.get("discovery_score_public") or -1.0),
            r["formula"],
        )
    )
    experiment_lines = [
        "# Experiment Leaderboard",
        "",
        f"Generated: {GENERATED_DATE}",
        "",
        "Only records that could still justify experimental or compute follow-up appear here.",
        "",
        "| Formula | Role | Discovery Score | Promotion Gate | Mechanism Risk | Next Action |",
        "|---|---|---|---|---|---|",
    ]
    if experiment_rows:
        for row in experiment_rows:
            experiment_lines.append(
                f"| {row['formula']} | {row['record_role']} | {fmt_score(row.get('discovery_score_public'))} | "
                f"{row['promotion_gate']} | {', '.join(row.get('mechanism_risk', [])) or '-'} | {row['next_action']} |"
            )
    else:
        experiment_lines.append("| - | No experiment-eligible records | - | - | - | - |")
    experiment_lines += [
        "",
        "## Mandatory Exclusions",
        "",
        "- known references do not enter the experiment leaderboard as new experimental targets",
        "- benchmark controls do not enter the experiment leaderboard as new targets",
        "- negative controls do not enter the experiment leaderboard",
        "",
    ]
    (REPORTS / "experiment_leaderboard.md").write_text("\n".join(experiment_lines), encoding="utf-8")


def main() -> int:
    records = [classify(row) for row in load_records()]
    write_registry(records)

    references = [r for r in records if r["record_role"] == "reference_anchor"]
    benchmarks = [r for r in records if r["record_role"] == "benchmark_control"]
    active = [r for r in records if r["record_role"] == "exploratory_candidate"]
    conditional = [r for r in records if r["record_role"] == "conditional_candidate"]
    negative = [r for r in records if r["record_role"] == "negative_control"]
    failed = [r for r in records if r["record_role"] == "negative_control"]
    mechanism = [r for r in records if r["record_role"] == "mechanism_anchor"]

    write_board("reference_anchor_board.md", "Reference Anchor Board", references + mechanism,
                "Known references and mechanism anchors used for family learning rather than novelty claims.")
    write_board("benchmark_control_board.md", "Benchmark Control Board", benchmarks,
                "Benchmark controls calibrate known superconducting families and should not be treated as new discoveries.")
    write_board("active_candidate_board.md", "Active Candidate Board", active,
                "Positive exploratory candidates only. Empty is acceptable when the current loop has no clean active lane.")
    write_board("conditional_candidate_board.md", "Conditional Candidate Board", conditional,
                "These records remain scientifically interesting but cannot be promoted until their unmet gates are satisfied.")
    write_board("negative_control_board.md", "Negative Control Board", negative,
                "These records are scientifically useful because they teach the generator what to avoid in the current phase/proxy regime.")
    write_failed_memory(failed)
    write_blockers(records)
    update_status(records)
    update_strategy()
    write_leaderboards(records)
    write_funnel_assets(records)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
