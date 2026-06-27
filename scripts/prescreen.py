#!/usr/bin/env python3
"""
LOOP-SC Prescreen Module v0.2

Base mode:
- heuristic prescreen for all candidates

Optional CHGNet mode:
- evaluate a small prototype-structure subset
- use CHGNet force magnitude as a structure-confidence proxy
"""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from pymatgen.core import Lattice, Structure

SC_ROOT = Path(__file__).parent.parent

METALLIC_FAMILIES = {
    "AlB2_MgB2_boride",
    "BC_framework",
    "iron_based_extrapolation",
    "AlTiPbW_exploratory",
    "kagome_vanHove",
    "MXene_2D",
    "layered_nitride_halonitride",
}

KNOWN_SC_PROTOTYPES = {
    "MgB2",
    "NbB2",
    "ZrB2",
    "MoB2",
    "WB2",
    "TiB2",
    "LaFeAsO",
    "BaFe2As2",
    "FeSe",
    "LiFeAs",
    "Ba0.6K0.4Fe2As2",
    "ZrNCl",
    "HfNCl",
    "Ba8Si46",
    "CsV3Sb5",
    "KV3Sb5",
    "RbV3Sb5",
    "Mo2C",
    "Bi2Se3",
    "Cu0.3Bi2Se3",
    "SrTiO3",
    "WO3",
    "TiN",
    "La2CuO4",
    "YBa2Cu3O7",
    "Bi2Sr2CaCu2O8",
    "HgBa2Ca2Cu3O8",
    "La1.85Sr0.15CuO4",
    "LiBC",
    "BC3",
    "NdNiO2",
    "LaNiO2",
    "PrNiO2",
    "Nd0.8Sr0.2NiO2",
    "La0.8Sr0.2NiO2",
    "Pr0.8Sr0.2NiO2",
    "AgF2",
    "Cs2AgF4",
    "Ba2NiO2F2",
    "La2PdO4",
    "LaPdO2",
}

FORBIDDEN_KEYWORDS = {"MOF", "COF", "organic", "porphyrin", "fullerene"}


