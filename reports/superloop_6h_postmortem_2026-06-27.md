# SC SuperLoop 6h Postmortem

Updated: 2026-06-27 23:00 +08

## Scope

This postmortem audits the last 6 hours of local SC SuperLoop behavior and explains why the loop produced almost no substantive research progress without external prompting.

Audit window:

- 2026-06-27 17:03 +08 to 23:03 +08

## Executive Verdict

The loop did not fail because "there were no ideas."
It failed because the current engineering allows repeated state refreshes to count as a valid cycle even when:

- the active anchor has not advanced
- no new compute was launched
- no structure proxy was attached
- no candidate was promoted through the funnel
- no corpus expansion happened

In short:

- the system has persistence
- the system has reports
- the system does **not** yet have a hard progress contract

That means it can look alive while being scientifically stationary.

## High-Severity Findings

### P0. Fake autonomy: report refresh was accepted as loop progress

Evidence:

- `reports/strategy_updates.md` contains repeated cycle notes claiming `maintenance-only`.
- The phrase `maintenance-only` appears about 100 times.
- The phrase `Mo2C / prescreen` appears about 108 times.
- In the audit window the loop kept refreshing:
  - `loop_state`
  - `dft_queue_status`
  - `discovery_feed`
  - board reports
- But these refreshes did not force a scientific transition.

Why this is fatal:

- a self-loop must treat "no state transition" as a failure condition after a bounded number of cycles
- the current loop treats it as acceptable steady state

### P0. Active anchor can live forever without advancing

Evidence:

- `reports/loop_state.md` still shows:
  - resume anchor = `E0-2026-06-25-0254 / Mo2C / prescreen`
  - verified step = `not_started`
  - next action = `prescreen`
- `scripts/update_loop_state.py` returns `active_anchor_still_eligible` whenever the current anchor is not explicitly blocked.
- There is no age limit, no stagnation counter, and no execution-proof check.

Why this is fatal:

- "eligible" is not the same as "progressing"
- a loop that cannot expire a stale anchor is not autonomous

### P0. Newly promoted mainline records were silently collapsed into passive anchors

Observed bug:

- new mainline records such as:
  - `Nd0.8Sr0.2NiO2`
  - `NdNiO2`
  - `PrNiO2`
  - `Ba2NiO2F2`
  - `La2PdO4`
- were promoted into the public corpus, but the optimizer reclassified them as `reference_anchor`
- that made them passive instead of executable

Root cause:

- `scripts/optimize_discovery_corpus.py` used a default reference-anchor classification path for unknown rows
- this erased the intended exploratory semantics of the new charge-transfer mainline

Impact:

- the public corpus grew
- but the execution loop lost those rows as forward-driving candidates

Immediate fix applied in this audit:

- preserve explicit record semantics instead of blindly defaulting to `reference_anchor`
- add explicit exploratory classification for nickelate / square-ligand / palladate mainline rows

### P1. The execution queue excluded the new mainline by design

Evidence:

- `scripts/update_loop_state.py` originally only admitted ready-QE candidates from:
  - `AlB2_MgB2_boride`
  - `AlTiPbW_exploratory`
  - `MXene_2D`
- `cuprate_extrapolation` was excluded

Impact:

- even when the new nickelate/palladate rows existed in the manifest, they could not enter the main execution shortlist

Immediate fix applied in this audit:

- `cuprate_extrapolation` was added to the ready-QE branch set

### P1. Queue ranking still favors old high-scoring legacy families

Evidence:

- after the branch-admission fix, the ready queue still prefers:
  - `NbB2`
  - `MoB2`
  - `Mo2C`
  - other legacy boride rows
- the new mainline rows now appear in `manifest_candidate_funnel.md`
- but they do not dominate `dft_queue_status.md` because ranking still follows old discovery-score bias

Impact:

- the loop admits the new lane but does not yet prioritize it correctly
- this is a remaining optimization gap, not yet fully fixed

### P1. No "progress watchdog" exists

