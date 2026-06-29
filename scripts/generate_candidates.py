#!/usr/bin/env python3
"""
LOOP-SC Candidate Generator v0.2
Generates candidates across legacy branches while projecting them into the
new 12-lane SC SuperLoop architecture.
"""
import argparse
import json, random, itertools
from collections import Counter
from datetime import datetime
from pathlib import Path

from lane_registry import (
    infer_condition_class,
    infer_required_condition_vector,
    lane_metadata_for,
)

SC_ROOT = Path(__file__).parent.parent
CANDIDATES_DIR = SC_ROOT / "candidates"
CORPUS_REGISTRY = SC_ROOT / "knowledge" / "credible_superconductors.jsonl"

# Branch weights (from spec)
BRANCH_WEIGHTS = {
    "AlB2_MgB2_boride":        0.14,
    "BC_framework":            0.10,
    "cuprate_extrapolation":   0.12,
    "iron_based_extrapolation":0.12,
    "AlO_STO_oxide":           0.10,
    "AlTiPbW_exploratory":     0.06,
    "BCH_BCNH_framework":      0.10,
    "p_block_hydride":         0.07,
    "doped_clathrate":         0.06,
    "layered_nitride_halonitride": 0.05,
    "kagome_vanHove":          0.04,
    "MXene_2D":                0.02,
    "high_entropy":            0.01,
    "topological_doped":       0.01,
}

