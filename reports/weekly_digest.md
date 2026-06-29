# Weekly Digest — Week of 2026-06-25

## Summary
LOOP-SC v0.1 infrastructure established. All Task 1-14 completed.

## Benchmarks Completed
- Nb SCF+DOS: PASS (BCC metal, Tc_exp=9.25K)
- Pb SCF+DOS: PASS (FCC strong-coupling, Tc_exp=7.2K)
- MgB2 SCF+DOS: PASS (AlB2-type, sigma-band metallic, Tc_exp=39K)

## Candidates Generated
- 300 E0/E1 candidates across 14 branches
- Top branch: AlB2_MgB2_boride (35), BC_framework (34), iron_based (34)
- E1 count: 234

## Infrastructure Status
- QE: operational (pw.x, dos.x, ph.x available)
- Python: pymatgen, spglib, phonopy, duckdb, pandas available
- chgnet: pending CPU-only install
- Database: materials.sqlite initialized
- Reports: all 11 standard report files populated

## Next Week Goals
- DFT on top 5 E1 candidates (NbB2, TiB2, WB2, MoB2, TiN)
- MP API pull for candidate structure matching
- First E3 dossiers expected

## Known Issues / Risks
- Nb pseudo: self-generated, not production-grade for EPC
- Pb pseudo: LDA (not PBE), SOC not included
- CHGNet not yet operational (GPU dependency issue)
- All prescreen scores are heuristic-only until CHGNet/MP integration
