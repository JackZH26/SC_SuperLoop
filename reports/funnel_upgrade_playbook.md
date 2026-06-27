# Funnel Upgrade Playbook

Updated: 2026-06-27

## Objective

Turn the current candidate funnel into an executable upgrade system that increases both:

- candidate volume in the broad pool
- scientifically usable candidates in the structured and promotion-ready pools

## Current Bottleneck

The main blocker is not lack of ideas. It is that too many candidates remain trapped at:

- `entry_block_reason = no_structure_proxy`
- `entry_block_reason = proxy_only`
- missing condition encoding for doping / interface / termination sensitive families

This means the next optimization step is not stricter filtering. It is faster candidate upgrading.

## Immediate Upgrade Rule

Use the following conversion logic:

1. `broad -> structured`
   - attach a verified structure proxy
   - encode explicit condition scope
   - preserve family-specific mechanism semantics

2. `structured -> promotion-ready`
   - complete structure-specific validation
   - remove `proxy_only`
   - ensure branch-level gate is scientific, not purely bookkeeping

3. `promotion-ready -> heavy compute`
   - only after the candidate is no longer blocked by structure ambiguity, negative-control status, or missing condition scope

## Priority Queue

### Priority A: fastest path to structured

These candidates already have strong quantity signals and should be upgraded first:

- `Mo2C`
  - why first: top broad-pool quantity signal, already the live resume anchor
  - blocker: `no_structure_proxy`
  - required upgrade:
    - attach a verified bare/idealized Mo2C structural proxy
    - explicitly separate bare `Mo2C` from `Mo2CTx`
    - encode termination-sensitive scope

- `HfNCl`
  - why first: strong layered nitride anchor family, high discovery score
  - blocker: `no_structure_proxy`
  - required upgrade:
    - attach host-layer structural proxy
    - encode intercalation/doping condition explicitly

- `ZrNCl`
  - why first: same family as `HfNCl`, likely reusable upgrade path
  - blocker: `no_structure_proxy`
  - required upgrade:
    - attach host-layer structural proxy
    - preserve intercalation-sensitive semantics

- `BC3`
  - why first: light-element branch with good scale potential
  - blocker: `no_structure_proxy`
  - required upgrade:
    - attach prototype proxy
    - distinguish ideal 2D/3D framework assumptions

### Priority B: structured candidates closest to promotion-ready

These should be the first structured-pool rows promoted upward once proxy cleanup is done:

- `LiBC`
  - current state: `structured`, `proxy_only`
  - required upgrade:
    - encode hole-doping route
    - validate the exact proxy used
    - keep MgB2-neighbor mechanism wording disciplined

- `SrTiO3`
  - current state: `structured`, `proxy_only`
  - required upgrade:
    - encode carrier-density/interface condition
    - make clear parent vs doped/interface-superconducting context

- `CaTiO3`
  - current state: `structured`, `proxy_only`
  - required upgrade:
    - validate prototype scope
    - encode oxide branch condition assumptions

- `KTaO3`
  - current state: `structured`, `proxy_only`
  - required upgrade:
    - encode interface/doping path
    - keep SOC/interface caveat explicit

- `BaTiO3`
  - current state: `structured`, `proxy_only`
  - required upgrade:
    - encode carrier-density-sensitive condition
    - avoid flattening ferroelectric parent into a generic superconducting claim

### Priority C: keep blocked, do not waste heavy compute

- `TiB2`, `ZrB2`, `WB2`
  - role: negative control / failed memory
  - action: retain avoid rules only

- `NbB2`
  - role: conditional candidate
  - action: free-cell relax + EOS mini scan before any promotion

- `MoB2`
  - role: conditional candidate
  - action: phase split before any promotion

## Family-Specific Upgrade Rules

### MXene / layered carbide

- never promote formula-only MXene rows
- require explicit bare vs terminated scope
- require one prototype proxy per promoted candidate

### Layered nitride / halonitride

- preserve host/intercalant/doping semantics
- do not flatten `ZrNCl` or `HfNCl` into unconditional superconductors
- upgrade rows in family batches to reuse the same host proxy logic

### MgB2-neighbor diboride / borocarbide

- do not promote by `AlB2-type` alone
- require boron-network mechanism continuity or explicit doping path
- prefer `LiBC` and `MgBC` style mechanism-preserving variants over random transition-metal diborides
- treat `Mg1-xAlxB2` and `Al-Li-B` as `sigma-band filling control` candidates, not as standalone room-temperature routes
- keep stoichiometric `AlB2` as a calibration / failure-memory checkpoint unless a real hole-restoring path is explicit

### Oxide / STO-adjacent

- treat parent, doped, interface, and oxygen-vacancy contexts separately
- do not use plain PBE metallicity as a superconductivity claim
- prefer condition-complete rows over raw formula expansion
- split `bulk Al-O` from `LAO/STO` and `FeSe/LaAlO3` interface conjectures
- keep `FeSe/LaAlO3` explicitly tagged as `conjecture_only` and `mechanism_ambiguous` until literature or bounded interface modeling says otherwise

## Near-Term Success Criterion

This optimization phase is successful if the next cycle reaches:

- at least `3-5` additional rows upgraded from `broad` to `structured`
- at least `2` rows upgraded from `structured` to `promotion-ready`
- no reopening of negative-control diborides
- no loss of broad-pool volume while quality rises upstream

## Operating Principle

Quantity and quality should not be traded against each other.

The correct design is:

- keep a large broad pool
- upgrade the best rows quickly
- reserve heavy compute for only the cleaned, condition-explicit subset
