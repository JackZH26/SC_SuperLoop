# Credible Superconductors Corpus Status

Updated: 2026-06-29

## Goal

Build a 100-record scientifically credible superconducting-material corpus.

## Current Counts

- total credible corpus records: 180
- Track A literature-backed references: 23 / 70
- Track B loop-verified exploratory records: 156 / 20
- Track C benchmark-adjacent / review anchors: 1 / 10

## Funnel Counts

- Broad candidate pool: 0
- Structured candidate pool: 51
- Promotion-ready pool: 129

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
