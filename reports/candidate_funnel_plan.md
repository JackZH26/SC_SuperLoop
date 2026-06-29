# Candidate Funnel Optimization Plan

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
