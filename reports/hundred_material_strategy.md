# 100 Scientifically Credible Superconductors Strategy

Updated: 2026-06-26

## Objective

Reach a usable corpus of 100 scientifically credible superconducting-material records as fast as possible without overclaiming novelty.

This target is not the same as "100 new discoveries".
It is a mixed corpus with strict evidence labeling.

## Why The Current Narrow Loop Is Too Slow

- The current heavy lane is optimized for upgrading a small number of exploratory candidates into E3.
- That is good for discovery quality, but too narrow to efficiently produce 100 credible records.
- The fastest path to 100 is to combine:
  - a reference corpus of known superconductors with sourced experimental evidence
  - a smaller verified exploratory corpus from SC SuperLoop itself

## Corpus Split

### Track A — Literature-backed Reference Corpus (target: 70)

Purpose:
- build a broad scientifically credible baseline quickly
- anchor mechanism families, prototype families, and known Tc regimes

Inclusion rules:
- experimentally reported superconductivity exists
- every Tc-like value must carry a source citation
- structure / family / mechanism labels must be conservative
- if doping, pressure, intercalation, or surface termination is essential, state it explicitly

Good families for fast accumulation:
- elemental superconductors
- A15 / intermetallic conventional superconductors
- binary nitrides / carbides / borides
- layered nitride halides
- kagome superconductors
- iron-based superconductors
- cuprates
- clathrates
- topological-doped superconductors

### Track B — Loop-verified Exploratory Corpus (target: 20)

Purpose:
- preserve the actual SC SuperLoop research value
- keep a subset of candidates that have passed bounded internal checks

Inclusion rules:
- E3 or above
- reviewed dossier exists
- wording stays at `DFT-screened candidate` unless stronger evidence exists
- no numerical Tc claim before the allowed evidence threshold

### Track C — High-priority Review / Benchmark-Adjacent Corpus (target: 10)

Purpose:
- keep scientifically useful queue anchors and benchmark-adjacent materials visible
- avoid pretending these are "new discoveries"

Inclusion rules:
- known superconducting references or benchmark-adjacent controls
- clearly labeled as `reference` or `benchmark-adjacent`
- useful for calibration, not counted as novelty

## Minimum Data Fields Per Record

Each record should aim to include:

- formula
- normalized_formula
- material_class
- branch_or_family
- structure_or_prototype_note
- evidence_class
- superconductivity_context
- Tc_value_or_range
- condition_note
- mechanism_note
- risk_tags
- source_citation
- source_type
- review_status

## Evidence Language Rules

- `literature-confirmed`: experimentally reported superconductivity with a source
- `DFT-screened`: SC SuperLoop internal bounded DFT support, not a Tc claim
- `reference`: known superconducting control / benchmark-adjacent material
- `exploratory`: promising but still under review

Do not collapse these into one label.

## Immediate Operational Shift

Until the corpus reaches 100:

1. Lane A remains conservative heavy compute on the active anchor.
2. Lane B should prefer reference-corpus building over cosmetic publication refreshes.
3. Publication surface refresh is still allowed, but only after:
   - active heavy lane is advanced or confirmed blocked
   - at least one new reference-corpus action has been considered

## Practical Throughput Target

- heavy lane: keep current 15-minute cadence discipline
- light lane: try to add or validate 3-5 reference records per successful curation cycle
- first milestone: 25 credible records
- second milestone: 50 credible records
- final milestone: 100 credible records

## Anti-Hallucination Rules

- never invent Tc values
- never use memory-only experimental numbers
- every experimental number must cite a source
- if a value is known qualitatively but exact value is not yet verified, mark it as `needs_source_verification`
- if a material is only superconducting after doping / pressure / intercalation, encode that condition explicitly

## Success Condition

The strategy succeeds when SC SuperLoop owns a 100-record corpus that is:

- scientifically conservative
- source-backed
- internally labeled by evidence class
- useful both for discovery benchmarking and for public/external interpretation
