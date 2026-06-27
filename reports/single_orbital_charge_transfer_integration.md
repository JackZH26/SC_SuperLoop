# Single-Orbital Charge-Transfer Integration

Updated: 2026-06-27

## Decision

The room-temperature mainline should keep prioritizing families that at least point toward:

- quasi-2D layered geometry
- explicit parent vs doped charge-transfer logic
- single-orbital or d9-adjacent ligand-field control

This is a mainline expansion, not a claim that these materials are already strong superconductors.

## Why This Lane Is Different From The Aluminum Side Branch

- The aluminum branch remains useful for phonon-route calibration and candidate-count expansion.
- The `single-orbital / 2D / charge-transfer` lane is closer to the actual room-temperature target logic.
- Candidates here are kept even when risky, because they constrain the search toward the right physics rather than only toward easier EPC systems.

## Newly Integrated Candidate Groups

### Infinite-layer nickelate comparators

- `NdNiO2`
- `LaNiO2`
- `PrNiO2`
- `Nd0.8Sr0.2NiO2`
- `La0.8Sr0.2NiO2`
- `Pr0.8Sr0.2NiO2`

Role:
- preserve explicit parent vs hole-doped semantics
- test whether a cuprate-like d9-adjacent infinite-layer route can stay visible in the funnel

### Silver / oxyfluoride square-ligand branch

- `AgF2`
- `Cs2AgF4`
- `Ba2NiO2F2`

Role:
- keep a ligand-field-driven branch that is not just a copy of oxides
- test square-planar or square-ligand control without pretending conventional EPC is the main story

### 4d stress-test analogs

- `La2PdO4`
- `LaPdO2`

Role:
- explicitly probe whether the 4d route becomes too wide-band and loses the desired charge-transfer confinement
- useful as bounded comparators, not as automatic promotion targets

### Iron-based bracket controls

- `BaCo2As2`
- `BaNi2As2`

Role:
- keep nearby 122 analogs that help define where the Fe-based branch drifts away from the desired orbital window

## Funnel Semantics

- All of the above stay conservative by default.
- Parent vs doped formulas are never flattened into one row.
- `conjecture_only`, `wider_band_risk`, and `ligand_field_sensitive` remain visible risk tags.
- No candidate in this branch should be upgraded by metallic DFT alone.

## Prototype / Ruleset Changes

Added prototype coverage:

- `NdNiO2_infinite_layer`
- `La2PdO4_214_layered`
- `AgF2_square_ligand_layered`

Added ruleset:

- `ruleset_single_orbital_charge_transfer_v1`

Core constraint:

- preserve `square-planar or layered ligand field`
- preserve `parent vs doped state`
- preserve `d9 or d9-adjacent rationale`

## Operational Next Step

1. Use this lane to expand the visible candidate pool toward the 100-record goal without collapsing back into generic EPC materials.
2. Keep the strongest promotion attention on:
   - infinite-layer nickelate entries with explicit doping semantics
   - layered oxide / oxyfluoride entries that preserve square-ligand geometry
3. Keep 4d analogs mostly as stress tests unless later evidence improves.