def make_structure_builders() -> dict[str, Structure]:
    structures: dict[str, Structure] = {}

    structures["Nb"] = Structure(Lattice.cubic(3.3001), ["Nb"], [[0, 0, 0]])
    structures["Pb"] = Structure(Lattice.cubic(4.9492), ["Pb"], [[0, 0, 0]])
    structures["MgB2"] = Structure(
        Lattice.hexagonal(3.086, 3.524),
        ["Mg", "B", "B"],
        [[0, 0, 0], [1 / 3, 2 / 3, 0.5], [2 / 3, 1 / 3, 0.5]],
    )
    structures["TiN"] = Structure(Lattice.cubic(4.24), ["Ti", "N"], [[0, 0, 0], [0.5, 0.5, 0.5]])
    structures["SrTiO3"] = Structure(
        Lattice.cubic(3.905),
        ["Sr", "Ti", "O", "O", "O"],
        [[0, 0, 0], [0.5, 0.5, 0.5], [0.5, 0.5, 0], [0.5, 0, 0.5], [0, 0.5, 0.5]],
    )
    structures["CaTiO3"] = Structure(
        Lattice.cubic(3.82),
        ["Ca", "Ti", "O", "O", "O"],
        [[0, 0, 0], [0.5, 0.5, 0.5], [0.5, 0.5, 0], [0.5, 0, 0.5], [0, 0.5, 0.5]],
    )
    structures["BaTiO3"] = Structure(
        Lattice.cubic(4.00),
        ["Ba", "Ti", "O", "O", "O"],
        [[0, 0, 0], [0.5, 0.5, 0.5], [0.5, 0.5, 0], [0.5, 0, 0.5], [0, 0.5, 0.5]],
    )
    structures["KTaO3"] = Structure(
        Lattice.cubic(3.989),
        ["K", "Ta", "O", "O", "O"],
        [[0, 0, 0], [0.5, 0.5, 0.5], [0.5, 0.5, 0], [0.5, 0, 0.5], [0, 0.5, 0.5]],
    )
    structures["TiO2"] = Structure(
        Lattice.tetragonal(4.593, 2.959),
        ["Ti", "Ti", "O", "O", "O", "O"],
        [
            [0, 0, 0],
            [0.5, 0.5, 0.5],
            [0.305, 0.305, 0],
            [0.695, 0.695, 0],
            [0.805, 0.195, 0.5],
            [0.195, 0.805, 0.5],
        ],
    )
    structures["WO3"] = Structure(
        Lattice.cubic(3.78),
        ["W", "O", "O", "O"],
        [[0, 0, 0], [0.5, 0.5, 0], [0.5, 0, 0.5], [0, 0.5, 0.5]],
    )
    structures["LiBC"] = Structure(
        Lattice.hexagonal(2.75, 7.06),
        ["Li", "B", "C", "Li", "B", "C"],
        [
            [0, 0, 0.25],
            [1 / 3, 2 / 3, 0.125],
            [2 / 3, 1 / 3, 0.125],
            [0, 0, 0.75],
            [2 / 3, 1 / 3, 0.625],
            [1 / 3, 2 / 3, 0.625],
        ],
    )
    structures["NdNiO2"] = Structure(
        Lattice.tetragonal(3.92, 3.31),
        ["Nd", "Ni", "O", "O"],
        [[0, 0, 0], [0.5, 0.5, 0.5], [0.5, 0, 0.5], [0, 0.5, 0.5]],
    )
    structures["LaNiO2"] = Structure(
        Lattice.tetragonal(3.96, 3.38),
        ["La", "Ni", "O", "O"],
        [[0, 0, 0], [0.5, 0.5, 0.5], [0.5, 0, 0.5], [0, 0.5, 0.5]],
    )
    structures["PrNiO2"] = Structure(
        Lattice.tetragonal(3.94, 3.33),
        ["Pr", "Ni", "O", "O"],
        [[0, 0, 0], [0.5, 0.5, 0.5], [0.5, 0, 0.5], [0, 0.5, 0.5]],
    )
    structures["AgF2"] = Structure(
        Lattice.tetragonal(4.60, 3.30),
        ["Ag", "F", "F"],
        [[0, 0, 0], [0.5, 0, 0.5], [0, 0.5, 0.5]],
    )
    structures["Cs2AgF4"] = Structure(
        Lattice.tetragonal(4.55, 13.80),
        ["Cs", "Cs", "Ag", "F", "F", "F", "F"],
        [
            [0, 0, 0.0],
            [0.5, 0.5, 0.5],
            [0, 0, 0.25],
            [0.5, 0, 0.25],
            [0, 0.5, 0.25],
            [0.5, 0, 0.75],
            [0, 0.5, 0.75],
        ],
    )
    structures["Ba2NiO2F2"] = Structure(
        Lattice.tetragonal(4.02, 12.70),
        ["Ba", "Ba", "Ni", "O", "O", "F", "F"],
        [
            [0, 0, 0.0],
            [0.5, 0.5, 0.5],
            [0, 0, 0.25],
            [0.5, 0, 0.25],
            [0, 0.5, 0.25],
            [0.5, 0, 0.75],
            [0, 0.5, 0.75],
        ],
    )
    structures["La2PdO4"] = Structure(
        Lattice.tetragonal(4.03, 12.90),
        ["La", "La", "Pd", "O", "O", "O", "O"],
        [
            [0, 0, 0.0],
            [0.5, 0.5, 0.5],
            [0, 0, 0.25],
            [0.5, 0, 0.25],
            [0, 0.5, 0.25],
            [0.5, 0, 0.75],
            [0, 0.5, 0.75],
        ],
    )
    structures["LaPdO2"] = Structure(
        Lattice.tetragonal(4.05, 3.45),
        ["La", "Pd", "O", "O"],
        [[0, 0, 0], [0.5, 0.5, 0.5], [0.5, 0, 0.5], [0, 0.5, 0.5]],
    )
    return structures


