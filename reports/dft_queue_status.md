# DFT Queue Status

Generated: 2026-06-27
Queue policy: prioritize only lanes that remain eligible after corpus classification and gate checks.

## Active This Cycle

| Candidate | Formula | Branch | Verified Step | Result | Next Action |
|-----------|---------|--------|---------------|--------|-------------|
| E0-2026-06-25-0254 | Mo2C | MXene_2D | not_started | active_anchor_still_eligible | prescreen |

## Completed

| Candidate | Formula | Branch | Result | Next Action |
|-----------|---------|--------|--------|-------------|
| E0-2026-06-25-0029 | TiN | AlTiPbW_exploratory | pending | promote to phonon_shortlist_or_relax_refinement |
| E0-2026-06-25-0091 | WB2 | AlB2_MgB2_boride | revise | relax_cell_or_alternate_prototype_review |
| E0-2026-06-25-0095 | NbB2 | AlB2_MgB2_boride | pending | pseudopotential_or_eos_audit |
| E0-2026-06-25-0103 | TiB2 | AlTiPbW_exploratory | revise | relax_cell_or_alternate_prototype_review |
| E0-2026-06-25-0177 | ZrB2 | AlB2_MgB2_boride | revise | relax_cell_or_alternate_prototype_review |
| E0-2026-06-25-0273 | MoB2 | AlB2_MgB2_boride | revise | relax_cell_or_alternate_prototype_review |

## Ready To Promote

| Rank | Candidate | Formula | Branch | Discovery | Layer | Gate Status | Next Action |
|------|-----------|---------|--------|-----------|-------|-------------|-------------|
| 1 | E0-2026-06-27-0090 | NbB2 | AlB2_MgB2_boride | 80.0 | structured | eligible | prescreen |
| 2 | E0-2026-06-27-0159 | MgB2 | AlB2_MgB2_boride | 80.0 | structured | classified_as_benchmark_control | prescreen |
| 3 | E0-2026-06-27-0198 | ZrB2 | AlB2_MgB2_boride | 80.0 | structured | classified_as_negative_control | prescreen |
| 4 | E0-2026-06-27-0233 | MoB2 | AlB2_MgB2_boride | 80.0 | structured | eligible | prescreen |
| 5 | E0-2026-06-27-0103 | TiB2 | AlTiPbW_exploratory | 78.8 | structured | classified_as_negative_control | prescreen |
| 6 | E0-2026-06-27-0250 | Mo2C | MXene_2D | 78.8 | broad | eligible | prescreen |
| 7 | E0-2026-06-27-0278 | TiN | AlTiPbW_exploratory | 78.8 | structured | classified_as_benchmark_control | prescreen |
| 8 | E0-2026-06-27-0206 | WO3 | AlTiPbW_exploratory | 71.0 | broad | eligible | prescreen |
| 9 | E0-2026-06-27-0091 | ScB2 | AlB2_MgB2_boride | 66.8 | broad | eligible | prescreen |
| 10 | E0-2026-06-27-0176 | MgBC | AlB2_MgB2_boride | 66.8 | broad | eligible | prescreen |
| 11 | E0-2026-06-27-0258 | AlB2 | AlB2_MgB2_boride | 66.8 | broad | eligible | prescreen |
| 12 | E0-2026-06-27-0013 | Bi2Sr2CaCu2O8 | cuprate_extrapolation | 65.0 | broad | eligible | prescreen |

## Notes

- resume anchor status: `active_anchor_still_eligible`
- negative controls, reference anchors, and benchmark controls must not be reopened as heavy DFT lanes
- if the first queue row is structure-blocked or classification-blocked, reseed to the next eligible lane and record the reason
- Lane B should continue literature-backed corpus growth whenever the heavy lane is blocked
