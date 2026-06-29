# Benchmark Checklist

Generated: 2026-06-25

| Benchmark | Structure | Pseudo | SCF | DOS | Metallic | Dossier | Status |
|-----------|-----------|--------|-----|-----|----------|---------|--------|
| QE Smoke (Si) | FCC, ibrav=2 | Si_ONCV_PBE-1.0.upf | ✓ | — | ✓ | si_smoke/ | PASS |
| Nb | BCC, ibrav=3 | Nb.pbe-rrkj.UPF (ld1.x) | ✓ | ✓ | ✓ (3.90 st/eV) | BM-Nb-001.md | PASS |
| Pb | FCC, ibrav=2 | pb_s.UPF (LDA PAW) | ✓ | ✓ | ✓ (0.52 st/eV) | BM-Pb-001.md | PASS |
| MgB2 | AlB2-type, ibrav=4 | Mg+B pz-vbc (LDA) | ✓ | ✓ | ✓ (0.71 st/eV) | BM-MgB2-001.md | PASS |
| H3S | — | — | — | — | — | — | DEFERRED |

## Notes
- Nb pseudo: self-generated with ld1.x (NC RRKJ PBE, 4S+4D valence, lloc=2). Adequate for DOS/metallicity; not production-grade for EPC.
- Pb pseudo: LDA PAW from QE distribution. SOC not included. Valid for metallic baseline.
- MgB2: LDA pseudos from QE EPW examples — standard reference set for this system.
- H3S: deferred per v0.1 scope (high-pressure, requires EPC/Eliashberg).

## Key Reference Values
| Material | Tc_exp | DOS@Ef (our calc) | E_total (Ry) | Notes |
|----------|--------|-------------------|--------------|-------|
| Nb | 9.25 K | 3.895 st/eV/cell | -38.0475 | d-metal reference |
| Pb | 7.2 K | 0.516 st/eV/cell | -118.6672 | strong-coupling sp-metal |
| MgB2 | 39 K | 0.707 st/eV/cell | -13.5742 | sigma-band reference |