# Branch templates: (formula_template, parent, mechanism_hyp, risk_tags)
BRANCH_TEMPLATES = {
    "AlB2_MgB2_boride": [
        # A-site substitutions in AlB2/MgB2 prototype
        ("MgB2",   "MgB2 AlB2-type", "sigma-band two-gap EPC, E2g phonon", ["two_gap_risk"]),
        ("AlB2",   "AlB2 prototype",  "sigma-band unfilled, check electron count", ["low_Tc_risk"]),
        ("Mg0.75Al0.25B2", "MgB2/AlB2 alloy", "partial Al substitution as sigma-hole filling control knob", ["carrier_density_sensitive","configurational_disorder"]),
        ("Mg0.5Al0.5B2", "MgB2/AlB2 alloy","alloy electron count tuning", ["configurational_disorder"]),
        ("Mg0.25Al0.75B2", "MgB2/AlB2 alloy", "late-stage sigma-band overfilling checkpoint against MgB2 mechanism", ["carrier_density_sensitive","configurational_disorder","low_Tc_risk"]),
        ("Li0.5Al0.5B2", "Li/Al mixed A-site diboride", "Al-Li-B sigma-band tuning route with lighter A-site chemistry", ["carrier_density_sensitive","configurational_disorder","metastability_risk"]),
        ("LiAlB4", "Li-Al-B ternary boride", "Al-Li-B ternary route probing sigma-band continuity beyond binary diborides", ["carrier_density_sensitive","metastability_risk"]),
        ("BeB2",   "MgB2 A-site sub","Be lighter, higher phonon freq, less stable", ["metastability_risk"]),
        ("CaB2",   "MgB2 A-site sub","Ca larger, sigma-band filling may drop", ["structure_distortion_risk"]),
        ("ScB2",   "AlB2-type",       "d-metal A-site, extra electron, possible sigma enhancement", []),
        ("TiB2",   "AlB2-type",       "d-metal A-site, Ti-d + B-p hybridization", []),
        ("VB2",    "AlB2-type",       "d-metal, half-filled d-band, check magnetism", ["magnetic_risk"]),
        ("NbB2",   "AlB2-type",       "Nb d-metal analog, large lambda expected", []),
        ("MoB2",   "AlB2-type",       "Mo d-metal, multiple phases known", []),
        ("WB2",    "AlB2-type",       "W heavy d-metal, SOC relevant", ["SOC_check_later"]),
        ("ZrB2",   "AlB2-type",       "Zr d-metal, hardest diboride, low EPC expected", ["low_Tc_risk"]),
        ("HfB2",   "AlB2-type",       "Hf analog to Zr, SOC", ["SOC_check_later"]),
        ("CrB2",   "AlB2-type",       "Cr magnetic risk high", ["magnetic_risk"]),
        ("FeB2",   "AlB2-type",       "Fe magnetic, check stability", ["magnetic_risk","metastability_risk"]),
        ("Li2B3",  "boride framework","Li-doped boride", ["metastability_risk"]),
        ("Ca0.5Mg0.5B2", "mixed A-site","chemical pressure tuning", ["configurational_disorder"]),
        ("LiBC",   "LiBC prototype",  "isoelectronic MgB2 analog, hole-doped insulator->SC", ["carrier_density_sensitive"]),
        ("BeBC",   "LiBC analog",     "lighter, higher freq estimate", ["metastability_risk"]),
        ("MgBC",   "LiBC analog",     "Mg+B+C framework", []),
    ],
    "BC_framework": [
        ("BC3",    "BC3 layered",     "graphite-like, B-C covalent, intercalation SC possible", ["carrier_density_sensitive"]),
        ("B2C",    "boron carbide",   "B-rich, conductive, check EPC", []),
        ("BC",     "rocksalt BC",     "metastable, high freq phonons", ["metastability_risk"]),
        ("B4C",    "B4C structure",   "hard, insulating unless doped", ["carrier_density_sensitive"]),
        ("LiB",    "NaCl-type LiB",   "light elements, check phonon instability", ["metastability_risk"]),
        ("NaBC2",  "B-C + alkali",    "alkali metallizes B-C", []),
        ("KB3C4",  "K-intercalated BC","K donor, B-C metallic", []),
        ("CaB2C2", "B-C-Ca quaternary","charge balance with Ca", []),
        ("MgB2C2", "B-C-Mg quaternary","Mg donor to B-C", []),
        ("Li2BC2", "Li-B-C",          "Li-rich, metallic B-C", []),
    ],
    "cuprate_extrapolation": [
        ("La2CuO4",    "214 cuprate",   "parent compound, AF insulator, doped->SC, d9 CuO2 plane", ["strong_correlation_risk"]),
        ("YBa2Cu3O7",  "123 cuprate",   "optimal doped, Tc~92K reference", ["strong_correlation_risk"]),
        ("Bi2Sr2CaCu2O8","2212 BSCCO",  "layered, easy cleavage, Tc~85K", ["strong_correlation_risk"]),
        ("La1.85Sr0.15CuO4","doped 214","Sr doping ~optimal, Tc~38K", ["strong_correlation_risk","carrier_density_sensitive"]),
        ("NdNiO2",     "infinite-layer nickelate", "d9-adjacent Ni infinite-layer parent, direct cuprate-like single-band comparator", ["strong_correlation_risk","carrier_density_sensitive","conjecture_only"]),
        ("LaNiO2",     "infinite-layer nickelate", "La infinite-layer nickelate parent, charge-transfer route with reduced apical oxygen", ["strong_correlation_risk","carrier_density_sensitive","conjecture_only"]),
        ("PrNiO2",     "infinite-layer nickelate", "rare-earth-tuned infinite-layer nickelate parent probing cuprate-like 2D d9 physics", ["strong_correlation_risk","carrier_density_sensitive","conjecture_only"]),
        ("Nd0.8Sr0.2NiO2", "Sr-doped infinite-layer nickelate", "hole-doped infinite-layer nickelate with explicit charge-reservoir tuning", ["strong_correlation_risk","carrier_density_sensitive"]),
        ("La0.8Sr0.2NiO2", "Sr-doped infinite-layer nickelate", "La nickelate variant preserving explicit hole-doping semantics", ["strong_correlation_risk","carrier_density_sensitive","conjecture_only"]),
        ("Pr0.8Sr0.2NiO2", "Sr-doped infinite-layer nickelate", "Pr nickelate variant for rare-earth control of the cuprate-like window", ["strong_correlation_risk","carrier_density_sensitive","conjecture_only"]),
        ("La2NiO4",    "214 Ni analog", "Ni d8 vs d9, orbital check", ["strong_correlation_risk"]),
        ("La2CoO4",    "214 Co analog", "Co d7, check spin state", ["strong_correlation_risk","magnetic_risk"]),
        ("AgF2",       "fluoride cuprate analog", "Ag2+ square-ligand route to cuprate-like single-orbital physics without copper", ["strong_correlation_risk","conjecture_only","ligand_field_sensitive"]),
        ("Cs2AgF4",    "layered silver fluoride", "K2NiF4-like Ag-F layered analog with explicit square-ligand context", ["strong_correlation_risk","magnetic_risk","conjecture_only","ligand_field_sensitive"]),
        ("Ba2NiO2F2",  "oxychalcogen-free layered nickelate", "square-planar nickel oxyfluoride route to stronger ligand-field control", ["strong_correlation_risk","carrier_density_sensitive","conjecture_only","ligand_field_sensitive"]),
        ("La2PdO4",    "214 Pd analog", "4d analog stress-test for wider-band single-orbital charge-transfer chemistry", ["strong_correlation_risk","conjecture_only","wider_band_risk"]),
        ("LaPdO2",     "infinite-layer palladate", "4d infinite-layer analog testing whether Pd can preserve 2D charge-transfer structure", ["strong_correlation_risk","carrier_density_sensitive","conjecture_only","wider_band_risk"]),
        ("Y0.9Ca0.1Ba2Cu3O7","Ca-doped 123","overdoped direction", ["strong_correlation_risk"]),
        ("HgBa2Ca2Cu3O8","Hg-1223",     "highest Tc cuprate ~133K", ["strong_correlation_risk","toxicity_risk"]),
        ("Tl2Ba2Ca2Cu3O10","Tl-2223",   "Tl-based multilayer", ["strong_correlation_risk","toxicity_risk"]),
        ("CaCuO2",     "infinite layer","no apical O, parent structure", ["strong_correlation_risk"]),
        ("SrCuO2",     "infinite layer Sr","Sr version", ["strong_correlation_risk"]),
        ("La2-xBaxCuO4","Ba-doped 214","Ba analog to Sr", ["strong_correlation_risk"]),
        ("Nd2CuO4",    "T'-type 214",   "electron-doped parent", ["strong_correlation_risk"]),
    ],
    "iron_based_extrapolation": [
        ("LaFeAsO",    "1111 pnictide",  "parent compound, AF, doped->SC", ["magnetic_risk","strong_correlation_risk"]),
        ("BaFe2As2",   "122 pnictide",   "parent compound, nematic, doped->SC", ["magnetic_risk"]),
        ("FeSe",       "11 chalcogenide","simplest iron SC, Tc~9K", ["nematicity_risk"]),
        ("LiFeAs",     "111 pnictide",   "self-doped SC, Tc~18K", []),
        ("BaCo2As2",   "122 cobalt analog", "3d analog that helps bracket the single-orbital charge-transfer window against overfilled d-shells", ["magnetic_risk","wider_band_risk"]),
        ("BaNi2As2",   "122 nickel analog", "Ni analog stress-test for itinerant 122 physics versus cuprate-like aspirations", ["wider_band_risk"]),
        ("LaFeAsO0.9F0.1","F-doped 1111","optimal F-doping", ["carrier_density_sensitive"]),
        ("Ba0.6K0.4Fe2As2","K-doped 122","optimal K-doping, Tc~38K", ["carrier_density_sensitive"]),
        ("BaFe2P2",    "122 P-analog",   "FeP vs FeAs, lower Tc, no magnetism", []),
        ("BaFe2S2",    "122 S-analog",   "FeSe/FeS competition", []),
        ("LaFePO",     "1111 P-analog",  "FeP layer, lower Tc", []),
        ("LaFeAsO_F0.05","low F-doped",  "underdoped side", ["carrier_density_sensitive"]),
        ("CaFe2As2",   "122 Ca-A-site",  "collapsed tetragonal", []),
        ("SrFe2As2",   "122 Sr-A-site",  "larger A-site", []),
        ("KFe2Se2",    "K-122 intercalated","Fe vacancy ordered phase", ["magnetic_risk"]),
        ("FeTe0.5Se0.5","11 alloy",       "mixed chalcogenide, enhanced Tc", ["configurational_disorder"]),
    ],
    "AlO_STO_oxide": [
        ("SrTiO3",     "STO parent",    "soft phonon, ferroelectric proximity, Tc~0.4K at O-vac", ["carrier_density_sensitive","oxygen_vacancy_sensitive"]),
        ("BaTiO3",     "BTO analog",    "ferroelectric, proximity to STO", ["carrier_density_sensitive"]),
        ("CaTiO3",     "CTO perovskite","smaller A-site vs STO", []),
        ("KTaO3",      "KTO perovskite","Ta analog to Ti, higher SOC, Tc~0.9K surface", ["SOC_check_later","interface_required"]),
        ("SrZrO3",     "STO Zr-analog", "Zr replaces Ti", []),
        ("SrHfO3",     "STO Hf-analog", "Hf d0, large SOC", ["SOC_check_later"]),
        ("BaZrO3",     "BZO perovskite","proton conductor, check SC", []),
        ("SrTi0.9Nb0.1O3","Nb-doped STO","Nb as donor impurity", ["carrier_density_sensitive"]),
        ("SrTi0.9V0.1O3","V-doped STO", "V 3d, magnetic risk", ["magnetic_risk"]),
        ("WO3",        "WO3 bulk",      "doped WO3 SC at Tc~3K", ["carrier_density_sensitive","oxygen_vacancy_sensitive"]),
        ("Na0.05WO3",  "Na-doped WO3",  "Na donor, bronze phase", ["carrier_density_sensitive"]),
        ("Al2O3",      "corundum Al2O3","wide gap, interface SC only", ["interface_required"]),
        ("LaAlO3",     "LAO perovskite","LAO/STO interface SC", ["interface_required"]),
        ("LaAlO3/SrTiO3", "polar oxide interface", "canonical LAO/STO 2DEG superconducting interface anchor", ["interface_required","carrier_density_sensitive"]),
        ("FeSe/LaAlO3", "FeSe monolayer on LAO", "conjectured interface phonon enhancement route via LAO substrate without abandoning FeSe layer physics", ["interface_required","conjecture_only","mechanism_ambiguous"]),
        ("FeSe/LaAlO3(001)", "FeSe monolayer on LAO(001)", "structure-scoped FeSe-on-LAO interface testbed; preserve monolayer and substrate orientation semantics", ["interface_required","conjecture_only","mechanism_ambiguous"]),
        ("TiO2",       "rutile TiO2",   "reduced TiO2-x superconductor path", ["oxygen_vacancy_sensitive"]),
    ],
    "AlTiPbW_exploratory": [
        ("AlB2",   "Al boride AlB2","Al sp-metal + B sigma-band analog", []),
        ("Al2O3",  "corundum",      "Al-O framework, interface SC relevant", ["interface_required"]),
        ("AlN",    "wurtzite AlN",  "Al nitride, wide gap, doping needed", ["carrier_density_sensitive"]),
        ("TiN",    "rocksalt TiN",  "TiN Tc~5K conventional, hard ceramic SC", []),
        ("TiO2",   "rutile TiO2",   "reduced TiO2-x", ["oxygen_vacancy_sensitive"]),
        ("TiB2",   "AlB2-type TiB2","Ti d-metal + B sigma-band", []),
        ("TiC",    "rocksalt TiC",  "TiC Tc~3K", []),
        ("PbO",    "PbO layered",   "Pb-O, interface SC candidate", ["SOC_check_later"]),
        ("Pb2O3",  "mixed Pb oxide","Pb mixed valence", ["SOC_check_later"]),
        ("PbTe",   "rocksalt PbTe", "topological, pressure-induced SC", ["SOC_check_later"]),
        ("PbSe",   "rocksalt PbSe", "analog to PbTe", ["SOC_check_later"]),
        ("WC",     "WC hexagonal",  "WC Tc~10K? check literature", []),
        ("WB",     "WB structure",  "W boride", ["SOC_check_later"]),
        ("WO3",    "WO3 oxide",     "doped W bronze", ["carrier_density_sensitive"]),
        ("W2B5",   "W boride",      "W-rich boride phase", ["SOC_check_later"]),
        ("Al3Mg2", "intermetallic", "Al-Mg alloy", []),
    ],
    "BCH_BCNH_framework": [
        ("B2H6",       "diborane-derived","check H-rich B cage stability", ["metastability_risk","high_pressure_risk"]),
        ("BC2H",       "B-C-H cage",     "mixed covalent + H phonon", ["metastability_risk"]),
        ("BN",         "h-BN/c-BN",      "wide gap, doping path to SC", ["carrier_density_sensitive"]),
        ("B2N2H2",     "B-N-H ring",     "mixed bonding", ["metastability_risk"]),
        ("C3N4",       "carbon nitride", "polymorphic, metallic phases under pressure", ["high_pressure_risk"]),
        ("BC3N3",      "B-C-N sodalite", "B/C/N cage", ["metastability_risk"]),
        ("Li2B4H4",    "Li-B-H",         "Li donor + B-H cage", []),
        ("Ca2B10H10",  "Ca-closo-borane","closoborane cage with Ca", []),
        ("MgB4H4",     "Mg-B-H",         "Mg donor + B-H", []),
        ("KB3H8",      "K-B-H",          "K donor, high-H content", ["high_pressure_risk"]),
    ],
    "p_block_hydride": [
        ("SnH4",   "group 14 hydride","Sn-H cage, predicted Tc>80K at high P", ["high_pressure_risk"]),
        ("PbH4",   "group 14 hydride","Pb-H, heavy pnictogen + H", ["high_pressure_risk","SOC_check_later"]),
        ("BiH3",   "group 15 hydride","Bi-H", ["high_pressure_risk","SOC_check_later"]),
        ("SbH3",   "group 15 hydride","Sb-H, lighter than Bi", ["high_pressure_risk"]),
        ("TeH2",   "group 16 hydride","Te-H", ["high_pressure_risk"]),
        ("SbCH6",  "Sb-C-H ternary", "ternary with C cage", ["high_pressure_risk"]),
        ("SnCH6",  "Sn-C-H ternary", "Sn-C-H cage", ["high_pressure_risk"]),
        ("Bi2H6",  "Bi-H di",        "Bi-H dimer unit", ["high_pressure_risk","SOC_check_later"]),
        ("GaH3",   "group 13 hydride","Ga-H", ["high_pressure_risk"]),
        ("InH3",   "group 13 hydride","In-H", ["high_pressure_risk"]),
    ],
    "doped_clathrate": [
        ("Ba8Si46",    "Si clathrate II", "Ba-filled Si cage, Tc~8K", []),
        ("Ba8Ge46",    "Ge clathrate",    "Ge cage analog", []),
        ("K8Si46",     "K-Si clathrate",  "K donor, check electron count", []),
        ("Cs8Si46",    "Cs-Si clathrate", "larger alkali donor", []),
        ("Ba8Al16Si30","Al-Si clathrate", "alloyed cage with Al", []),
        ("Ba8Ga16Ge30","BGG clathrate",   "thermoelectric related", []),
        ("Sr8Si46",    "Sr-Si clathrate", "Sr donor", []),
        ("Ca8Si46",    "Ca-Si clathrate", "Ca donor", []),
        ("Ba8Si40B6",  "B-sub Si clat",   "B substitution in Si cage", []),
        ("Ba8C46",     "C clathrate",     "pure C cage with Ba", ["metastability_risk"]),
    ],
    "layered_nitride_halonitride": [
        ("ZrNCl",      "ZrNCl prototype","Zr-N-Cl layered, Tc~15K intercalated", ["carrier_density_sensitive"]),
        ("HfNCl",      "HfNCl analog",   "Hf heavier analog, Tc~25K intercalated", ["carrier_density_sensitive","SOC_check_later"]),
        ("TiNCl",      "TiNCl analog",   "Ti lighter, check band structure", []),
        ("NbNCl",      "NbNCl analog",   "Nb d-metal", []),
        ("TaNBr",      "TaNBr analog",   "Ta with Br instead of Cl", ["SOC_check_later"]),
        ("Li0.5ZrNCl", "Li-ZrNCl",       "Li-intercalated, Tc onset", ["carrier_density_sensitive"]),
        ("Na0.5ZrNCl", "Na-ZrNCl",       "Na intercalated", ["carrier_density_sensitive"]),
        ("ZrNF",       "ZrNF analog",    "F replaces Cl", []),
        ("HfNBr",      "HfNBr analog",   "Br replaces Cl in HfNCl", ["SOC_check_later"]),
        ("ScNCl",      "ScNCl analog",   "Sc d0+1, lighter", []),
    ],
    "kagome_vanHove": [
        ("CsV3Sb5",    "AV3Sb5 kagome",  "kagome SC, CDW competition, Tc~2.5K", ["cdw_competition"]),
        ("KV3Sb5",     "AV3Sb5 kagome",  "K version, Tc~0.9K", ["cdw_competition"]),
        ("RbV3Sb5",    "AV3Sb5 kagome",  "Rb version", ["cdw_competition"]),
        ("CsNb3Sb5",   "ANb3Sb5 kagome", "Nb kagome analog", []),
        ("CsTa3Sb5",   "ATa3Sb5 kagome", "Ta kagome, SOC", ["SOC_check_later"]),
        ("KNb3Sb5",    "ANb3Sb5",        "K + Nb kagome", []),
        ("RbNb3Sb5",   "ANb3Sb5",        "Rb + Nb kagome", []),
        ("CsV3Bi5",    "AV3Bi5",         "Bi instead of Sb", ["SOC_check_later","cdw_competition"]),
        ("CsCr3Sb5",   "ACr3Sb5 kagome", "Cr magnetic risk", ["magnetic_risk"]),
        ("BaFe6Sn6",   "Fe kagome",      "Fe kagome layer", ["magnetic_risk"]),
    ],
    "MXene_2D": [
        ("Ti3C2",      "MXene Ti3C2",    "2D metallic MXene", ["surface_termination_sensitive"]),
        ("Nb2C",       "MXene Nb2C",     "Nb-based MXene, predicted SC", ["surface_termination_sensitive"]),
        ("Mo2C",       "MXene Mo2C",     "Mo-based MXene, measured Tc~4K", ["surface_termination_sensitive"]),
        ("V2C",        "MXene V2C",      "V-based MXene", ["surface_termination_sensitive"]),
        ("Ti2C",       "MXene Ti2C",     "Ti thin MXene", ["surface_termination_sensitive"]),
        ("Nb4C3",      "MXene Nb4C3",    "thick Nb MXene", ["surface_termination_sensitive"]),
        ("Mo2N",       "MXene Mo2N",     "nitride MXene", ["surface_termination_sensitive"]),
        ("V2N",        "MXene V2N",      "V nitride MXene", ["surface_termination_sensitive"]),
        ("Ti3CN",      "MXene mixed",    "Ti-C-N mixed", ["surface_termination_sensitive"]),
        ("Cr2C",       "MXene Cr2C",     "Cr magnetic risk", ["magnetic_risk","surface_termination_sensitive"]),
    ],
    "high_entropy": [
        ("Nb0.25V0.25Ti0.25Zr0.25B2","HE boride AlB2-type","high-entropy A-site MgB2-like", ["configurational_disorder_high"]),
        ("TiZrNbHfB2", "HE diboride",   "5-component HE diboride", ["configurational_disorder_high"]),
        ("TiZrNbNiCu", "HE nitride/alloy","multi-principal HE alloy", ["configurational_disorder_high"]),
        ("NbMoTaWB2",  "HE W-group boride","heavy HE boride", ["configurational_disorder_high","SOC_check_later"]),
        ("TiNbZrVCrN", "HE nitride",    "5-metal HE nitride", ["configurational_disorder_high"]),
    ],
    "topological_doped": [
        ("Bi2Se3",     "TI parent",     "topological insulator, Cu-doped SC", ["SOC_check_later"]),
        ("Cu0.3Bi2Se3","Cu-doped TI",   "CuxBi2Se3, Tc~3.8K", ["SOC_check_later"]),
        ("Sr0.1Bi2Se3","Sr-doped TI",   "Sr intercalation", ["SOC_check_later"]),
        ("Bi2Te3",     "TI Te analog",  "Bi2Te3 topological", ["SOC_check_later"]),
        ("WTe2",       "Weyl SM",       "type-II Weyl, pressure SC", ["SOC_check_later","high_pressure_risk"]),
        ("MoTe2",      "Weyl SM MoTe2", "type-II Weyl analog", ["SOC_check_later"]),
        ("Bi2S3",      "lighter analog","Bi2S3, less SOC", ["SOC_check_later"]),
        ("Bi2Se2S",    "mixed chalco",  "mixed Se/S", ["SOC_check_later"]),
    ],
}