def prescreen_score(candidate: dict) -> tuple[float, str]:
    score = 50.0
    formula = candidate.get("formula", "")
    branch = candidate.get("branch", "")
    risks = candidate.get("risk_tags", [])

    for kw in FORBIDDEN_KEYWORDS:
        if kw.lower() in formula.lower():
            return 0.0, "excluded_v0.1"

    if formula in KNOWN_SC_PROTOTYPES:
        score += 25

    if branch in METALLIC_FAMILIES:
        score += 10

    if "high_pressure_risk" in risks:
        score -= 15
    if "strong_correlation_risk" in risks:
        score -= 8
    if "magnetic_risk" in risks:
        score -= 10
    if "metastability_risk" in risks:
        score -= 8
    if "carrier_density_sensitive" in risks:
        score -= 5
    if "configurational_disorder_high" in risks:
        score -= 5
    if "conjecture_only" in risks:
        score -= 4
    if "wider_band_risk" in risks:
        score -= 6
    if "ligand_field_sensitive" in risks:
        score -= 4

    light_els = set("BCNH")
    formula_els = {char for char in formula if char.isupper()}
    if formula_els & light_els:
        score += 8

    if len(formula) <= 5:
        score += 5

    if branch == "AlB2_MgB2_boride":
        score += 5

    return min(100.0, max(0.0, score)), "heuristic"


def compute_discovery_score(ps: float, chgnet_force_max: float | None) -> float:
    score = 0.6 * ps + 0.4 * 50.0
    if chgnet_force_max is not None:
        if chgnet_force_max < 0.2:
            score += 8
        elif chgnet_force_max < 0.5:
            score += 4
        elif chgnet_force_max > 2.0:
            score -= 10
        elif chgnet_force_max > 1.0:
            score -= 5
    return round(min(100.0, max(0.0, score)), 1)


def maybe_load_chgnet(enabled: bool):
    if not enabled:
        return None
    from chgnet.model import CHGNet

    return CHGNet.load()


def chgnet_probe(candidate: dict, model, structure_builders: dict[str, Structure]) -> dict:
    formula = candidate.get("formula", "")
    if model is None:
        return {"chgnet_ready": False, "chgnet_reason": "disabled"}
    structure = structure_builders.get(formula)
    if structure is None:
        return {"chgnet_ready": False, "chgnet_reason": "no_structure_proxy"}

    output = model.predict_structure(structure)
    forces = output["f"]
    max_force = max(math.sqrt(float(x * x + y * y + z * z)) for x, y, z in forces.tolist())
    energy_per_atom = float(output["e"]) / len(structure)
    return {
        "chgnet_ready": True,
        "chgnet_reason": "prototype_proxy",
        "chgnet_energy_ev_atom": round(energy_per_atom, 6),
        "chgnet_force_max_ev_ang": round(max_force, 6),
        "structure_proxy_source": f"prototype:{formula}",
    }


