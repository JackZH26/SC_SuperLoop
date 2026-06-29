# Discovery Publish Plan

Updated (UTC): 2026-06-25

## Goal

Promote only sufficiently reviewed SC SuperLoop candidates into a dedicated SClib discovery database and expose them on a first-level `Discovery` page in the SClib website, refreshed every 6 hours.

## Why This Exists

- the current leaderboard is useful for internal iteration but too noisy for public presentation
- SClib needs a cleaner public-facing discovery lane with explicit review thresholds
- the loop should continue publishing qualified results even when Jack is not actively messaging

## Scope

### In Scope
- reviewed-candidate export from SC SuperLoop into SClib
- first-level `Discovery` navigation item after `timeline`
- Discovery landing page in SClib style
- English-only top intro explaining the method at a high level
- recurring 6-hour sync
- explicit public filter and confidence labels

### Out of Scope for v0.1
- automatic claims about superconducting Tc
- publishing candidates with unresolved checker flags
- exposing raw prescreen-only or CHGNet-only candidates
- replacing the internal leaderboard

## Public Filter Standard v0.1

A candidate is eligible for SClib Discovery only if all conditions hold:

1. It is not a benchmark / known-reference material used only for calibration.
2. It has reached at least `E3`.
3. `checker_status` is `pass`.
4. A dossier exists with:
   - mechanism hypothesis
   - risk tags
   - provenance summary
   - review timestamp
   - recommended next step
5. The entry survives deduplication by `formula + branch + prototype family`.
6. The candidate is assigned a public confidence label.

## Public Preview Mode (active now)

To get the Discovery page online early, the initial public deployment may
use a looser preview rule:

1. benchmarks still excluded
2. minimum evidence still `E3`
3. `checker_status=pending` is temporarily allowed alongside `pass`
4. entries must still have a dossier and provenance summary
5. the page must clearly signal that the current feed is a preview / exploratory release

This preview mode should be tightened again once the public candidate count
and checker maturity are higher.

## Proposed Public Confidence Labels

- `Exploratory Review Passed`
- `Mechanism-Supported`
- `High-Confidence Shortlist`

These are public-facing ranking tiers, not proof claims.

## Discovery Database Payload

Minimum public fields:

- `formula`
- `normalized_formula`
- `branch`
- `prototype_family`
- `evidence_level`
- `checker_status`
- `public_confidence`
- `discovery_score`
- `mechanism_hypothesis`
- `risk_tags`
- `review_summary`
- `provenance_summary`
- `recommended_next_step`
- `last_reviewed_at_utc`
- `published_at_utc`

Internal-only fields to keep private by default:

- raw candidate ids
- full intermediate logs
- noisy failed branches not meant for public review
- incomplete reviewer notes

## Website Requirements

- add `Discovery` as a first-level nav item immediately after `timeline`
- use SClib visual language and layout conventions
- top section must be English-only
- include a short method introduction:
  - SClib seeds known superconducting families and literature context
  - SC SuperLoop expands candidate neighborhoods with physics-informed heuristics
  - qualified candidates pass through prescreen, DFT, mechanism audit, and checker review before public display
- show last update time and filter standard on the page

## Sync Cadence

- run a dedicated export + publish sync every 6 hours
- only push delta changes plus required demotions/removals
- every sync should also verify that existing public entries still satisfy the filter

## Loop Integration

Target loop:

`Knowledge -> Hypothesis -> Candidate -> Prescreen -> DFT -> Phonon -> Mechanism Audit -> Checker -> Publish Review -> Ranking -> SClib Sync -> Memory Update -> Next Round`

## Open Decisions

- exact rule for `checker_status=pass`
- whether phonon evidence should be mandatory for the top public tier
- whether benchmark references appear on the public page as a separate explanatory section
- where the real SClib frontend repo / deployment config lives in this workspace or outside it

## Next Implementation Moves

1. define the `checker pass` rubric
2. create a local export artifact from SC SuperLoop state to a SClib-ready schema
3. locate and patch the SClib site codebase for nav + page integration
4. add the 6-hour sync job
5. add self-review checks for accidental over-promotion or stale public entries