What is missing:

- `last_substantive_advance_at`
- `cycles_since_substantive_advance`
- `anchor_age_hours`
- `max_cycles_without_transition`
- `max_cycles_without_commit`
- `max_cycles_without_new_record`

Why this matters:

- if the system never measures stagnation, it cannot self-supervise

### P1. The funnel is descriptive, not prescriptive

Evidence:

- `reports/upgrade_execution_queue.md` often has almost no actionable `Structured -> Promotion-Ready` rows
- the funnel explains candidate state well
- but it does not yet enforce the next scientific operation

Impact:

- the funnel acts like analytics
- not like a real executor

### P2. CHGNet / structure-proxy coverage is still effectively absent

Evidence:

- `reports/loop_state.md` shows `CHGNet-covered rows: 0`
- many candidates remain blocked by `no_structure_proxy`

Impact:

- the loop cannot cheaply unlock enough `broad -> structured` upgrades
- this forces excessive dependence on already-known families

## Why The Loop Did Not Notice Its Own Failure

### 1. The success criterion is wrong

Current implicit criterion:

- "the reports are refreshed and nothing inconsistent happened"

Correct criterion:

- "at least one substantive scientific state transition happened"

### 2. Maintenance mode has no expiration

The loop has a valid conservative mode, but no hard rule like:

- if maintenance-only repeats for 3 cycles, escalate
- if the same anchor survives 2 hours with `not_started`, reseed
- if no scientific advance occurs in 6 hours, create a failure report and switch strategy

### 3. Reporting and execution are not separated

The current system can:

- rewrite reports
- refresh queues
- export the same public feed

without proving that any execution action actually happened.

### 4. There is no forced fallback ladder

When the heavy lane stalls, the loop should automatically switch to:

1. structure-proxy upgrade
2. corpus promotion
3. generator revision
4. branch reseeding
5. failure report + strategy change

That ladder is not yet enforced.

## What Was Actually Accomplished In The Last 6 Hours

Substantive positive work:

- promoted Discovery feed from 30 to 35 public records
- integrated nickelate / square-ligand / palladate mainline ideas into candidate generation
- created a public corpus presence for:
  - `Nd0.8Sr0.2NiO2`
  - `NdNiO2`
  - `PrNiO2`
  - `Ba2NiO2F2`
  - `La2PdO4`

But the execution loop itself underperformed because:

- it did not convert those additions into a new active research lane
- it did not produce a new compute result
- it did not advance the stale anchor

## Immediate Fixes Applied During This Audit

1. `optimize_discovery_corpus.py`

- stopped blindly collapsing unknown rows into `reference_anchor`
- added explicit exploratory treatment for the new charge-transfer mainline formulas
- preserved `ruleset_single_orbital_charge_transfer_v1`

2. `update_loop_state.py`

- allowed `cuprate_extrapolation` to enter the ready-QE candidate pool

3. Rebuilt local state

- regenerated:
  - `loop_state`
  - `dft_queue_status`
  - `manifest_candidate_funnel`
  - `upgrade_execution_queue`

Result after fixes:

- the mainline rows now appear in `manifest_candidate_funnel.md` as promotion-ready rows
- however, queue priority is still dominated by older higher-scoring boride rows

## Full Optimization Plan

### Phase 1. Install a real progress contract

Add a cycle result model with exactly these statuses:

- `advance_compute`
- `advance_structure_proxy`
- `advance_corpus`
- `advance_generator`
- `blocked_with_escalation`
- `failure`

Rule:

- every cycle must end in one of these
- plain report refresh is not a valid result

### Phase 2. Add a stagnation watchdog

Persist in `reports/loop_state.json`:

- `last_substantive_advance_at`
- `cycles_since_substantive_advance`
- `anchor_age_hours`
- `cycles_since_last_commit`
- `cycles_since_last_public_growth`
- `cycles_since_last_new_candidate_family`

Escalation policy:

