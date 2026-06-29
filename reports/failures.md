# Failure Log

Generated: 2026-06-25

## QE Failures

| Date | Candidate | Stage | Error | Resolution |
|------|-----------|-------|-------|------------|
| 2026-06-25 | Nb (initial) | pseudo read | UPF PP_TAUMOD XML malformed from ld1.x | Stripped PP_TAUMOD/PP_TAUATOM empty sections with Python |
| 2026-06-25 | Mg (ld1.x) | pseudo gen | PS-KS equation errors with RRKJ scheme | Switched to bundled EPW example pseudos (Mg.pz-n-vbc.UPF) |
| 2026-06-25 | Nb pseudo download | pseudo fetch | All external UPF download sources unavailable (DNS/404) | Generated locally with ld1.x |

## Prescreen Failures

None yet.

## DFT Review Flags

| Date | Candidate | Stage | Issue | Resolution |
|------|-----------|-------|-------|------------|
| 2026-06-25 | MoB2 (AlB2-type prototype) | DOS interpretation | SCF/NSCF/DOS completed, but DOS(E_F) is near zero in current setup | Keep as E3-computed candidate with `checker_status=revise`; retry with alternate prototype or relax strategy |
| 2026-06-26 | NbB2 (AlB2-type prototype) | unconstrained vc-relax follow-up | Free-cell `vc-relax` drove the lattice toward an unphysical tiny volume and aborted with `Not enough space allocated for radial FFT` | Keep the fixed-cell E3 metallic result; require constrained-cell / parameter-audited relax before any phonon promotion |

## Autonomy / Continuity Flags

| Date | Issue | Evidence | Resolution |
|------|-------|----------|------------|
| 2026-06-26 | No single resume anchor for the next cron turn | `reports/loop_state.md` and the leaderboards are both informative, but the last explicit loop-state timestamp was still `2026-06-25` and the active DFT lane had to be inferred by reading multiple files | Added a code-level `resume_anchor` path in `scripts/update_loop_state.py` and updated `reports/strategy_updates.md` to point at the live DFT queue item |
| 2026-06-26 | External state is fragmented across several reports | `strategy_updates.md`, `loop_state.md`, `dft_queue_status.md`, and the leaderboards each carry part of the handoff | Use `reports/dft_queue_status.md` as the operational entry point for the next cycle, with the generated `resume_anchor` becoming the single continuation contract |
| 2026-06-26 | Strategy seed pointed at the wrong active lane | `reports/strategy_updates.md` still seeded `WB2`, while `reports/dft_queue_status.md` marked `ZrB2` as active | Corrected the seed to `E0-2026-06-25-0177 / ZrB2 / advance_to_scf` and kept `WB2` as a secondary fallback only |
| 2026-06-26 | Loop-state timestamp lagged behind the active queue | `reports/loop_state.md` still showed `2026-06-25` even though `reports/dft_queue_status.md` had already advanced | Regenerated `reports/loop_state.json` and `reports/loop_state.md` so the on-disk resume anchor matches the live queue again |
| 2026-06-26 | `resume_anchor` generation was brittle | The generator failed to extract the active row from `reports/dft_queue_status.md`, leaving `reports/loop_state.json` with an empty `resume_anchor` | Switched `scripts/update_loop_state.py` to parse the active table row directly and re-ran the generator so the anchor is now persisted again |

## Self-Review Outcomes

| Date | Check | Result | Notes |
|------|-------|--------|-------|
| 2026-06-26 | Discovery preview mode | Pass | The public preview endpoint is live, populated, and still reflects preview-mode publication semantics. |
| 2026-06-26 | Active anchor / secondary lane policy | Pass | Lane A remains on `E0-2026-06-25-0254 / Mo2C`; lane B is still kept lightweight instead of spawning a second heavy QE branch. |
| 2026-06-26 | Continuation contract on disk | Pass | `reports/loop_state.json` now carries a non-empty `resume_anchor`, so the next cron turn has an explicit handoff target. |

## Self-Review Audit — 2026-06-26

| Date | Check | Result | Notes |
|------|-------|--------|-------|
| 2026-06-26 | Discovery preview mode | Pass | `reports/discovery_feed.json` remains populated and `reports/discovery_meta.json` still reports `mode: preview`. |
| 2026-06-26 | Active anchor / secondary lane policy | Pass | The live queue anchor remains `E0-2026-06-25-0254 / Mo2C`, and the secondary lane is still being used conservatively. |
| 2026-06-26 | Loop stall risk | Pass | No structural stall was found; the single resume contract on disk is sufficient for next-turn continuity. |

## Notes

- Failure categories: convergence / structure / input / compute / pseudo
- All failures documented here before retrying or escalating.
- Continuity issues are logged here when they would otherwise cause the loop to depend on a human prompt.

## Self-Review Follow-up

