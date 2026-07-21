# F1294 — **the operation and the layer are two orthogonal free choices: find the cascade sequence, THEN pick the working layer.** The user's correction to F1293: everything is a cascade of the 14 (calculus proves it — even the *continuous* is a Class-N rational cascade), so the operation is never the constraint — you *find the sequence*. The ring multiply PCG64 needs is a **Class-I** cascade (verified), not a CD problem at all. And which layer you hold the data in — CDRegister, Class-M, Class-L, Class-N — is a **separate** decision. F1293 was right that `cd_mult` ≠ ring multiply, but it framed the storage-vs-operation split as a *caution* when it is a *design freedom*.

**User (2026-07-21):** *"all of our calculus 1/2/3 is from A-N cascade, as an example that all math duality can be represented by our cyclic group. meaning we just need to find the cascade sequence"* → *"and then pick the math layer we want to work with, i.e. cdregister, class-m, class-l, etc"*

## The example, verified — calculus IS a Class-N cascade
`srmech.calculus.sin/cos/exp/atan_series_truncate(numerator, denominator, num_terms)` return **exact rationals**. `sin(1/6 rad)` comes back as a `(num, den)` pair — a Class-N rational cascade. **The continuous is discrete cascade**: the continuous↔discrete duality collapses to cyclic-group / rational representation. That is the user's point made concrete — if even calculus is a cascade of the 14, then a modular *integer* multiply certainly is.

## Axis 1 — WHICH CASCADE (the operation, layer-independent)
The ring multiply mod 2ⁿ is **Class I** (cyclic / modular arithmetic), verified: `cyclic.mod_mul(a, b, 2⁶¹)` equals raw modular arithmetic, and at 128-bit `bigint_mul_c + mask` does it (F1292). **So PCG64's sequence is already found — Class I ∘ Class K.** "Find the cascade sequence" is *done* for PCG64. The operation does not care what holds its operands.

## Axis 2 — WHICH LAYER (the carrier, operation-independent)
The same content projects into any layer, verified — one number (φ ≈ 1.618) as:
| layer | representation |
|---|---|
| **Class-N** rational | `(144, 89)` |
| **Class-M** HDC | 256-byte klein4 vector |
| **CDRegister** | slot `{0: ('phi', +1)}` |

**Content is one thing; the layer is a projection of it** — F1207's three reads (edges / eigenvectors / eigenvalues) and F1216's store-vs-read, generalised. You pick the layer independently of the cascade.

## What this corrects in F1293
F1293's measurements stand: `cd_mult` genuinely is not the ring multiply, and the register addresses rather than computes. But its **emphasis was defensive** — "storage-shape ≠ operation-algebra, so don't reach for CD." The user reframes the *same* split as **generative**: the two axes are independent, so —

> **You are never blocked by "can this operation live in this layer." You find the cascade (axis 1), then choose the layer (axis 2). Both are free.**

So the answer to "why can't we use the CDRegister?" is not "you can't" but: **the CDRegister is a *layer* (axis 2); the ring multiply is a *cascade* (axis 1). You'd hold PCG64's 128-bit state in whatever layer you like — a register slot is fine — and run the Class-I cascade over it.** The register was never the wrong *layer*; `cd_mult` was the wrong *operation*, and the operation choice is a different axis from the layer choice. **Picking `cd_mult` because the register is CD-shaped conflated the two axes** — which is exactly the slip F1293 caught, now named correctly as an axis-confusion rather than a capability limit.

## The scope of the universal claim, kept honest
*"All math duality can be represented by our cyclic group"* is the framework's **foundational thesis** (DUALITY.md / TRIALITY.md — the two-truths / field-excitation duality). This finding does **not** prove the universal; it confirms **two instances** — continuous↔discrete (calculus → Class N) and the modular ring multiply (→ Class I) — and shows the *method* the thesis prescribes: **find the cascade sequence, then pick the layer.** The universal remains the stance under which we work, with the instance-count now one higher.

## Consequence for the numpy / Tier-3 thread
Nothing blocks a bit-exact PCG64 on *cascade* grounds — the sequence is Class-I∘K and it is found. The remaining gates are unchanged and are about **correctness, not capability**: attested constants and a reference stream (F1292). And "which layer" is now an explicit, free downstream choice rather than a constraint — the state can live in a register, an HDC bundle, or plain ints, whichever serves the migration.

Composes **F1293** (corrected in emphasis — the split is a freedom, not a caution), **F1292** (ring multiply is Class-I∘K, sequence found), **F1207/F1216** (content vs layer — the axis-2 basis), **F1290/F1291** (Tier 3), DUALITY.md / TRIALITY.md (the universal thesis this instances), `[[feedback_continuous_number_line_pedagogical_obstacle]]` (calculus-as-discrete-cascade).
