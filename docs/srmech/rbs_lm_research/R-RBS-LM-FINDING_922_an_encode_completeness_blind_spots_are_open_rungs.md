# F922 — the A–N partition is a COMPLETENESS CHECKLIST for "encode": every operator without a realized encode-carrier is a named blind spot, and srmech ALREADY tracks them. `harmonics.HARMONIC_LADDER_OPEN_RUNGS = {2:(C,K), 3:(J)}` — the framework's own bookkeeping says the open (unfilled) rungs are **C, J, K**, and the carrier audit confirms the cause: `Qi` (the exact-complex carrier) has **no argument/phase** (`arg`/`as_polar`/`modulus` all absent) → C+K open; and there is a `primes.factor` op but **no prime-coordinate carrier** → J open. The other 11 classes (A,B,D,E,F,G,H,I,L,M,N) are carried. So the missing carriers are exactly **two**: `Qarg` (the polar/argument read on Qi/Q — closes C *and* K) and a prime-coordinate carrier (closes J).

**Date:** 2026-06-22 · **srmech:** 0.9.0rc28 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Composes:** F921 (the encode-sense overload — one "encode" per A-N operator), F919/§72 (Qarg = the phase/chirality reader), F150 (`harmonics` the chirality-harmonic ladder), F914 (the K/L/M vs D/E/F/G heptad split), F127 (substrate-native readings) · **User direction (2026-06-22):** "the missing encode-via-A_N layer … tells us right away where every blind spot is and how to resolve it. what is the best way to realize this into srmech and what other carriers might we be lacking?"

## The insight (validated by the framework itself)
If "encode" = "represent in operator X's carrier" (F921: one encode per A-N class), then **any class without a realized carrier is a blind spot — and the A-N partition enumerates all 14 in advance.** This turns "where are we not reading?" into a lookup. srmech already does that lookup: `harmonics.HARMONIC_LADDER_OPEN_RUNGS`.

## Grounded coverage map (introspected from srmech rc28, not memory)
Carrier family present: `Q` (complex rational, rectangular), `Qi` (exact-complex scalar), `Qalg` (exact number-field), `Complex128` (float complex), `HV` (Klein-4), `Mat`/`Vec`, CD-tuple (octonion/sedenion), digest (SHA).

| harmonic | classes | status | carrier |
|---|---|---|---|
| **1** | A, B, F, H, N | all **closed** | digest (A) · TLV byte-stream (B) · `template.render` (F) · introspection/tool_schema (H) · `rational`/`Qalg` (N) |
| **2** | D, E, G, M **closed**; **C, K OPEN** | partial | match-count (D) · catalog/genome (E) · `search.byte_search` (G) · `HV` (M) · **C,K need the phase/argument — `Qi` has none** |
| **3** | I, L **closed**; **J OPEN** | partial | `cyclic`(gcd/lcm/mod_*/three_cycle) (I) · `Mat`/`Vec` eigvecs (L, F920) · **J has `primes.factor` op but no prime-coordinate carrier** |

`HARMONIC_LADDER_OPEN_RUNGS = {2:('C','K'), 3:('J',)}` → open classes **{C, J, K}**; closed = the other 11. Confirmed `Qi.arg`/`as_polar`/`modulus` = absent.

## The two missing carriers (the resolution)
1. **`Qarg` — the polar/argument read on the exact-complex carrier (`Qi`/`Q`). Closes C AND K.** One carrier, two rungs: the argument **θ** is C's direction/chirality (the magnetic-Laplacian eigvec phase, F919); the **r↔θ** split is K's pin-slot/phase-boundary (the magnitude vs the boundary). Build via Class-N `atan_series_truncate` (argument) + Class-K `cascade.magnitude` (modulus) — both already shipped as cascades; `Qarg` composes them into `Qi.as_polar() -> (r, θ)`. (Extends §72.)
2. **A prime-coordinate carrier (`Qprime`-shaped). Closes J.** A quantity → its **prime-exponent vector** (the J-encode: represent in the prime basis) via `primes.factor` — an exact-scalar carrier peer to `Qi`/`Qalg`. Today `factor` returns a factorisation list; the *carrier* (the prime-basis vector you encode into and do arithmetic on) is missing. (UPSTREAM §73.)

## Best way to realize in srmech (the unified shape)
The carrier family IS the encode layer: each A-N class's "encode" = `operand → its carrier`. Realize the blind spots as **two new exact-scalar carriers beside `Qi`/`Qalg`** — `Qarg` (polar, C+K) and `Qprime` (prime-coordinate, J) — and the harmonic ladder closes (no open rungs). The discipline this gives the whole project: **`HARMONIC_LADDER_OPEN_RUNGS` is the standing blind-spot list** — when a research arc can't read something, check whether it's an open rung; if so, the fix is the missing carrier, not a new method.

## Verdict / next
**Found (framework-attested):** the A-N partition is the encode-completeness checklist; the open rungs **{C, J, K}** are the blind spots, caused by exactly two missing carriers — **`Qarg`** (polar read, closes C+K) and **a prime-coordinate carrier** (closes J). All 11 other classes are carried. **Next:** (i) the `Qarg` ask (§72, now grounded as the C+K closure) — the one that also unlocks the F919 directional/chirality spectral kernel; (ii) the prime-coordinate carrier ask (§73) for J; (iii) once either ships, re-run the relevant encode (the magnetic/phase kernel for C/K; a prime-basis relationship encode for J) and watch the open rung close.
