# Aluminum Route Integration

Updated: 2026-06-27

## Decision

Integrate aluminum-bearing ideas into the current SC SuperLoop as a constrained phonon / chemical-energy side branch, not as a room-temperature mainline.

The working split is:

- keep `Mg1-xAlxB2` and `Al-Li-B` inside `AlB2_MgB2_boride`
- keep `LaAlO3/SrTiO3` and `FeSe/LaAlO3` inside `AlO_STO_oxide`
- do not merge bulk `Al2O3` or `LaAlO3` with interface-mediated hypotheses

## Why This Fits the Current Framework

The present funnel already has two nearby branches:

- `AlB2_MgB2_boride`
- `AlO_STO_oxide`

So the correct integration is not a new branch. It is stricter sub-routing inside those two existing families.

## Aluminum Candidate Classes Added

### A. Sigma-band filling control, mechanism-preserving

These are useful because they stay close to the MgB2 mechanism rather than pretending that stoichiometric `AlB2` is itself a breakthrough candidate.

- `Mg0.75Al0.25B2`
- `Mg0.5Al0.5B2`
- `Mg0.25Al0.75B2`
- `Li0.5Al0.5B2`
- `LiAlB4`

Operational meaning:

- treat them as `broad -> structured` upgrade material
- preserve explicit alloy / ternary semantics
- score them by whether they preserve a credible sigma-hole path

### B. Aluminum-oxide interface routes, conjecture-only

These are not bulk oxide superconductors. They are interface-conditioned hypotheses and must stay tagged that way.

- `LaAlO3/SrTiO3`
- `FeSe/LaAlO3`
- `FeSe/LaAlO3(001)`

Operational meaning:

- keep `interface_required`
- for `FeSe/LaAlO3*`, also keep `conjecture_only`
- never flatten them into plain `FeSe` or plain `LaAlO3`

## Hard Constraints

1. `AlB2` itself remains a calibration / failure-memory checkpoint unless a real hole-restoring route is explicit.
2. `bulk Al-O` does not get promoted by light-element intuition alone.
3. `FeSe/LaAlO3` is not evidence of a better STO replacement. It is only a bounded hypothesis entry.
4. No aluminum route should displace the main room-temperature search lanes centered on d/f-electron, 2D, charge-transfer, or magnetic-exchange logic.

## Funnel Placement

### Broad pool

Place here by default:

- all `Mg1-xAlxB2` variants
- `Li0.5Al0.5B2`
- `LiAlB4`
- `FeSe/LaAlO3`
- `FeSe/LaAlO3(001)`

Typical blockers:

- `no_structure_proxy`
- `proxy_only`
- `carrier_density_sensitive`
- `interface_required`
- `mechanism_ambiguous`

### Structured pool

Allow promotion only after:

- alloy or interface semantics are explicit
- a verified prototype proxy exists
- the candidate is not being justified by generic light-element arguments alone

### Promotion-ready

Very few aluminum-bearing candidates belong here soon.

The only near-term plausible entrants are:

- a well-scoped `Mg1-xAlxB2` alloy row with explicit composition and mechanism wording
- `LaAlO3/SrTiO3` only as an interface anchor, not as a new discovery claim

## Recommended Next Actions

1. Add verified prototype proxies for the `Mg1-xAlxB2` alloy lane.
2. Keep `FeSe/LaAlO3` in the broad pool until literature or bounded interface modeling justifies stronger scope.
3. Use aluminum routes to increase visible candidate count toward `100`, but cap heavy-compute priority behind the current main queue.
4. Continue the mainline search for 3d/4d + ligand systems that better match the `single-orbital 2D charge-transfer` target.
