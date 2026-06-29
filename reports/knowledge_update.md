# Knowledge Update

Generated: 2026-06-25

## Materials Project / SCLib Integration
- Status: pending (mp-api available, key configuration needed)
- Plan: run mp-api pull for top-priority families in next session

## Benchmark Knowledge Added
- Nb: BCC conventional metal, DOS@Ef=3.895 st/eV (d-band character), Tc_exp=9.25K
- Pb: FCC strong-coupling sp-metal, DOS@Ef=0.516 st/eV, Tc_exp=7.2K, SOC important
- MgB2: AlB2-type, DOS@Ef=0.707 st/eV, sigma-band + pi-band confirmed metallic, Tc_exp=39K

## Candidate Generator v0.1
- 300 candidates generated across 14 branches
- Branch coverage: all 14 branches covered with >= 5 candidates
- Prescreen: heuristic-only (no CHGNet, no MP API yet)

## Pseudopotential Status
- Nb.pbe-rrkj.UPF: self-generated (ld1.x), NC, PBE, 4S+4D
- Pb.pz-kjpaw.UPF: from QE distribution (PAW, LDA)
- Mg.pz-n-vbc.UPF + B.pz-vbc.UPF: from QE EPW examples (NC, LDA)
- All PP_TAUMOD/PP_TAUATOM XML issues resolved

## Next Steps
1. Configure mp-api key and pull MP structures for E1 candidates
2. Install CHGNet for better stability prescreening
3. Run DFT on top 5 E1 candidates