- 2 cycles with same anchor and no step change -> reseed required
- 3 maintenance-only cycles -> force fallback ladder
- 6 hours with no substantive advance -> emit postmortem + strategy switch

### Phase 3. Replace "active_anchor_still_eligible" with execution-proof logic

An anchor stays active only if at least one is true:

- verified step changed
- new run directory was created
- dossier changed
- queue result changed
- last execution timestamp is within the allowed freshness window

If none is true:

- mark anchor as `stale_anchor`
- auto-reseed

### Phase 4. Enforce the fallback ladder

If heavy compute is blocked:

1. upgrade one `broad -> structured` row via structure proxy
2. promote one safe row into public corpus
3. revise generator/ruleset with one concrete family improvement
4. create one failure-memory / avoid-rule update
5. if still blocked, emit escalation report

This prevents zero-output cycles.

### Phase 5. Separate mainline priority from legacy-score gravity

Introduce a new priority score:

- `loop_priority_score`

Components:

- `goal_alignment_score`
- `novelty_relevance_score`
- `execution_readiness_score`
- `evidence_density_score`
- `stagnation_penalty`
- `legacy_family_penalty`

Important:

- this score must rank the room-temperature target lane above easy legacy borides when the scientific objective demands it

### Phase 6. Create a real orchestrator

Add a script such as:

- `scripts/run_superloop_cycle.py`

Responsibilities:

1. load state
2. evaluate watchdogs
3. choose lane
4. execute exactly one substantive action
5. verify artifact changed
6. write cycle verdict
7. commit if checkpoint-worthy
8. alert if blocked

Without this orchestrator, the loop remains a set of tools, not a self-driving system.

### Phase 7. Make promotion quotas explicit

Per 6-hour window:

- at least 1 substantive compute/structure action
- at least 1 funnel promotion or corpus promotion
- at least 1 generator or failure-memory improvement when compute is blocked

Per 24-hour window:

- at least 1 new family-level insight or queue-policy refinement

### Phase 8. Add audit-grade observability

Create a compact scoreboard, for example:

- `reports/superloop_health.md`

Track:

- last substantive advance time
- hours since last advance
- current anchor age
- maintenance-only streak
- public corpus count
- promotion-ready count
- structure-proxy backlog
- blocked-candidate count
- last commit time

Red flags:

- `hours_since_advance > 2`
- `maintenance_streak > 2`
- `anchor_age_hours > 2 and step=not_started`

### Phase 9. Tighten public-corpus promotion semantics

Public corpus promotion must never disable execution.

A row can be both:

- public-facing `DFT-screened`
- internally `exploratory_candidate`

Do not let public export semantics rewrite internal execution semantics.

### Phase 10. Add nightly failure-driven retrospection

If the loop had no substantive output in the last 6 hours, it must automatically produce:

- failure summary
- root cause
- next fallback move
- one code/process change candidate

That is the minimum viable self-improvement behavior.

## Concrete Next Actions

### Within the next 30 minutes

1. patch queue ranking so the mainline charge-transfer rows are not buried behind legacy diboride scores
2. add stagnation counters to `loop_state.json`
3. add `superloop_health.md`

### Within the next 2 hours

1. create `run_superloop_cycle.py`
2. force one substantive cycle that does one of:
   - structure-proxy upgrade for a mainline row
   - queue reseed away from stale `Mo2C`
   - bounded execution on a top aligned mainline candidate

### Within the next 12 hours

1. make maintenance-only cycles self-limiting
2. make failure escalation automatic
3. make Discord updates driven by watchdog events, not by human prompting

## Final Judgment

The present SC SuperLoop is not dead, but it is not yet a true self-propelling research superloop.

Right now it is:

- persistent
- conservative
- reasonably well documented

but still too willing to equate "safe, unchanged, refreshed" with "acceptable."

That is the core engineering mistake.

The real target is different:

- if nothing advances, the system must feel that as failure
- then change lane
- then produce a new artifact
- then re-evaluate

Only then does it become a real superconductivity superloop rather than a conservative status-refresh machine.
