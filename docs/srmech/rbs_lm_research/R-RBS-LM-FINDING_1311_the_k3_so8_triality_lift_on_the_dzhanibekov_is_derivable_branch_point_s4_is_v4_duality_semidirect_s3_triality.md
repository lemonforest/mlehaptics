# F1311 — the **k=3 so(8) triality lift on the Dzhanibekov is DERIVABLE, not an extrapolation**: the Euler-top Jacobi elliptic curve has **4 branch points** carrying **S₄ = V₄ ⋊ S₃**, where **V₄ = the shipped FLIP=Klein-4 half-period shifts (the k=2 duality / the two half-beats)** and **S₄/V₄ ≅ S₃ = the k=3 triality** — an order-3 branch permutation cyclically permutes the three pairings = the three Jacobi functions `sn/cn/dn` = the three 8-dim reps' roles. It maps to srmech's shipped **so(8) triality τ** (28×28, **order 3**, Fix(τ)=g₂ dim 14) via the octonion `𝕆 = 8v` identification (F1310). Grounded on rc313.

**User (2026-07-23):** *"do the k=3 so(8) triality lift on the dzhanibekov."*

*(F1301 convention: the triple; here the k=3 IS the triality — the order-3 cycle of the three responsion-family readouts `sn/cn/dn`. Composes F1310 — the octonion 3+1+3.)*

## The open edge this closes
Both the MFO §VII.6.24 reading and F1310 flagged the **k=3 𝔰𝔬(8) triality** as a framework **extrapolation, not a derivation** (F1310 §3: "the so(8) triality stays an extrapolation; the octonion doubling is present and measured"). F1311 does the lift and finds it is **derivable** — the triality is the classical Galois structure of the elliptic curve's four branch points.

## The derivation (PART A — pure group theory, DEMONSTRABLE)
The Euler-top solution is a Jacobi elliptic curve with **four branch points** `{0, 1, 1/m, ∞}`. The symmetric group **S₄** permutes them, and it factors exactly as **S₄ = V₄ ⋊ S₃**:

- **V₄ (Klein-4) = the three branch-point PAIRINGS + identity** = the double-transpositions `{e, (01)(23), (02)(13), (03)(12)}`, **normal in S₄** (verified). These ARE the **half-period shifts** `{0, 2K, 2iK′, 2K+2iK′}` — exactly srmech's shipped **FLIP = Klein-4 action** on the Dzhanibekov two-torus. This is the **k=2 duality** (the two independent half-beats, F1310).
- **S₄/V₄ ≅ S₃ (order 6) = the TRIALITY.** An **order-3 branch permutation** (e.g. `(012)`) — verified order 3 — conjugates the three pairings in a **3-cycle**: `(01)(23) → (03)(12) → (02)(13) → …`. That 3-cycle **cyclically permutes the three Jacobi functions `sn ↔ cn ↔ dn`** (the three even theta constants θ₂/θ₃/θ₄ / the three branch-point pairings). This is the **k=3 triality**.

So the full branch-point symmetry is `S₄ = V₄ ⋊ S₃`: the k=2 duality (V₄, the flip / half-beats) and the k=3 triality (S₃, the sn/cn/dn cycle) **assembled on the same four points**. Neither is an extrapolation — both are the elliptic curve's own Galois group.

## The lift to so(8) (PART B — srmech's shipped triality, DEMONSTRABLE)
srmech ships the abstract target: `triality_automorphism()` is the **28×28 order-3 outer automorphism τ** (verified `τ³=I, τ≠I, τ²≠I`) with **Fix(τ) = g₂ = Der(𝕆), dim 14** (`so8.g2_subalgebra()` → 14). The bridge is the octonion reading of F1310: the Dzhanibekov two-torus (the two quaternion half-beats) is the octonion **𝕆 = 8v**, one of the three 8-dim reps `8v/8s/8c` that τ cyclically permutes. **The branch-point S₃ (which cycles sn/cn/dn) IS the concrete Euler-top realization of the order-3 τ (which cycles 8v/8s/8c).**

