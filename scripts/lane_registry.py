#!/usr/bin/env python3
"""Shared 12-lane registry for SC SuperLoop."""

from __future__ import annotations

from typing import Any

LANE_ORDER = [
    "cuprate",
    "iron_based",
    "nickelate",
    "hydride",
    "conventional",
    "elemental",
    "chalcogenide",
    "mgb2_diboride",
    "heavy_fermion",
    "kagome",
    "borocarbide",
    "frontier_first_principles",
]

LANE_REGISTRY: dict[str, dict[str, Any]] = {
    "cuprate": {
        "family_ruleset_id": "ruleset_cuprate_condition_preserving_v2",
        "validation_recipe_id": "validate_cuprate_condition_window_v1",
        "condition_class": "doped",
        "mechanism_family": "charge_transfer_layered",
        "generation_mode": "extrapolation",
        "family_confidence": 0.9,
        "lane_priority_bias": 8.0,
    },
    "iron_based": {
        "family_ruleset_id": "ruleset_iron_based_mechanism_preserving_v2",
        "validation_recipe_id": "validate_iron_based_layer_magnetism_v1",
        "condition_class": "doped",
        "mechanism_family": "multiband_spin_fluctuation",
        "generation_mode": "extrapolation",
        "family_confidence": 0.88,
        "lane_priority_bias": 6.0,
    },
    "nickelate": {
        "family_ruleset_id": "ruleset_nickelate_charge_transfer_v1",
        "validation_recipe_id": "validate_nickelate_square_planar_v1",
        "condition_class": "doped",
        "mechanism_family": "charge_transfer_square_planar",
        "generation_mode": "extrapolation",
        "family_confidence": 0.86,
        "lane_priority_bias": 9.0,
    },
    "hydride": {
        "family_ruleset_id": "ruleset_hydride_pressure_estimated_v2",
        "validation_recipe_id": "validate_hydride_pressure_window_v1",
        "condition_class": "high_pressure",
        "mechanism_family": "hydrogen_rich_epc",
        "generation_mode": "extrapolation",
        "family_confidence": 0.84,
        "lane_priority_bias": 7.0,
    },
    "conventional": {
        "family_ruleset_id": "ruleset_conventional_epc_v1",
        "validation_recipe_id": "validate_conventional_metallicity_v1",
        "condition_class": "ambient",
        "mechanism_family": "epc_metallic",
        "generation_mode": "interpolation",
        "family_confidence": 0.8,
        "lane_priority_bias": 3.0,
    },
    "elemental": {
        "family_ruleset_id": "ruleset_elemental_phase_condition_v1",
        "validation_recipe_id": "validate_elemental_phase_scope_v1",
        "condition_class": "ambient",
        "mechanism_family": "elemental_phase_dependent",
        "generation_mode": "extrapolation",
        "family_confidence": 0.78,
        "lane_priority_bias": 2.0,
    },
    "chalcogenide": {
        "family_ruleset_id": "ruleset_chalcogenide_layered_pressure_v1",
        "validation_recipe_id": "validate_chalcogenide_soc_condition_v1",
        "condition_class": "mixed",
        "mechanism_family": "layered_chalcogenide",
        "generation_mode": "analogy",
        "family_confidence": 0.79,
        "lane_priority_bias": 4.0,
    },
    "mgb2_diboride": {
        "family_ruleset_id": "ruleset_diboride_mechanism_preserving_v2",
        "validation_recipe_id": "validate_diboride_sigma_band_v1",
        "condition_class": "ambient",
        "mechanism_family": "sigma_band_epc",
        "generation_mode": "interpolation",
        "family_confidence": 0.85,
        "lane_priority_bias": 5.0,
    },
    "heavy_fermion": {
        "family_ruleset_id": "ruleset_heavy_fermion_qcp_v1",
        "validation_recipe_id": "validate_heavy_fermion_low_temp_v1",
        "condition_class": "mixed",
        "mechanism_family": "kondo_qcp",
        "generation_mode": "analogy",
        "family_confidence": 0.75,
        "lane_priority_bias": 3.5,
    },
    "kagome": {
        "family_ruleset_id": "ruleset_kagome_cdw_v1",
        "validation_recipe_id": "validate_kagome_motif_cdw_v1",
        "condition_class": "ambient",
        "mechanism_family": "kagome_multiband",
        "generation_mode": "analogy",
        "family_confidence": 0.82,
        "lane_priority_bias": 5.5,
    },
    "borocarbide": {
        "family_ruleset_id": "ruleset_borocarbide_framework_v1",
        "validation_recipe_id": "validate_borocarbide_framework_v1",
        "condition_class": "ambient",
        "mechanism_family": "boron_carbide_intermetallic",
        "generation_mode": "analogy",
        "family_confidence": 0.77,
        "lane_priority_bias": 4.5,
    },
    "frontier_first_principles": {
        "family_ruleset_id": "ruleset_frontier_first_principles_v1",
        "validation_recipe_id": "validate_frontier_sanity_v1",
        "condition_class": "unknown",
        "mechanism_family": "frontier_unknown",
        "generation_mode": "frontier",
        "family_confidence": 0.6,
        "lane_priority_bias": 6.5,
    },
}

