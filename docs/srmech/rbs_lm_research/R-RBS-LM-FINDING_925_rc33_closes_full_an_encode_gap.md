# F925 — VERIFICATION: srmech 0.9.0rc33 closes the FULL A–N encode gap. The §74 consolidated ask landed: `harmonics.HARMONIC_LADDER_OPEN_RUNGS = {2:(), 3:()}` (EMPTY — every A–N class now has a carrier), `Qi` gained the polar read (`arg`/`modulus`/`as_polar`/`from_polar`/`from_complex` — closes C+K), and the `Qprime` prime-coordinate carrier shipped (`srmech.amsc.qprime` — closes J). Verified in a clean venv.

**Date:** 2026-06-22 · **srmech:** 0.9.0rc33 (TestPyPI, native ABI 3) · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Composes / closes:** §74 (the consolidated ask), F922 (the open-rung map), F923 (Qprime prototype), F924 (Qarg prototype) · **User direction (2026-06-22):** "get next srmech rc33 with that fix and closed the full A-N encode gap with new carriers we can check out."

## Scorecard (clean venv, rc33)
| ask (§74) | result |
|---|---|
| open-rungs map emptied | ✅ `HARMONIC_LADDER_OPEN_RUNGS = {2:(), 3:()}` — no open classes; the 14-class encode ladder is fully carried |
| `Qarg` polar read on `Qi` (closes **C+K**) | ✅ `arg`, `modulus`, `as_polar`, `from_polar`, `from_complex` all present; `Qi(3+4i).as_polar() → (r=5, θ=0.9273)`; `from_complex(3+4j)` lifts cleanly |
| `Qprime` prime-coordinate carrier (closes **J**) | ✅ `srmech.amsc.qprime.Qprime`: `coords(12)={2:2,3:1}`, `gcd(12,18).to_int()=6`, `lcm=36`, `similarity(12,18)=16/25` (exact) |

## API note (canonical shape vs our prototype)
The maintainer's shipped shape is slightly tighter than the F923/F924 proposals — same behavior, cleaner names:
- `Qprime.from_vec({prime: exp})` (dict, not a pair-list `from_int`); accessors `coords`/`to_int`/`gcd`/`lcm`/`similarity`/`period`.
- `Qi` polar = `arg`/`modulus`/`as_polar`/`from_polar` + the bonus `from_complex` we asked for (lifts `Mat`/`Vec` entries — unblocks the directional spectral kernel directly on `magnetic_laplacian` output).

## Verdict
The encode-completeness program (F921→F922→§74) is **complete in the package**: all 14 A–N classes carry an encode-lens; `HARMONIC_LADDER_OPEN_RUNGS` is empty. This is the standing guarantee — any future "can't read X" is no longer a missing carrier (the ladder is full), so it must be a *composition* gap, not a primitive gap. **Next:** press the additional kernel encoding types the carriers now enable (the C/K directional kernel via `Qarg`+`magnetic_laplacian`; the J multiplicative/period kernel via `Qprime`) — F926+.
