# Manifest Candidate Funnel

Generated: 2026-06-27

This board tracks the broader prescreen manifest, not only the 30-row credible corpus.

## Funnel Counts

- Broad candidate pool: 40
- Structured candidate pool: 11
- Promotion-ready pool: 40

## Broad Candidate Pool

Preserve quantity here; most rows are blocked by missing structure proxies or missing condition encoding.

| Candidate | Formula | Branch | Quantity | Quality | Block | Upgrade |
|---|---|---|---|---|---|---|
| E0-2026-06-28-0250 | Mo2C | MXene_2D | 84.0 | 61.6 | no_structure_proxy | attach_verified_structure_proxy, prototype_verification, condition_scope_check, termination_scope_check |
| E0-2026-06-28-0204 | Ba0.6K0.4Fe2As2 | iron_based_extrapolation | 72.8 | 56.8 | - | preserve_branch_constraints |
| E0-2026-06-28-0066 | Bi2Se3 | topological_doped | 69.8 | 57.4 | - | preserve_branch_constraints |
| E0-2026-06-28-0215 | Cu0.3Bi2Se3 | topological_doped | 69.8 | 57.4 | - | preserve_branch_constraints |
| E0-2026-06-28-0244 | BaFe2As2 | iron_based_extrapolation | 69.8 | 57.4 | - | preserve_branch_constraints |
| E0-2026-06-28-0255 | SnCH6 | p_block_hydride | 78.0 | 52.0 | - | track_pressure_window_as_soft_prior, hydride_structure_scope_check |
| E0-2026-06-28-0141 | ScNCl | layered_nitride_halonitride | 63.8 | 50.6 | - | preserve_branch_constraints |
| E0-2026-06-28-0171 | B2C | BC_framework | 63.8 | 50.6 | - | preserve_branch_constraints |
| E0-2026-06-28-0188 | TiNCl | layered_nitride_halonitride | 63.8 | 50.6 | - | preserve_branch_constraints |
| E0-2026-06-28-0241 | HfNBr | layered_nitride_halonitride | 63.8 | 50.6 | - | preserve_branch_constraints |
| E0-2026-06-28-0246 | NbNCl | layered_nitride_halonitride | 63.8 | 50.6 | - | preserve_branch_constraints |
| E0-2026-06-28-0254 | NaBC2 | BC_framework | 63.8 | 50.6 | - | preserve_branch_constraints |
| E0-2026-06-28-0268 | TaNBr | layered_nitride_halonitride | 63.8 | 50.6 | - | preserve_branch_constraints |
| E0-2026-06-28-0283 | KB3C4 | BC_framework | 63.8 | 50.6 | - | preserve_branch_constraints |
| E0-2026-06-28-0040 | TeH2 | p_block_hydride | 68.0 | 50.0 | - | track_pressure_window_as_soft_prior, hydride_structure_scope_check |
| E0-2026-06-28-0122 | PbH4 | p_block_hydride | 68.0 | 50.0 | - | track_pressure_window_as_soft_prior, hydride_structure_scope_check |
| E0-2026-06-28-0130 | SbCH6 | p_block_hydride | 68.0 | 50.0 | - | track_pressure_window_as_soft_prior, hydride_structure_scope_check |
| E0-2026-06-28-0197 | SnH4 | p_block_hydride | 68.0 | 50.0 | - | track_pressure_window_as_soft_prior, hydride_structure_scope_check |
| E0-2026-06-28-0256 | SbH3 | p_block_hydride | 68.0 | 50.0 | - | track_pressure_window_as_soft_prior, hydride_structure_scope_check |
| E0-2026-06-28-0296 | BiH3 | p_block_hydride | 68.0 | 50.0 | - | track_pressure_window_as_soft_prior, hydride_structure_scope_check |

## Structured Candidate Pool

These rows already have a prototype proxy or enough branch semantics to support better ranking and controlled expansion.