FORMULA_LANE_OVERRIDES = {
    "NdNiO2": "nickelate",
    "LaNiO2": "nickelate",
    "PrNiO2": "nickelate",
    "Nd0.8Sr0.2NiO2": "nickelate",
    "La0.8Sr0.2NiO2": "nickelate",
    "Pr0.8Sr0.2NiO2": "nickelate",
    "Ba2NiO2F2": "nickelate",
    "La2PdO4": "nickelate",
    "LaPdO2": "nickelate",
    "La2CoO4": "nickelate",
    "BaNi2As2": "nickelate",
    "BaCo2As2": "iron_based",
    "Bi2Se3": "chalcogenide",
    "Cu0.3Bi2Se3": "chalcogenide",
    "Sr0.1Bi2Se3": "chalcogenide",
    "Bi2Te3": "chalcogenide",
    "Bi2S3": "chalcogenide",
    "Bi2Se2S": "chalcogenide",
    "PbTe": "chalcogenide",
    "PbSe": "chalcogenide",
    "WTe2": "chalcogenide",
    "MoTe2": "chalcogenide",
    "TiN": "conventional",
    "TiC": "conventional",
    "WO3": "conventional",
    "SrTiO3": "conventional",
    "CaTiO3": "conventional",
    "BaTiO3": "conventional",
    "KTaO3": "conventional",
    "ZrNCl": "conventional",
    "HfNCl": "conventional",
    "TiNCl": "conventional",
    "NbNCl": "conventional",
    "TaNBr": "conventional",
    "Li0.5ZrNCl": "conventional",
    "Na0.5ZrNCl": "conventional",
    "ZrNF": "conventional",
    "HfNBr": "conventional",
    "ScNCl": "conventional",
    "Ba8Si46": "conventional",
    "Ba8Ge46": "conventional",
    "K8Si46": "conventional",
    "Cs8Si46": "conventional",
    "Ba8Al16Si30": "conventional",
    "Ba8Ga16Ge30": "conventional",
    "Sr8Si46": "conventional",
    "Ca8Si46": "conventional",
    "Ba8Si40B6": "conventional",
    "Nb": "elemental",
    "Pb": "elemental",
}