| Date | Issue | Evidence | Resolution |
|------|-------|----------|------------|
| 2026-06-26 | Discovery preview mode audit | `curl http://127.0.0.1:3088/api/leaderboard?page=1` returned a populated preview board and `reports/discovery_meta.json` still reports `mode: preview` | No action needed |
| 2026-06-26 | Active anchor / secondary lane audit | `reports/loop_state.md` and `reports/dft_queue_status.md` still agree on `E0-2026-06-25-0254 / Mo2C` as the resume anchor, with the secondary lane remaining light-only | No action needed |
| 2026-06-26 | Public checker wording | `reports/discovery_feed.json` and `scripts/export_discovery_feed.py` were still wording `pending / revise` as if they were public checker states | Reworded the preview text so those states are explicitly internal review signals |
| 2026-06-26 | Public surface policy drift | `reports/strategy_updates.md` still implied preview export could surface `pending` E3 candidates even though the feed policy keeps `pending / revise` internal | Reworded the strategy note to match the conservative export rule |
| 2026-06-27 | Discovery feed checker label was too absolute for preview mode | `reports/discovery_feed.json` said `verified / pass only` while the preview feed intentionally still contains internal review states like `pending` and `revise` | Reworded the filter rule to say preview rows may carry internal review signals, while export-ready rows still require verified / pass |
| 2026-06-27 | Self-review audit consistency pass | Live anchor, heavy-lane gate, and failure-memory routing still align across `reports/loop_state.md`, `reports/dft_queue_status.md`, and the leaderboards; the only drift was preview/public wording in `reports/discovery_feed.json` | Softened the checker rule to match preview semantics and logged the audit in `reports/strategy_updates.md` |
| 2026-06-27 | Self-review bounded recheck | `reports/loop_state.md`, `reports/dft_queue_status.md`, and `reports/discovery_feed.json` still agree on the active anchor and on conservative preview/public semantics; the remaining conditional candidates are still gated and negative controls remain blocked | No structural fix needed; recorded the pass in `reports/strategy_updates.md` |
| 2026-06-27 | Discovery feed checker wording regression | `scripts/export_discovery_feed.py` still phrased the preview checker rule too absolutely even after the feed itself had been regenerated in preview mode | Softened the script text to say export-ready rows require verified / pass, while pending and revise stay internal preview states |
| 2026-06-27 | Watchdog stale-anchor wording could be misread as a stall | `reports/loop_state.md` sets `stale anchor: True` even when the queue has already reseeded to a new active lane, which is correct but easy to misinterpret | Clarified in the self-review trail that this is a watchdog flag, not a structural continuity failure |

## Self-Review Audit — 2026-06-27

| Date | Check | Result | Notes |
|------|-------|--------|-------|
| 2026-06-27 | Bounded self-review continuity | Pass | `reports/loop_state.md`, `reports/dft_queue_status.md`, the leaderboards, `reports/discovery_feed.json`, and `reports/credible_corpus_status.md` still agree on the current anchor, conservative gating, and preview/public claim boundaries. |
| 2026-06-27 | Structural-stall risk | Pass | No evidence of a broken handoff loop was found; the current `stale anchor: True` signal still behaves as a watchdog flag rather than a continuity failure. |
| 2026-06-27 | Active anchor continuity | Pass | `reports/loop_state.md` and `reports/dft_queue_status.md` still agree on `E0-2026-06-25-0254 / Mo2C / prescreen` as the resume anchor. |
| 2026-06-27 | Heavy-lane gating | Pass | `NbB2` and `MoB2` remain conditional, while `TiB2`, `WB2`, and `ZrB2` stay in failure-memory routing. |
| 2026-06-27 | Public-claim discipline | Pass | The discovery feed keeps preview/public semantics explicit, and the leaderboards do not promote benchmark or negative-control rows. |
| 2026-06-27 | Feed / leaderboard consistency | Pass | The feed and all three leaderboards are aligned on the same conservative candidate set and claim levels. |
| 2026-06-27 | Self-review bounded recheck | Pass | The current reports still form a self-sustaining loop contract; only the usual export timestamp lag separates the generated views. |
| 2026-06-27 | Generated header skew | Pass | `reports/dft_queue_status.md` still has an older generated header date, but its active-row content matches the live anchor and does not require a structural fix. |
| 2026-06-27 | Generated report refresh | Pass | Re-ran `scripts/update_loop_state.py` and `scripts/export_discovery_feed.py` so `loop_state`, `dft_queue_status`, and the discovery preview all share the same current generation pass. |
| 2026-06-27 | Stale queue header wording | Pass | `scripts/update_loop_state.py` now uses the current generation date when writing `reports/dft_queue_status.md`, so the header no longer lags behind the content. |
| 2026-06-27 | Stale generated board headers | Pass | `scripts/optimize_discovery_corpus.py` now stamps generated board headers from the runtime date, which removes the misleading 6/26 vs 6/27 header skew on leaderboard and status reports. |
| 2026-06-27 | Self-review bounded recheck | Pass | The current loop state, DFT queue, leaderboards, discovery feed, and credible corpus status still agree on the same active anchor, gating policy, and conservative public-claim boundaries; no structural fix was needed this cycle. |
| 2026-06-27 | Resume-anchor handoff wording | Pass | The live queue has reseeded from the older Mo2C continuation path to `E0-2026-06-27-0261 / Nd0.8Sr0.2NiO2 / prescreen`; the top-level strategy note was updated so future turns read the current anchor first. |
| 2026-06-27 | Watchdog stale-anchor wording | Pass | `stale anchor: True` is still the correct watchdog state, but the loop is already reseeded; the report now spells out that this is maintenance pressure rather than a structural stall. |

## Self-review alert 2026-06-28T07:46:54.957192+00:00
- Feed/corpus mismatch or missing active anchor detected.
- Active anchor: `Ba2NiO2F2 / nickelate / prescreen`
- Discovery feed count: `141` vs corpus `141`
- Stale-anchor reason: `unknown`
- Discovery audit: `fail`
