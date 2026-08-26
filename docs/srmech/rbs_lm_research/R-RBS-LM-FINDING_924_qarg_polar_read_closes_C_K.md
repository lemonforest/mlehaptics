# F924 — prototype: the `Qarg` polar read on the exact-complex carrier closes BOTH open rungs C and K — and it needs NO new transcendental code. `srmech.asymptotic_calculus` already ships `atan2` (exact `Q`, full quadrant, accepts `Q` args), `sqrt`, `hypot`, `sin`, `cos`. So `Qi.modulus()=sqrt(norm_sq())` [Class K] and `Qi.arg()=atan2(imag,real)` [Class C] are pure accessors over shipped ops. Verified: polar round-trip residual 0–1e-15 (display-collapse only; r,θ are exact `Q`), and on a directed magnetic Laplacian the phase flips **exactly** with edge direction (θ_fwd + θ_rev = exact `Q(0,1)`) while the modulus stays `Q(1,2)` direction-blind — i.e. arg = the chirality (C), modulus = the pin-slot magnitude (K). Built by an opus sub-agent; verified against rc28.

**Date:** 2026-06-22 · **srmech:** 0.9.0rc28 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Probe:** `R-RBS-LM-FINDING_924_qarg_polar_read_closes_C_K.py` (qarg_polar + qarg_ck_closure + qarg_api) · **Composes:** F922 (open-rung map — C,K), F919/§72 (Qarg = the chirality reader), F920 (the spectral kernel this unlocks directionally), `qi.Qi`/`q.Q`, `asymptotic_calculus` · **User direction (2026-06-22):** "prototype the Qarg polar read … opus sub-agents."

## Verified (rc28, exact `Q` throughout)
- **Gap confirmed:** `Qi`/`Q` are rectangular-only (no `arg`/`as_polar`/`modulus`/`phase`).
- **Ops already ship** in `srmech.asymptotic_calculus`: `atan2(y,x,*,terms=40)->Q` (exact, full quadrant, **accepts `Q` args** → exact-in/exact-out), `atan`, `sqrt`, `hypot`, `sin`, `cos` (+ `*_series_truncate`). No new transcendental code needed.
- **Round-trip** `Qi → (r,θ) → Qi`, all 4 quadrants + axes + a rational point: residual **0 to 1.2e-15** (purely the `float()` display collapse; r, θ stay exact `Q`). E.g. (−3,+4): r=5, θ=+2.2143, residual 1.2e-15.
- **C/K closure** on `magnetic_laplacian(3, dir-cycle, q=0.25)` → `hermitian_eigendecompose`: off-diagonal forward `−0.5i` (θ=−π/2), reversed `+0.5i` (θ=+π/2); **θ_fwd + θ_rev = exact `Q(0,1)`** (chirality flip is structurally exact, not float-fuzzy); modulus **`Q(1,2)` both directions** (K is direction-blind). Eigenvector component `V[0,2]`: θ_fwd=−1.1273, θ_rev=+1.1273, r identical.

## Proposed API (`Qarg`; thin accessors on `Qi`/`Q`, over shipped ops)
`Qi.modulus() -> Q  = sqrt(norm_sq())` [K] · `Qi.arg() -> Q = atan2(imag, real)` [C] · `Qi.as_polar() -> (r, θ)` · `Qi.from_polar(r, θ)` (via `cos`/`sin`). Methods (consistent with the existing `norm_sq()` method), or all promoted to properties together. Same pattern fits `Q`.

## Gap note (minor, non-blocking)
No `Qi.from_complex(z)` lift: `magnetic_laplacian`/`hermitian_eigendecompose` return builtin `complex` entries, so reading their phase needs `Qi(Q.from_float(z.real), Q.from_float(z.imag))`. Suggest adding `Qi.from_complex(z)` as a peer to `from_pairs`/`from_float` — unblocks the polar read directly on Laplacian output (the F920 directional spectral kernel).

## Verdict
Both C and K open rungs close with one polar accessor over already-shipped `asymptotic_calculus` ops — the lowest-cost, highest-leverage carrier fill (also unlocks the F919/F920 directional spectral kernel). Feeds §74 (consolidated ask).
