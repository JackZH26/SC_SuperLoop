# LOOP-SC Toolchain Status

Date: 2026-06-25
Project root: `/data/.openclaw/workspace/research/SC_SuperLoop`

## Scope

This report covers:

- Task 1: independent workspace setup
- Task 2: toolchain inspection
- Task 4: Quantum ESPRESSO smoke test

Task 3 was skipped by user instruction because it had already been completed earlier.

## Task 1: Independent Workspace

Status: COMPLETE

The project root is established at:

`/data/.openclaw/workspace/research/SC_SuperLoop`

Standard subdirectories created:

- `workspace/`
- `knowledge/`
- `candidates/`
- `runs/`
- `dossiers/`
- `reports/`
- `configs/`
- `scripts/`
- `benchmarks/`
- `cleanup_audit/`

## Task 2: Toolchain Inspection

### Quantum ESPRESSO

Observed PATH result:

- `pw.x`: not found in current shell `PATH`
- `ph.x`: not found in current shell `PATH`
- `dos.x`: not found in current shell `PATH`

Located binaries:

- `pw.x`: `/data/software/q-e-qe-7.3.1/PW/src/pw.x`
- `ph.x`: `/data/software/q-e-qe-7.3.1/PHonon/PH/ph.x`
- `dos.x`: `/data/software/q-e-qe-7.3.1/PP/src/dos.x`

Initial runtime status:

- `pw.x` initially failed at startup with missing shared library dependencies
- `ph.x` and `dos.x` were initially not launchable for the same reason

`ldd` on `pw.x` reports missing:

- `libopenblas.so.0`
- `libfftw3.so.3`
- `libmpichfort.so.12`
- `libgfortran.so.5`

Repair status:

- QE runtime was repaired in user space without reinstalling QE itself.
- A local runtime library overlay was built under:
  `/data/.openclaw/workspace/research/SC_SuperLoop/vendor/runtime/lib`
- Added runtime pieces include:
  - `libmpich12` extracted from Debian package
  - `libucx0` extracted from Debian package
  - local symlinks for `libopenblas.so.0`, `libfftw3.so.3`, `libgfortran.so.5`,
    `libhwloc.so.15`, and `libxml2.so.16`
- A reusable environment helper was created:
  `scripts/qe_env.sh`

Current runtime status:

- `pw.x` launches successfully when `scripts/qe_env.sh` is sourced
- `pw.x -version` now works

### Python

- `python3 --version`: `Python 3.13.5`
- `python3 -m pip --version`: `pip 25.1.1`

### Python package check

Available:

- `pymatgen`
- `spglib`
- `mp_api`
- `pandas`

Missing:

- `chgnet`
- `phonopy`
- `duckdb`

## Task 4: Quantum ESPRESSO Smoke Test

Status: COMPLETE

Result:

- A minimal `Si` SCF smoke test was executed successfully.
- QE now reaches input parsing and completes a real calculation.

Smoke test input:

- benchmark directory:
  `benchmarks/si_smoke/`
- input file:
  `benchmarks/si_smoke/input/si_scf.in`
- pseudopotential:
  `Si_ONCV_PBE-1.0.upf`
- output file:
  `benchmarks/si_smoke/output/si_scf.out`

Smoke test result:

- `PWSCF v.7.3.1` launched correctly
- SCF converged in 6 iterations
- total energy:
  `-15.74903857 Ry`
- job ended with `JOB DONE.`

## Immediate Next Actions

1. Reuse `scripts/qe_env.sh` for all QE-based tasks in this project.
2. Verify `ph.x` and `dos.x` through the same environment wrapper before phonon or DOS tasks.
3. Install the missing Python packages for the v0.1 toolchain:
   `chgnet`, `phonopy`, `duckdb`.
4. Proceed to benchmark tasks once the remaining Python-side gaps are addressed.

## Summary

- Task 1: complete
- Task 2: complete
- Task 4: complete after runtime repair