HYDRIDE_PRESSURE_PRIORS_GPA = {
    "SnH4": 95,
    "PbH4": 120,
    "BiH3": 115,
    "SbH3": 105,
    "TeH2": 90,
    "SbCH6": 85,
    "SnCH6": 80,
    "Bi2H6": 125,
    "GaH3": 85,
    "InH3": 95,
    "B2H6": 110,
    "KB3H8": 70,
    "BC2H": 75,
    "B2N2H2": 80,
}

LANE_WEIGHTS = {
    "mgb2_diboride": 0.12,
    "borocarbide": 0.03,
    "cuprate": 0.12,
    "iron_based": 0.10,
    "nickelate": 0.11,
    "hydride": 0.10,
    "conventional": 0.16,
    "elemental": 0.06,
    "chalcogenide": 0.08,
    "heavy_fermion": 0.05,
    "kagome": 0.05,
    "frontier_first_principles": 0.02,
}

LANE_TEMPLATES = {
    "mgb2_diboride": [
        ("MgB2", "MgB2 AlB2-type", "sigma-band two-gap EPC, E2g phonon", ["two_gap_risk"]),
        ("AlB2", "AlB2 prototype", "sigma-band filling boundary check", ["low_Tc_risk"]),
        ("Mg0.75Al0.25B2", "MgB2/AlB2 alloy", "A-site alloy tuning around MgB2", ["carrier_density_sensitive", "configurational_disorder"]),
        ("Mg0.85Li0.15B2", "MgB2/Li alloy", "hole-side A-site tuning around MgB2", ["carrier_density_sensitive", "configurational_disorder"]),
        ("Mg0.85Zn0.15B2", "MgB2/Zn alloy", "isovalent disorder test near MgB2 phonon route", ["configurational_disorder"]),
        ("Ca0.5Mg0.5B2", "mixed A-site diboride", "chemical-pressure interpolation between MgB2 and CaB2", ["configurational_disorder", "structure_distortion_risk"]),
        ("LiAlB4", "Li-Al-B ternary boride", "light-element ternary continuation of the diboride sigma-band lane", ["carrier_density_sensitive", "metastability_risk"]),
        ("ScB2", "AlB2-type", "d-metal A-site sigma-band neighbor", []),
        ("NbB2", "AlB2-type", "Nb diboride EPC candidate", []),
        ("MoB2", "AlB2-type", "Mo diboride polymorph-sensitive EPC route", []),
        ("CaB2", "MgB2 A-site analog", "chemical pressure in diboride lane", ["structure_distortion_risk"]),
        ("LiBC", "LiBC prototype", "hole-doped MgB2-neighbor analog", ["carrier_density_sensitive"]),
        ("MgBC", "LiBC analog", "B-C sigma-network continuation", []),
        ("BeB2", "light AlB2-type analog", "lighter diboride branch with higher phonon-scale upside", ["metastability_risk"]),
        ("HfB2", "AlB2-type", "heavy diboride boundary comparator", ["SOC_check_later"]),
        ("ZrB2", "AlB2-type", "hard diboride negative-control check", ["low_Tc_risk"]),
        ("TiB2", "AlB2-type", "transition-metal diboride comparator", [])
    ],
    "borocarbide": [
        ("YNi2B2C", "borocarbide prototype", "rare-earth borocarbide EPC/magnetism interplay", []),
        ("LuNi2B2C", "borocarbide prototype", "clean nonmagnetic borocarbide comparator", []),
        ("ErNi2B2C", "borocarbide prototype", "magnetism coexistence borocarbide", ["magnetic_risk"]),
        ("HoNi2B2C", "borocarbide prototype", "magnetism interplay borocarbide", ["magnetic_risk"]),
        ("TmNi2B2C", "borocarbide prototype", "rare-earth tuning within the borocarbide superconducting family", ["magnetic_risk"]),
        ("DyNi2B2C", "borocarbide prototype", "magnetically active borocarbide comparator", ["magnetic_risk"]),
        ("TbNi2B2C", "borocarbide prototype", "stronger-moment rare-earth borocarbide stress test", ["magnetic_risk"]),
        ("BC3", "BC3 layered", "boron-carbon framework metallicization route", ["carrier_density_sensitive"]),
        ("B2C", "boron carbide", "boron-carbon conductor with EPC uncertainty", []),
        ("CaB2C2", "borocarbide framework", "calcium borocarbide framework tuning", []),
        ("MgB2C2", "borocarbide framework", "magnesium borocarbide analog", []),
        ("Li2BC2", "borocarbide framework", "alkali borocarbide carrier tuning", ["carrier_density_sensitive"]),
        ("NaBC2", "borocarbide framework", "alkali borocarbide charge donation", ["carrier_density_sensitive"]),
        ("KB3C4", "alkali borocarbide framework", "heavier alkali donation into a boron-carbon network", ["carrier_density_sensitive"]),
        ("CaB4C4", "calcium borocarbide framework", "larger borocarbide cage continuation", []),
        ("MgB4C4", "magnesium borocarbide framework", "magnesium-rich borocarbide framework extension", [])
    ],
    "cuprate": [
        ("La2CuO4", "214 cuprate", "parent cuprate AF insulator baseline", ["strong_correlation_risk"]),
        ("YBa2Cu3O7", "123 cuprate", "optimally oxygenated CuO2-plane mainline", ["strong_correlation_risk"]),
        ("Bi2Sr2CaCu2O8", "2212 BSCCO", "layered Bi cuprate mainline", ["strong_correlation_risk"]),
        ("La1.85Sr0.15CuO4", "doped 214 cuprate", "explicit optimally doped 214 cuprate", ["strong_correlation_risk", "carrier_density_sensitive"]),
        ("HgBa2Ca2Cu3O8", "Hg-1223", "high-Tc multilayer cuprate ceiling probe", ["strong_correlation_risk", "toxicity_risk"]),
        ("Tl2Ba2Ca2Cu3O10", "Tl-2223", "multilayer thallium cuprate", ["strong_correlation_risk", "toxicity_risk"]),
        ("CaCuO2", "infinite-layer cuprate", "parent infinite-layer cuprate", ["strong_correlation_risk"]),
        ("SrCuO2", "infinite-layer cuprate", "Sr infinite-layer cuprate comparator", ["strong_correlation_risk"]),
        ("Nd2CuO4", "T'-type cuprate", "electron-doped cuprate parent", ["strong_correlation_risk"]),
        ("La2-xBaxCuO4", "Ba-doped 214 cuprate", "stripe-sensitive Ba-doped 214 route", ["strong_correlation_risk", "carrier_density_sensitive"]),
        ("Pr2CuO4", "T'-type cuprate", "rare-earth electron-doped cuprate parent comparator", ["strong_correlation_risk"]),
        ("Sm2CuO4", "T'-type cuprate", "smaller rare-earth electron-doped cuprate boundary test", ["strong_correlation_risk"]),
        ("Eu2CuO4", "T'-type cuprate", "rare-earth contraction test in the T'-cuprate family", ["strong_correlation_risk"]),
        ("HgBa2CuO4", "Hg-1201", "single-layer Hg cuprate continuation of the high-Tc lane", ["strong_correlation_risk", "toxicity_risk"]),
        ("Bi2Sr2CuO6", "2201 BSCCO", "single-layer Bi cuprate comparator", ["strong_correlation_risk"])
    ],
    "iron_based": [
        ("LaFeAsO", "1111 pnictide", "parent FeAs-layer baseline", ["magnetic_risk", "strong_correlation_risk"]),
        ("BaFe2As2", "122 pnictide", "nematic 122 parent", ["magnetic_risk"]),
        ("FeSe", "11 chalcogenide", "simplest iron-based superconducting layer", ["nematicity_risk"]),
        ("LiFeAs", "111 pnictide", "self-doped iron-based superconductor", []),
        ("LaFeAsO0.9F0.1", "F-doped 1111", "explicit doped 1111 route", ["carrier_density_sensitive"]),
        ("Ba0.6K0.4Fe2As2", "K-doped 122", "explicit hole-doped 122 route", ["carrier_density_sensitive"]),
        ("BaFe2P2", "122 phosphide", "lighter anion iron-based comparator", []),
        ("LaFePO", "1111 phosphide", "lower-Tc phosphide comparator", []),
        ("CaFe2As2", "122 calcium analog", "pressure-sensitive 122 analog", []),
        ("SrFe2As2", "122 strontium analog", "A-site tuning in 122 family", []),
        ("FeTe0.5Se0.5", "mixed chalcogenide iron-based", "mixed-anion iron layer route", ["configurational_disorder"]),
        ("NaFeAs", "111 pnictide", "alkali 111 iron-pnictide continuation", ["magnetic_risk"]),
        ("KFe2As2", "122 hole-rich pnictide", "overdoped hole-side 122 comparator", ["carrier_density_sensitive"]),
        ("RbFe2As2", "122 hole-rich pnictide", "heavier alkali 122 hole-side comparator", ["carrier_density_sensitive"]),
        ("CsFe2As2", "122 hole-rich pnictide", "largest-alkali 122 hole-side boundary test", ["carrier_density_sensitive"]),
        ("FeS", "11 sulfide", "lighter-anion iron-chalcogenide comparator", [])
    ],
    "nickelate": [
        ("NdNiO2", "infinite-layer nickelate", "parent infinite-layer nickelate", ["strong_correlation_risk", "carrier_density_sensitive"]),
        ("LaNiO2", "infinite-layer nickelate", "La infinite-layer nickelate parent", ["strong_correlation_risk", "carrier_density_sensitive"]),
        ("PrNiO2", "infinite-layer nickelate", "rare-earth tuned parent nickelate", ["strong_correlation_risk", "carrier_density_sensitive"]),
        ("Nd0.8Sr0.2NiO2", "Sr-doped infinite-layer nickelate", "explicit hole-doped mainline nickelate", ["strong_correlation_risk", "carrier_density_sensitive"]),
        ("La0.8Sr0.2NiO2", "Sr-doped infinite-layer nickelate", "La hole-doped nickelate variant", ["strong_correlation_risk", "carrier_density_sensitive"]),
        ("Pr0.8Sr0.2NiO2", "Sr-doped infinite-layer nickelate", "Pr hole-doped nickelate variant", ["strong_correlation_risk", "carrier_density_sensitive"]),
        ("Ba2NiO2F2", "square-ligand nickel oxyfluoride", "square-planar ligand-field nickelate extension", ["strong_correlation_risk", "ligand_field_sensitive"]),
        ("AgF2", "silver fluoride analog", "square-ligand cuprate-adjacent comparator", ["strong_correlation_risk", "conjecture_only", "ligand_field_sensitive"]),
        ("Cs2AgF4", "layered silver fluoride", "K2NiF4-like silver fluoride comparator", ["strong_correlation_risk", "magnetic_risk", "conjecture_only"]),
        ("La2PdO4", "214 palladate analog", "4d boundary comparator", ["strong_correlation_risk", "wider_band_risk"]),
        ("LaPdO2", "infinite-layer palladate", "4d infinite-layer boundary comparator", ["strong_correlation_risk", "carrier_density_sensitive", "wider_band_risk"]),
        ("SmNiO2", "infinite-layer nickelate", "smaller rare-earth parent nickelate continuation", ["strong_correlation_risk", "carrier_density_sensitive", "conjecture_only"]),
        ("EuNiO2", "infinite-layer nickelate", "rare-earth contraction test in the infinite-layer nickelate lane", ["strong_correlation_risk", "carrier_density_sensitive", "conjecture_only"]),
        ("GdNiO2", "infinite-layer nickelate", "late rare-earth infinite-layer nickelate boundary probe", ["strong_correlation_risk", "carrier_density_sensitive", "conjecture_only"]),
        ("Sm0.8Sr0.2NiO2", "Sr-doped infinite-layer nickelate", "hole-doped Sm nickelate continuation", ["strong_correlation_risk", "carrier_density_sensitive", "conjecture_only"]),
        ("Eu0.8Sr0.2NiO2", "Sr-doped infinite-layer nickelate", "hole-doped Eu nickelate continuation", ["strong_correlation_risk", "carrier_density_sensitive", "conjecture_only"])
    ],
    "hydride": [
        ("SnH4", "group 14 hydride", "p-block hydride under pressure", ["high_pressure_risk"]),
        ("PbH4", "group 14 hydride", "heavy p-block hydride under pressure", ["high_pressure_risk", "SOC_check_later"]),
        ("BiH3", "group 15 hydride", "bismuth hydride high-pressure route", ["high_pressure_risk", "SOC_check_later"]),
        ("SbH3", "group 15 hydride", "antimony hydride high-pressure route", ["high_pressure_risk"]),
        ("TeH2", "group 16 hydride", "tellurium hydride pressure route", ["high_pressure_risk"]),
        ("SbCH6", "Sb-C-H ternary hydride", "ternary cage hydride route", ["high_pressure_risk"]),
        ("SnCH6", "Sn-C-H ternary hydride", "lower-pressure-target ternary hydride", ["high_pressure_risk"]),
        ("Bi2H6", "bismuth hydride dimer", "heavy hydride dimer route", ["high_pressure_risk", "SOC_check_later"]),
        ("BaSiH8", "ternary superhydride", "lower-pressure ternary hydride target", ["high_pressure_risk"]),
        ("Mg2IrH6", "ambient-leaning ternary hydride", "chemical-precompression hydride route", ["metastability_risk"]),
        ("GeH4", "group 14 hydride", "lighter group-14 hydride route under pressure", ["high_pressure_risk"]),
        ("SiH4", "group 14 hydride", "silane-derived high-pressure EPC route", ["high_pressure_risk"]),
        ("PH3", "group 15 hydride", "phosphine-family high-pressure hydride route", ["high_pressure_risk"]),
        ("AsH3", "group 15 hydride", "arsenic hydride pressure route", ["high_pressure_risk"]),
        ("SbH4", "group 15 hydride", "hydrogen-richer antimony hydride continuation", ["high_pressure_risk"])
    ],
    "conventional": [
        ("TiN", "rocksalt TiN", "hard conventional nitride superconductor", []),
        ("TiC", "rocksalt TiC", "conventional carbide superconductor", []),
        ("WO3", "doped tungsten bronze route", "dilute-carrier oxide bronze route", ["carrier_density_sensitive", "oxygen_vacancy_sensitive"]),
        ("SrTiO3", "dilute-carrier oxide", "low-density superconducting oxide route", ["carrier_density_sensitive", "oxygen_vacancy_sensitive"]),
        ("KTaO3", "dilute-carrier oxide", "SOC-aware dilute-carrier oxide route", ["carrier_density_sensitive", "SOC_check_later"]),
        ("Ba8Si46", "silicon clathrate", "clathrate conventional superconductor", []),
        ("Ba8Ge46", "germanium clathrate", "clathrate analog", []),
        ("ZrNCl", "layered nitride halide", "intercalation-enabled nitride superconductor host", ["carrier_density_sensitive"]),
        ("HfNCl", "layered nitride halide", "heavy nitride halide analog", ["carrier_density_sensitive", "SOC_check_later"]),
        ("Mo2C", "MXene/carbide comparator", "known carbide/MXene superconducting anchor", ["surface_termination_sensitive"]),
        ("Nb2C", "MXene/carbide comparator", "niobium MXene superconducting route", ["surface_termination_sensitive"]),
        ("LaAlO3/SrTiO3", "oxide interface", "canonical interfacial superconductivity anchor", ["interface_required", "carrier_density_sensitive"]),
        ("TaC", "rocksalt tantalum carbide", "heavier carbide continuation of the conventional refractory route", []),
        ("NbC", "rocksalt niobium carbide", "classical carbide superconducting comparator", []),
        ("MoN", "molybdenum nitride", "nitride continuation of the refractory conventional lane", []),
        ("NbN", "niobium nitride", "canonical nitride superconducting comparator", []),
        ("TaN", "tantalum nitride", "heavy nitride conventional boundary test", [])
    ],
    "elemental": [
        ("Nb", "elemental Nb", "canonical elemental superconducting anchor", []),
        ("Pb", "elemental Pb", "canonical elemental superconducting anchor", []),
        ("Ta", "elemental Ta", "elemental BCS superconductor", []),
        ("V", "elemental V", "elemental transition-metal superconductor", []),
        ("Hg", "elemental Hg", "historical first elemental superconductor", []),
        ("Ga", "elemental Ga", "phase-sensitive elemental superconductor", ["phase_sensitive"]),
        ("In", "elemental In", "elemental superconducting comparator", []),
        ("Sn", "elemental Sn", "low-Tc elemental BCS continuation", []),
        ("Al", "elemental Al", "light-element elemental superconducting comparator", []),
        ("Tl", "elemental Tl", "heavy p-block elemental superconducting comparator", ["SOC_check_later"]),
        ("Re", "elemental Re", "high-mass elemental transition-metal superconductor", ["SOC_check_later"]),
        ("Mo", "elemental Mo", "elemental refractory boundary comparator", ["low_Tc_risk"])
    ],
    "chalcogenide": [
        ("Bi2Se3", "topological chalcogenide", "SOC-rich chalcogenide with doped superconducting route", ["SOC_check_later"]),
        ("Cu0.3Bi2Se3", "Cu-doped topological chalcogenide", "doped topological chalcogenide superconductor", ["SOC_check_later", "carrier_density_sensitive"]),
        ("Sr0.1Bi2Se3", "Sr-doped topological chalcogenide", "intercalated chalcogenide route", ["SOC_check_later", "carrier_density_sensitive"]),
        ("Bi2Te3", "topological chalcogenide", "telluride chalcogenide comparator", ["SOC_check_later"]),
        ("PbTe", "lead telluride", "pressure/doping chalcogenide route", ["SOC_check_later"]),
        ("PbSe", "lead selenide", "lead chalcogenide comparator", ["SOC_check_later"]),
        ("WTe2", "Weyl telluride", "pressure-sensitive chalcogenide route", ["SOC_check_later", "high_pressure_risk"]),
        ("MoTe2", "telluride semimetal", "chalcogenide/topological boundary route", ["SOC_check_later"]),
        ("Bi2S3", "lighter chalcogenide", "reduced-SOC chalcogenide comparator", ["SOC_check_later"]),
        ("Bi2Se2S", "mixed chalcogenide", "mixed-anion chalcogenide comparator", ["SOC_check_later"]),
        ("SnTe", "topological crystalline telluride", "SOC-rich telluride superconducting route under doping/pressure", ["SOC_check_later"]),
        ("In2Se3", "layered chalcogenide", "layered post-transition chalcogenide boundary test", ["carrier_density_sensitive"]),
        ("TaS2", "layered dichalcogenide", "CDW-competing dichalcogenide superconducting route", ["cdw_competition"]),
        ("NbSe2", "layered dichalcogenide", "canonical layered chalcogenide superconducting comparator", []),
        ("TiSe2", "layered dichalcogenide", "CDW-tuned layered chalcogenide route", ["cdw_competition"])
    ],
    "heavy_fermion": [
        ("CeCu2Si2", "heavy-fermion prototype", "first heavy-fermion superconductor anchor", ["magnetic_risk", "low_tc_regime"]),
        ("CeCoIn5", "115 heavy fermion", "high-profile heavy-fermion QCP superconductor", ["magnetic_risk", "low_tc_regime"]),
        ("CeIrIn5", "115 heavy fermion", "115 family comparator", ["magnetic_risk", "low_tc_regime"]),
        ("UPt3", "uranium heavy fermion", "multi-component heavy-fermion superconductor", ["magnetic_risk", "low_tc_regime"]),
        ("UBe13", "uranium heavy fermion", "canonical heavy-fermion superconductor", ["magnetic_risk", "low_tc_regime"]),
        ("URu2Si2", "uranium heavy fermion", "hidden-order heavy-fermion route", ["magnetic_risk", "low_tc_regime"]),
        ("UTe2", "uranium telluride", "spin-triplet heavy-fermion candidate", ["magnetic_risk", "low_tc_regime"]),
        ("UPd2Al3", "uranium heavy fermion", "magnetism coexistence comparator", ["magnetic_risk", "low_tc_regime"]),
        ("PuCoGa5", "actinide heavy fermion", "higher-Tc actinide heavy-fermion boundary", ["magnetic_risk"]),
        ("CeRhIn5", "115 heavy fermion", "pressure-nearby 115 heavy-fermion comparator", ["magnetic_risk", "low_tc_regime"]),
        ("CeIrSi3", "noncentrosymmetric heavy fermion", "parity-mixed heavy-fermion route", ["magnetic_risk", "low_tc_regime"]),
        ("CePt3Si", "noncentrosymmetric heavy fermion", "SOC-entangled heavy-fermion superconducting comparator", ["magnetic_risk", "low_tc_regime", "SOC_check_later"]),
        ("NpPd5Al2", "actinide heavy fermion", "actinide heavy-fermion continuation", ["magnetic_risk", "low_tc_regime"]),
        ("PuRhGa5", "actinide heavy fermion", "actinide analog to PuCoGa5", ["magnetic_risk", "low_tc_regime"])
    ],
    "kagome": [
        ("CsV3Sb5", "AV3Sb5 kagome", "kagome superconducting anchor", ["cdw_competition"]),
        ("KV3Sb5", "AV3Sb5 kagome", "kagome alkali variation", ["cdw_competition"]),
        ("RbV3Sb5", "AV3Sb5 kagome", "kagome alkali variation", ["cdw_competition"]),
        ("CsNb3Sb5", "ANb3Sb5 kagome", "niobium kagome analog", []),
        ("CsTa3Sb5", "ATa3Sb5 kagome", "tantalum kagome analog", ["SOC_check_later"]),
        ("KNb3Sb5", "ANb3Sb5 kagome", "potassium niobium kagome analog", []),
        ("RbNb3Sb5", "ANb3Sb5 kagome", "rubidium niobium kagome analog", []),
        ("CsV3Bi5", "AV3Bi5 kagome", "Bi-substituted kagome analog", ["SOC_check_later", "cdw_competition"]),
        ("CsCr3Sb5", "chromium kagome analog", "magnetic kagome stress test", ["magnetic_risk"]),
        ("BaFe6Sn6", "Fe kagome metal", "magnetic kagome-related boundary material", ["magnetic_risk"]),
        ("KV3Bi5", "AV3Bi5 kagome", "potassium bismuth kagome analog", ["SOC_check_later", "cdw_competition"]),
        ("RbV3Bi5", "AV3Bi5 kagome", "rubidium bismuth kagome analog", ["SOC_check_later", "cdw_competition"]),
        ("CsTi3Bi5", "ATi3Bi5 kagome", "Ti-based kagome continuation with lighter d filling", ["SOC_check_later"]),
        ("KTi3Bi5", "ATi3Bi5 kagome", "alkali-titanium kagome analog", ["SOC_check_later"]),
        ("RbTi3Bi5", "ATi3Bi5 kagome", "rubidium titanium kagome analog", ["SOC_check_later"])
    ],
    "frontier_first_principles": [
        ("BC2H", "B-C-H framework", "mixed covalent/hydrogen frontier route", ["metastability_risk"]),
        ("B2N2H2", "B-N-H framework", "heterocovalent frontier hydride route", ["metastability_risk"]),
        ("BC3N3", "B-C-N sodalite", "sodalite-like mixed light-element frontier route", ["metastability_risk"]),
        ("Li2B4H4", "Li-B-H framework", "alkali borohydride frontier route", ["metastability_risk"]),
        ("Ca2B10H10", "closoborane framework", "cage-stabilized frontier route", ["metastability_risk"]),
        ("Nb0.25V0.25Ti0.25Zr0.25B2", "high-entropy diboride", "high-entropy superconducting motif search", ["configurational_disorder_high"]),
        ("TiZrNbHfB2", "high-entropy diboride", "multi-principal diboride frontier route", ["configurational_disorder_high"]),
        ("TiNbZrVCrN", "high-entropy nitride", "high-entropy nitride frontier route", ["configurational_disorder_high"]),
        ("FeSe/LaAlO3(001)", "interface frontier", "monolayer/interface-enhanced superconductivity route", ["interface_required", "conjecture_only"]),
        ("Al3Mg2", "intermetallic frontier", "light-element intermetallic frontier route", []),
        ("W2B5", "tungsten boride frontier", "heavy-boride frontier route", ["SOC_check_later"]),
        ("Nb0.25Ta0.25Ti0.25Zr0.25B2", "high-entropy diboride", "Ta-bearing high-entropy diboride continuation", ["configurational_disorder_high", "SOC_check_later"]),
        ("TiZrNbHfN", "high-entropy nitride", "quaternary nitride high-entropy continuation", ["configurational_disorder_high"]),
        ("Li2B6H6", "borohydride cage frontier", "lighter closoborane continuation for frontier screening", ["metastability_risk"]),
        ("CaB6H6", "alkaline-earth borohydride frontier", "calcium-stabilized light-element cage frontier", ["metastability_risk"]),
        ("FeSe/KTaO3(001)", "interface frontier", "oxide-assisted monolayer FeSe continuation on a distinct dielectric host", ["interface_required", "conjecture_only"])
    ]
}