def run_prescreen(manifest_path: Path, use_chgnet: bool = False):
    candidates = [json.loads(line) for line in manifest_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    model = maybe_load_chgnet(use_chgnet)
    structure_builders = make_structure_builders()

    results = []
    branch_stats = defaultdict(list)
    chgnet_covered = 0

    for candidate in candidates:
        ps, _ = prescreen_score(candidate)
        chgnet_info = chgnet_probe(candidate, model, structure_builders)
        candidate.update(chgnet_info)
        ds = compute_discovery_score(ps, candidate.get("chgnet_force_max_ev_ang"))

        candidate["prescreen_score"] = round(ps, 1)
        candidate["discovery_score"] = ds
        if ps >= 55:
            candidate["evidence_level"] = "E1"
        if candidate.get("chgnet_ready"):
            chgnet_covered += 1

        results.append(candidate)
        branch_stats[candidate["branch"]].append(ps)

    results.sort(key=lambda item: (-(item["prescreen_score"] or 0), -(item["discovery_score"] or 0), item["formula"]))
    updated_path = manifest_path.parent / "candidate_manifest_prescreened.jsonl"
    with updated_path.open("w", encoding="utf-8") as handle:
        for item in results:
            handle.write(json.dumps(item) + "\n")

    return results, branch_stats, chgnet_covered


def write_prescreen_leaderboard(results, branch_stats, chgnet_covered: int, out_path: Path) -> None:
    date_str = datetime.today().strftime("%Y-%m-%d")
    top50 = results[:50]

    lines = [
        "# Prescreen Leaderboard",
        "",
        f"Generated: {date_str}",
        f"Total candidates: {len(results)}",
        f"E1 (score >= 55): {sum(1 for item in results if item['prescreen_score'] >= 55)}",
        f"CHGNet-covered candidates: {chgnet_covered}",
        "",
        "## Top 50 Candidates",
        "",
        "| Rank | ID | Formula | Branch | PS | Disc | CHGNet | Top Risk |",
        "|------|----|---------|--------|----|------|--------|----------|",
    ]

    for rank, item in enumerate(top50, 1):
        risks = item.get("risk_tags", [])
        top_risk = risks[0] if risks else "none"
        chgnet_tag = (
            f"{item['chgnet_force_max_ev_ang']:.2f}"
            if item.get("chgnet_ready")
            else item.get("chgnet_reason", "no")
        )
        lines.append(
            f"| {rank} | {item['candidate_id']} | {item['formula']} | "
            f"{item['branch'][:25]} | {item['prescreen_score']} | {item['discovery_score']} | "
            f"{chgnet_tag} | {top_risk} |"
        )

    lines += ["", "## Branch Coverage", "", "| Branch | Count | Avg PS | Max PS |", "|--------|-------|--------|--------|"]
    for branch, scores in sorted(branch_stats.items(), key=lambda pair: -max(pair[1])):
        lines.append(f"| {branch[:35]} | {len(scores)} | {sum(scores)/len(scores):.1f} | {max(scores):.1f} |")

    lines += [
        "",
        "## Notes",
        "",
        "- CHGNet is used only when a trusted prototype structure proxy is available.",
        "- Candidates with formula/template only remain heuristic-only; this is expected in v0.1.",
        "- High-pressure branches remain routed to the high-pressure board.",
        "",
        "## Next Action",
        "Top E1 candidates with either strong heuristic score or low CHGNet force proxy should be promoted to the DFT queue.",
    ]

    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=datetime.today().strftime("%Y-%m-%d"))
    parser.add_argument("--with-chgnet", action="store_true")
    args = parser.parse_args()

    manifest = SC_ROOT / "candidates" / args.date / "candidate_manifest.jsonl"
    results, branch_stats, chgnet_covered = run_prescreen(manifest, use_chgnet=args.with_chgnet)
    out_path = SC_ROOT / "reports" / "prescreen_leaderboard.md"
    write_prescreen_leaderboard(results, branch_stats, chgnet_covered, out_path)

    print(f"Prescreen leaderboard written: {out_path}")
    print(f"CHGNet-covered candidates: {chgnet_covered}")
    print("\nTop 10:")
    for idx, item in enumerate(results[:10], 1):
        if item.get("chgnet_ready"):
            chgnet_note = f" force={item['chgnet_force_max_ev_ang']:.2f}"
        else:
            chgnet_note = f" {item.get('chgnet_reason', 'heuristic')}"
        print(f"  {idx}. {item['formula']:20s} PS={item['prescreen_score']:5.1f} DS={item['discovery_score']:5.1f}{chgnet_note}")


if __name__ == "__main__":
    main()
