#!/usr/bin/env python3
"""
LOOP-SC Candidate Generator v0.1
Generates E0/E1 candidates across all 14 active branches.
"""
import json, random, itertools
from datetime import datetime
from pathlib import Path

SC_ROOT = Path(__file__).parent.parent
CANDIDATES_DIR = SC_ROOT / "candidates"

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
        ("La2NiO4",    "214 Ni analog", "Ni d8 vs d9, orbital check", ["strong_correlation_risk"]),
        ("La2CoO4",    "214 Co analog", "Co d7, check spin state", ["strong_correlation_risk","magnetic_risk"]),
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

def generate_candidates(n_total=200, seed=42):
    """Generate E0/E1 candidates across all branches."""
    random.seed(seed)
    branches = list(BRANCH_WEIGHTS.keys())
    weights = [BRANCH_WEIGHTS[b] for b in branches]
    
    candidates = []
    cid = 1
    date_str = datetime.today().strftime("%Y-%m-%d")
    
    # Ensure minimum coverage: 5 per branch for n_total <= 1000
    min_per_branch = 5
    guaranteed = []
    for branch in branches:
        templates = BRANCH_TEMPLATES.get(branch, [])
        if not templates:
            continue
        for tmpl in templates[:min_per_branch]:
            formula, parent, mech, risks = tmpl
            guaranteed.append({
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
            })
            cid += 1
    
    # Fill remaining by weighted branch sampling
    remaining = n_total - len(guaranteed)
    for _ in range(remaining):
        branch = random.choices(branches, weights=weights)[0]
        templates = BRANCH_TEMPLATES.get(branch, [])
        if not templates:
            continue
        formula, parent, mech, risks = random.choice(templates)
        candidates.append({
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
        })
        cid += 1
    
    all_candidates = guaranteed + candidates
    return all_candidates

if __name__ == "__main__":
    date_str = datetime.today().strftime("%Y-%m-%d")
    out_dir = CANDIDATES_DIR / date_str
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "candidate_manifest.jsonl"
    
    candidates = generate_candidates(n_total=300)
    
    with open(out_file, "w") as f:
        for c in candidates:
            f.write(json.dumps(c) + "\n")
    
    print(f"Generated {len(candidates)} candidates -> {out_file}")
    
    # Branch summary
    from collections import Counter
    counts = Counter(c["branch"] for c in candidates)
    for branch, count in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {branch}: {count}")