def estimate_required_pressure_gpa(branch: str, formula: str) -> int | None:
    """Soft pressure prior used for routing; not a hard gate."""
    if branch == "p_block_hydride":
        return HYDRIDE_PRESSURE_PRIORS_GPA.get(formula, 100)
    if formula in HYDRIDE_PRESSURE_PRIORS_GPA:
        return HYDRIDE_PRESSURE_PRIORS_GPA[formula]
    return None


def enrich_candidate_metadata(candidate: dict) -> dict:
    branch = candidate.get("branch", "")
    formula = candidate.get("formula", "")
    risk_tags = list(candidate.get("risk_tags", []))
    lane_meta = lane_metadata_for(branch, formula, risk_tags)
    condition_class = infer_condition_class(branch, formula, risk_tags)
    required_condition_vector = infer_required_condition_vector(branch, formula, risk_tags)

    candidate["lane_id"] = lane_meta["lane_id"]
    candidate["condition_class"] = condition_class
    candidate["required_condition_vector"] = required_condition_vector
    candidate["mechanism_family"] = lane_meta["mechanism_family"]
    candidate["family_confidence"] = lane_meta["family_confidence"]
    candidate["generation_mode"] = lane_meta["generation_mode"]
    candidate["validation_recipe_id"] = lane_meta["validation_recipe_id"]
    candidate["family_ruleset_id"] = lane_meta["family_ruleset_id"]
    candidate["lane_priority_score"] = lane_meta["lane_priority_bias"]

    required_pressure = estimate_required_pressure_gpa(branch, formula)
    if required_pressure is not None:
        candidate["estimated_required_pressure_gpa"] = required_pressure
        candidate["pressure_estimate_source"] = "sclib_hydride_prior_v1"
        candidate["pressure_estimate_kind"] = "soft_prior"
    if branch == "p_block_hydride":
        tags = list(dict.fromkeys(candidate.get("risk_tags", [])))
        if "hydride_pressure_tuned" not in tags:
            tags.append("hydride_pressure_tuned")
        candidate["risk_tags"] = tags
    return candidate


