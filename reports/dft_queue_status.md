# DFT Queue Status

Generated: 2026-06-29
Queue policy: prioritize only lanes that remain eligible after corpus classification and gate checks.

## Active This Cycle

| Candidate | Formula | Branch | Verified Step | Result | Next Action |
|-----------|---------|--------|---------------|--------|-------------|
| E0-2026-06-29-0087 | Mo2C | conventional | not_started | no_eligible_reseed_found | prescreen |

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

| Rank | Candidate | Formula | Branch | Loop Priority | Discovery | Layer | Gate Status | Next Action |
|------|-----------|---------|--------|---------------|-----------|-------|-------------|-------------|
| 1 | E0-2026-06-29-0087 | Mo2C | conventional | 66.0 | 80.0 | broad | eligible | prescreen |

## Notes

- resume anchor status: `no_eligible_reseed_found`
- negative controls, reference anchors, and benchmark controls must not be reopened as heavy DFT lanes
- if the first queue row is structure-blocked or classification-blocked, reseed to the next eligible lane and record the reason
- Lane B should continue literature-backed corpus growth whenever the heavy lane is blocked
- maintenance-only streak: `0`
- hours since substantive advance: `0.0`