BRANCH_LANE_DEFAULTS = {
    "cuprate": "cuprate",
    "cuprate_extrapolation": "cuprate",
    "nickelate": "nickelate",
    "iron_based_extrapolation": "iron_based",
    "iron_based": "iron_based",
    "p_block_hydride": "hydride",
    "hydride": "hydride",
    "mgb2_diboride": "mgb2_diboride",
    "AlB2_MgB2_boride": "mgb2_diboride",
    "kagome": "kagome",
    "kagome_vanHove": "kagome",
    "borocarbide": "borocarbide",
    "BC_framework": "borocarbide",
    "BCH_BCNH_framework": "frontier_first_principles",
    "frontier_first_principles": "frontier_first_principles",
    "high_entropy": "frontier_first_principles",
    "conventional": "conventional",
    "MXene_2D": "conventional",
    "AlO_STO_oxide": "conventional",
    "AlTiPbW_exploratory": "frontier_first_principles",
    "doped_clathrate": "conventional",
    "layered_nitride_halonitride": "conventional",
    "topological_doped": "chalcogenide",
    "elemental": "elemental",
    "elemental_conventional": "elemental",
    "a15_intermetallic": "conventional",
    "bismuthate_perovskite": "conventional",
    "fulleride_molecular": "conventional",
    "graphite_intercalation": "conventional",
    "intermetallic_low_tc": "conventional",
    "layered_perovskite_unconventional": "chalcogenide",
    "heavy_fermion_unconventional": "heavy_fermion",
    "chalcogenide": "chalcogenide",
    "AlB2-type hexagonal boride benchmark": "mgb2_diboride",
}


def resolve_lane_id(branch: str, formula: str, risk_tags: list[str] | None = None) -> str:
    if branch in LANE_REGISTRY:
        return branch
    if formula in FORMULA_LANE_OVERRIDES:
        return FORMULA_LANE_OVERRIDES[formula]

    lane_id = BRANCH_LANE_DEFAULTS.get(branch, "frontier_first_principles")
    risk_tags = risk_tags or []

    if lane_id == "frontier_first_principles":
        if "high_pressure_risk" in risk_tags and "H" in formula:
            return "hydride"
        if any(tag in risk_tags for tag in ("SOC_check_later",)) and any(x in formula for x in ("Se", "Te", "Sb", "Bi")):
            return "chalcogenide"
    return lane_id


def lane_metadata_for(branch: str, formula: str, risk_tags: list[str] | None = None) -> dict[str, Any]:
    lane_id = resolve_lane_id(branch, formula, risk_tags)
    metadata = dict(LANE_REGISTRY[lane_id])
    metadata["lane_id"] = lane_id
    return metadata


def infer_condition_class(branch: str, formula: str, risk_tags: list[str] | None = None) -> str:
    risk_tags = risk_tags or []
    if branch == "p_block_hydride":
        return "high_pressure"
    if "interface_required" in risk_tags:
        return "interfacial"
    if "carrier_density_sensitive" in risk_tags:
        return "doped"
    if "high_pressure_risk" in risk_tags:
        return "high_pressure"
    if "surface_termination_sensitive" in risk_tags:
        return "mixed"
    if formula in {"Nb", "Pb"}:
        return "ambient"
    return lane_metadata_for(branch, formula, risk_tags)["condition_class"]


def infer_required_condition_vector(branch: str, formula: str, risk_tags: list[str] | None = None) -> list[str]:
    risk_tags = risk_tags or []
    required: list[str] = []
    if branch == "p_block_hydride" or "high_pressure_risk" in risk_tags:
        required.append("pressure")
    if "carrier_density_sensitive" in risk_tags:
        required.append("doping")
    if "oxygen_vacancy_sensitive" in risk_tags:
        required.append("oxygen_stoichiometry")
    if "interface_required" in risk_tags:
        required.append("interface")
    if "surface_termination_sensitive" in risk_tags:
        required.append("surface_termination")
    if "configurational_disorder" in risk_tags or "configurational_disorder_high" in risk_tags:
        required.append("configuration_control")
    if "metastability_risk" in risk_tags:
        required.append("metastability_window")
    if formula in {"Nb", "Pb"}:
        required.append("phase_scope")
    return required