def load_public_corpus_formulas() -> set[str]:
    if not CORPUS_REGISTRY.exists():
        return set()
    formulas: set[str] = set()
    for line in CORPUS_REGISTRY.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            formulas.add(json.loads(line).get("formula", ""))
        except Exception:
            continue
    formulas.discard("")
    return formulas


def branch_templates_with_exclusion(branch: str, excluded_formulas: set[str]) -> list[tuple]:
    templates = LANE_TEMPLATES.get(branch, [])
    if not excluded_formulas:
        return templates
    fresh = [tmpl for tmpl in templates if tmpl[0] not in excluded_formulas]
    return fresh


def generate_candidates(n_total=200, seed=42, excluded_formulas: set[str] | None = None):
    """Generate E0/E1 candidates across the 12 active lanes."""
    random.seed(seed)
    excluded_formulas = excluded_formulas or set()
    branches = list(LANE_WEIGHTS.keys())
    weights = [LANE_WEIGHTS[b] for b in branches]
    
    candidates = []
    cid = 1
    date_str = datetime.today().strftime("%Y-%m-%d")
    
    # Ensure minimum coverage per lane so low-volume lanes stay alive.
    min_per_branch = 4
    guaranteed = []
    formula_counts: Counter[str] = Counter()
    for branch in branches:
        templates = branch_templates_with_exclusion(branch, excluded_formulas)
        if not templates:
            continue
        for tmpl in templates[:min_per_branch]:
            formula, parent, mech, risks = tmpl
            guaranteed.append(enrich_candidate_metadata({
                "candidate_id": f"E0-{date_str}-{cid:04d}",
                "formula": formula,
                "family": branch,
                "branch": branch,
                "evidence_level": "E0" if not any(True for _ in []) else "E1",
                "structure_source": f"template:{parent}",
                "generation_reason": f"minimum branch coverage",
                "parent_formula_or_template": parent,
                "mechanism_hypothesis": mech,
                "required_physics_tags": [],
                "risk_tags": risks,
                "prescreen_score": None,
                "discovery_score": None,
                "experiment_score": None,
                "dft_status": "not_started",
                "phonon_status": "not_started",
                "checker_status": "pending",
                "next_action": "prescreen",
                "created": date_str,
            }))
            formula_counts[formula] += 1
            cid += 1
    
    # Fill remaining by weighted branch sampling
    remaining = n_total - len(guaranteed)
    for _ in range(remaining):
        branch = random.choices(branches, weights=weights)[0]
        templates = branch_templates_with_exclusion(branch, excluded_formulas)
        if not templates:
            continue
        min_count = min(formula_counts.get(tmpl[0], 0) for tmpl in templates)
        least_used = [tmpl for tmpl in templates if formula_counts.get(tmpl[0], 0) == min_count]
        formula, parent, mech, risks = random.choice(least_used)
        candidates.append(enrich_candidate_metadata({
            "candidate_id": f"E0-{date_str}-{cid:04d}",
            "formula": formula,
            "family": branch,
            "branch": branch,
            "evidence_level": "E0",
            "structure_source": f"template:{parent}",
            "generation_reason": "weighted branch sampling",
            "parent_formula_or_template": parent,
            "mechanism_hypothesis": mech,
            "required_physics_tags": [],
            "risk_tags": risks,
            "prescreen_score": None,
            "discovery_score": None,
            "experiment_score": None,
            "dft_status": "not_started",
            "phonon_status": "not_started",
            "checker_status": "pending",
            "next_action": "prescreen",
            "created": date_str,
        }))
        formula_counts[formula] += 1
        cid += 1
    
    all_candidates = guaranteed + candidates
    return all_candidates


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-total", type=int, default=300)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--exclude-corpus",
        action="store_true",
        help="Prefer formulas not already present in the public credible corpus.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    date_str = datetime.today().strftime("%Y-%m-%d")
    out_dir = CANDIDATES_DIR / date_str
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "candidate_manifest.jsonl"

    excluded_formulas = load_public_corpus_formulas() if args.exclude_corpus else set()
    candidates = generate_candidates(
        n_total=args.n_total,
        seed=args.seed,
        excluded_formulas=excluded_formulas,
    )
    
    with open(out_file, "w") as f:
        for c in candidates:
            f.write(json.dumps(c) + "\n")
    
    print(f"Generated {len(candidates)} candidates -> {out_file}")
    if excluded_formulas:
        print(f"Preferred formulas outside public corpus: {len(excluded_formulas)} excluded")
    
    # Branch summary
    from collections import Counter
    counts = Counter(c["branch"] for c in candidates)
    for branch, count in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {branch}: {count}")