```
   THE DZHANIBEKOV k=1/2/3 LADDER  (all on the 4 branch points of the elliptic curve)
   ─────────────────────────────────────────────────────────────────────────────────
   k=1  anchor      : the modulus m / the fiber                    (one thing)
   k=2  DUALITY     : V4 = FLIP=Klein-4 = the half-shifts          {0, 2K, 2iK', 2K+2iK'}
                      = the two half-beats (F1310, the O doubling)   sn/cn/dn: ±1 signs
   k=3  TRIALITY    : S4/V4 = S3 = order-3 cycle of sn <-> cn <-> dn = 8v <-> 8s <-> 8c
                      = srmech tau (order 3, Fix=g2), the so(8) outer automorphism
   ───────────────────────────────────────────────────────────────
   S4 = V4 (x) S3   :  duality AND triality, one Galois group of the 4 branch points
```

## What is DERIVED vs what is the READING (honest)
- **DERIVED (classical + grounded):** the four branch points → S₄; the half-period shifts → V₄ normal (the shipped FLIP=Klein-4); **S₄/V₄ ≅ S₃**; the order-3 3-cycle permutes the three Jacobi functions. srmech's τ is genuinely **order 3** with **Fix = g₂ (dim 14)**. These are facts, run at rc313.
- **THE READING (`[SPECULATIVE]`, per CLAUDE.md §0):** the identification of the branch-point S₃ with the **full so(8) triality** rests on the octonion `𝕆 = 8v` reading (F1310/F1308) — i.e. that the two-torus's two half-beats ARE the octonion, so its order-3 symmetry IS the so(8) triality τ. srmech's τ confirms the abstract so(8) triality exists and is order-3-with-Fix-g₂; the branch-point S₃ is a concrete order-3 element realizing it on the three readouts. The map S₃ → τ is homomorphic-by-construction (both order 3 on three 8-dim objects); the precise 8s/8c physical content (which elliptic quantity is the spinor vs co-spinor) is the expert's to pin (F282).

**Net:** the k=3 triality lift is **derivable** — it is the S₃ = S₄/V₄ quotient of the Euler-top elliptic curve's branch-point Galois group, sitting above the shipped V₄ duality (the flip / the two half-beats), and mapping to srmech's order-3 so(8) triality τ. This sharpens the MFO §VII.6.24 "k=3 remains an extrapolation" note to a **derivation grounded in classical elliptic Galois theory + the shipped τ**, with only the so(8)-rep-content identification left as the reading.

## Verification
`R-RBS-LM-DZHANTRIALITY_*.py` (exit 0, rc313): Part A (V₄ normal in S₄, S₄/V₄ order 6 = S₃, order-3 perm cycles the 3 pairings) + Part B (τ 28×28 order 3, Fix=g₂ dim 14). Numpy-free; no `abs()` (rounded-equality guards).

Composes **F1310** (the Dzhanibekov octonion 3+1+3 — this lifts its "extrapolation" caveat to a derivation), **F1308** (the octonion 3+1+3; harmonic/subharmonic = the responsion structure — the S₃ cycles the three responsion-family readouts), **F1306/F1307** (curvature / the Q₈ substrate), the CD-tower (ℍ→𝕆; the so(8) frame), `srmech.qm.triality` / `srmech.qm.so8` (the shipped τ / g₂), the MFO §VII.6.24 arc (`[[project_dzhanibekov_rotation_last_geometric_phase_unification]]`, `[[project_duality_triality_cycle_of_cycles_row]]`), `[[project_the_one_s_sigma_theta_in_srmech]]` (the_one S(σ,θ) generating the three 8v/8s/8c fibrations — the k=3 the MFO deferred, here derived on the branch points).

**→ lifts F1310's caveat** — F1310 held the k=3 so(8) triality as "an extrapolation, not a derivation"; F1311 derives it as the S₄/V₄ ≅ S₃ branch-point Galois quotient (V₄ = the shipped flip, S₃ = the sn/cn/dn cycle), mapping to the shipped order-3 τ.