| Candidate | Formula | Branch | Quantity | Quality | Block | Upgrade |
|---|---|---|---|---|---|---|
| E0-2026-06-28-0090 | NbB2 | AlB2_MgB2_boride | 78.0 | 57.0 | structural_minimum_unresolved | free_cell_relax, eos_mini_scan, phase_consistency_check |
| E0-2026-06-28-0159 | MgB2 | AlB2_MgB2_boride | 92.0 | 88.0 | - | reference_maintenance_only |
| E0-2026-06-28-0198 | ZrB2 | AlB2_MgB2_boride | 58.0 | 22.0 | negative_control | record_avoid_rule, explore_only_escape_routes |
| E0-2026-06-28-0233 | MoB2 | AlB2_MgB2_boride | 78.0 | 57.0 | phase_ambiguity | phase_split, structure_validation, prototype_specific_followup |
| E0-2026-06-28-0103 | TiB2 | AlTiPbW_exploratory | 58.0 | 22.0 | negative_control | record_avoid_rule, explore_only_escape_routes |
| E0-2026-06-28-0278 | TiN | AlTiPbW_exploratory | 92.0 | 88.0 | - | retain_as_family_anchor |
| E0-2026-06-28-0051 | CsV3Sb5 | kagome_vanHove | 94.0 | 88.0 | - | reference_maintenance_only |
| E0-2026-06-28-0276 | FeSe | iron_based_extrapolation | 92.0 | 88.0 | - | reference_maintenance_only |
| E0-2026-06-28-0272 | LiFeAs | iron_based_extrapolation | 94.0 | 88.0 | - | reference_maintenance_only |
| E0-2026-06-28-0234 | Ba8Si46 | doped_clathrate | 92.0 | 88.0 | - | reference_maintenance_only |
| E0-2026-06-28-0281 | La2-xBaxCuO4 | cuprate_extrapolation | 98.0 | 91.0 | - | reference_maintenance_only |

## Promotion-Ready Pool

Only these rows should compete for heavier compute once corpus-level gates are also satisfied.

| Candidate | Formula | Branch | Quantity | Quality | Block | Upgrade |
|---|---|---|---|---|---|---|
| E0-2026-06-28-0146 | HfNCl | layered_nitride_halonitride | 74.0 | 70.0 | - | bounded_dft_followup |
| E0-2026-06-28-0195 | BC3 | BC_framework | 74.0 | 70.0 | - | bounded_dft_followup |
| E0-2026-06-28-0253 | ZrNCl | layered_nitride_halonitride | 74.0 | 70.0 | - | bounded_dft_followup |
| E0-2026-06-28-0053 | RbV3Sb5 | kagome_vanHove | 74.0 | 70.0 | - | bounded_dft_followup |
| E0-2026-06-28-0206 | WO3 | AlTiPbW_exploratory | 74.0 | 70.0 | - | bounded_dft_followup |
| E0-2026-06-28-0267 | KV3Sb5 | kagome_vanHove | 74.0 | 70.0 | - | bounded_dft_followup |
| E0-2026-06-28-0091 | ScB2 | AlB2_MgB2_boride | 74.0 | 70.0 | - | bounded_dft_followup |
| E0-2026-06-28-0176 | MgBC | AlB2_MgB2_boride | 74.0 | 70.0 | - | bounded_dft_followup |
| E0-2026-06-28-0258 | AlB2 | AlB2_MgB2_boride | 74.0 | 70.0 | - | bounded_dft_followup |
| E0-2026-06-28-0013 | Bi2Sr2CaCu2O8 | cuprate_extrapolation | 74.0 | 70.0 | - | bounded_dft_followup |
| E0-2026-06-28-0142 | La2CuO4 | cuprate_extrapolation | 74.0 | 70.0 | - | bounded_dft_followup |
| E0-2026-06-28-0245 | YBa2Cu3O7 | cuprate_extrapolation | 74.0 | 70.0 | - | bounded_dft_followup |
| E0-2026-06-28-0004 | Mg0.5Al0.5B2 | AlB2_MgB2_boride | 74.0 | 70.0 | - | bounded_dft_followup |
| E0-2026-06-28-0056 | Ti3C2 | MXene_2D | 74.0 | 70.0 | - | bounded_dft_followup |
| E0-2026-06-28-0057 | Nb2C | MXene_2D | 74.0 | 70.0 | - | bounded_dft_followup |
| E0-2026-06-28-0059 | V2C | MXene_2D | 74.0 | 70.0 | - | bounded_dft_followup |
| E0-2026-06-28-0060 | Ti2C | MXene_2D | 74.0 | 70.0 | - | bounded_dft_followup |
| E0-2026-06-28-0078 | TiC | AlTiPbW_exploratory | 74.0 | 70.0 | - | bounded_dft_followup |
| E0-2026-06-28-0099 | WC | AlTiPbW_exploratory | 74.0 | 70.0 | - | bounded_dft_followup |
| E0-2026-06-28-0125 | WB | AlTiPbW_exploratory | 74.0 | 70.0 | - | bounded_dft_followup |
